"""Fetch pharmacy elements once, sequentially, with raw bytes and provenance."""

import argparse
import hashlib
import json
import logging
import math
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)
USER_AGENT = (
    "PharmaAssistantPrototype/0.1 (https://github.com/JOEOFFME/pharma-assistant)"
)


class FetchError(RuntimeError):
    """A fetch failed, or a server returned an incomplete/non-Overpass payload."""


def load_config(path: Path) -> dict[str, Any]:
    """Read the explicit YAML configuration without machine-specific paths."""
    with path.open(encoding="utf-8") as stream:
        config = yaml.safe_load(stream)
    if not isinstance(config, dict):
        raise ValueError("Configuration must be a mapping")
    return config


def build_query(timeout_s: int, bbox: list[float] | None = None) -> str:
    """Query nodes, ways and relations, including center coordinates for polygons."""
    if not 1 <= timeout_s <= 600:
        raise ValueError("Query timeout must be between 1 and 600 seconds")
    if bbox is None:
        selector = 'area["ISO3166-1"="MA"]["admin_level"="2"]->.ma;'
        region = "area.ma"
    else:
        if len(bbox) != 4 or not all(math.isfinite(v) for v in bbox):
            raise ValueError("bbox must contain four finite numbers")
        south, west, north, east = bbox
        if not (-90 <= south < north <= 90 and -180 <= west < east <= 180):
            raise ValueError("bbox must be south,west,north,east within WGS84 bounds")
        selector = ""
        region = ",".join(str(v) for v in bbox)
    return (
        f"[out:json][timeout:{timeout_s}];{selector}"
        f'nwr["amenity"="pharmacy"]({region});out center tags;'
    )


def validate_payload(raw: bytes) -> dict[str, Any]:
    """Reject server remarks and partial results instead of reporting false coverage."""
    try:
        payload = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FetchError("Response is not valid JSON") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("elements"), list):
        raise FetchError("Response is missing the Overpass elements list")
    if not all(isinstance(item, dict) for item in payload["elements"]):
        raise FetchError("Response contains malformed element entries")
    if payload.get("remark"):
        raise FetchError(f"Overpass returned a remark: {payload['remark']}")
    if not isinstance(payload.get("osm3s"), dict):
        raise FetchError("Response is missing the OSM source timestamp metadata")
    return payload


def retry_after_seconds(value: str | None) -> float:
    """Honor numeric or HTTP-date Retry-After without treating invalid text as zero."""
    if value is None:
        return 0
    try:
        seconds = float(value)
        return max(0, seconds) if math.isfinite(seconds) else 0
    except ValueError:
        try:
            return max(
                0, (parsedate_to_datetime(value) - datetime.now(UTC)).total_seconds()
            )
        except (ValueError, TypeError, OverflowError):
            return 0


def respectful_sleep(seconds: float) -> None:
    """Sleep in bounded chunks with progress logs during long server cooldowns."""
    while seconds > 0:
        chunk = min(30.0, seconds)
        logger.info("Waiting %.0f seconds before another public request", chunk)
        time.sleep(chunk)
        seconds -= chunk


def request_overpass(query: str, config: dict[str, Any]) -> bytes:
    """POST sequentially with backoff, without hopping between endpoints."""
    endpoint = config["endpoint"]
    if urllib.parse.urlparse(endpoint).scheme != "https":
        raise ValueError("Overpass endpoint must use HTTPS")
    attempts = int(config["attempts"])
    if not 1 <= attempts <= 5 or float(config["backoff_s"]) < 1:
        raise ValueError("Use 1-5 attempts and at least one second backoff")
    request = urllib.request.Request(
        endpoint,
        data=urllib.parse.urlencode({"data": query}).encode(),
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    last_error: Exception | None = None
    for attempt in range(attempts):
        wait = float(config["backoff_s"]) * 2**attempt
        try:
            with urllib.request.urlopen(
                request, timeout=config["http_timeout_s"]
            ) as response:
                limit = int(config["max_response_bytes"])
                raw = response.read(limit + 1)
                if len(raw) > limit:
                    raise FetchError("Response exceeds configured size limit")
                validate_payload(raw)
                return raw
        except urllib.error.HTTPError as exc:
            if exc.code not in {429, 500, 502, 503, 504}:
                raise FetchError(
                    f"Overpass refused the request: HTTP {exc.code}"
                ) from exc
            wait = max(wait, retry_after_seconds(exc.headers.get("Retry-After")))
            last_error = exc
        except (urllib.error.URLError, TimeoutError, FetchError) as exc:
            last_error = exc
        logger.warning(
            "Overpass attempt %s/%s failed: %s", attempt + 1, attempts, last_error
        )
        if attempt + 1 < attempts:
            respectful_sleep(wait)
    raise FetchError(f"Overpass failed after {attempts} attempts: {last_error}")


def fetch_snapshot(
    config: dict[str, Any],
    output_dir: Path,
    cities: list[str] | None = None,
) -> Path:
    """Save immutable raw responses and a manifest; existing snapshots are reused."""
    manifest_path = output_dir / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        expected_scope = cities or ["Morocco"]
        if manifest["requested_regions"] != expected_scope:
            raise ValueError(
                "Existing snapshot has a different scope; use a new output directory"
            )
        for item in manifest["responses"]:
            raw = (output_dir / item["file"]).read_bytes()
            if hashlib.sha256(raw).hexdigest() != item["sha256"]:
                raise FetchError("Cached response SHA256 mismatch")
            validate_payload(raw)
        logger.info("Reusing checked snapshot %s (no network request)", manifest_path)
        return manifest_path
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError(
            "Nonempty incomplete snapshot directory; choose a new directory"
        )
    output_dir.mkdir(parents=True, exist_ok=True)
    regions = cities or ["Morocco"]
    responses = []
    for index, region in enumerate(regions):
        bbox = None if cities is None else config["city_bboxes"][region]
        query = build_query(int(config["query_timeout_s"]), bbox)
        if index:
            respectful_sleep(max(1, float(config["request_pause_s"])))
        raw = request_overpass(query, config)
        payload = validate_payload(raw)
        filename = (
            "pharmacies_morocco_raw.json"
            if cities is None
            else f"region_{index + 1}.json"
        )
        (output_dir / filename).write_bytes(raw)
        responses.append(
            {
                "region": region,
                "bbox": bbox,
                "file": filename,
                "query": query,
                "fetched_at": datetime.now(UTC).isoformat(),
                "osm_timestamp": payload["osm3s"].get("timestamp_osm_base"),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "bytes": len(raw),
                "elements": len(payload["elements"]),
            }
        )
        logger.info("Fetched %s: %s elements", region, len(payload["elements"]))
    manifest = {
        "source": "OpenStreetMap via Overpass",
        "endpoint": config["endpoint"],
        "attribution": "© OpenStreetMap contributors",
        "license": "https://opendatacommons.org/licenses/odbl/1-0/",
        "requested_regions": regions,
        "scope": "national_area" if cities is None else "selected_bounding_boxes_only",
        "responses": responses,
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return manifest_path


def main() -> None:
    """Fetch a national snapshot, or explicit per-city fallback boxes on a new run."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/pharmacies.yaml"))
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument(
        "--cities", nargs="+", help="Configured boxes; not national coverage"
    )
    parser.add_argument("--attempts", type=int)
    args = parser.parse_args()
    config = load_config(args.config)
    if args.attempts is not None:
        config["attempts"] = args.attempts
    if args.cities and any(city not in config["city_bboxes"] for city in args.cities):
        parser.error("Unknown city; add its query bbox to the YAML config first")
    path = fetch_snapshot(
        config, args.output_dir or Path(config["output_dir"]), args.cities
    )
    logger.info("Snapshot manifest: %s", path)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()

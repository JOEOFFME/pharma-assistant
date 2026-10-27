"""Download declared BDPM bulk files and ingest them without product-page scraping."""

import argparse
import csv
import gzip
import hashlib
import io
import json
import logging
import re
import urllib.request
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

from pharma_assistant.data.medications import (
    MedicationRecord,
    MedicationRepository,
    MedicationSource,
)
from pharma_assistant.data_tools.fetch_pharmacies import load_config
from pharma_assistant.data_tools.medication_names import generate_aliases

logger = logging.getLogger(__name__)


def published_dates(page: str, files: dict) -> dict[str, str]:
    """Read per-download dates from official download-link metadata only."""
    dates = {}
    for name in files:
        match = re.search(
            r'href="/download/file/' + re.escape(name) + r'"[^>]*>(.*?)</a>', page, re.S
        )
        date = re.search(r"\d{2}/\d{2}/\d{4}", match[1]) if match else None
        if date is None:
            raise ValueError(
                f"No published source date for {name}; review upstream metadata"
            )
        dates[name] = datetime.strptime(date[0], "%d/%m/%Y").date().isoformat()
    return dates


def read_snapshot(path: Path) -> tuple[dict, dict[str, bytes]]:
    """Validate both archive and original source byte hashes."""
    manifest = json.loads((path / "manifest.json").read_text(encoding="utf-8"))
    page = (path / "download_page.html").read_bytes()
    if hashlib.sha256(page).hexdigest() != manifest["download_page_sha256"]:
        raise ValueError("Download-page hash mismatch")
    contents = {}
    for name, meta in manifest["files"].items():
        archive = (path / meta["archive"]).read_bytes()
        if hashlib.sha256(archive).hexdigest() != meta["archive_sha256"]:
            raise ValueError(f"Archive hash mismatch: {name}")
        raw = gzip.decompress(archive)
        if hashlib.sha256(raw).hexdigest() != meta["sha256"]:
            raise ValueError(f"Source hash mismatch: {name}")
        contents[name] = raw
    return manifest, contents


def fetch_snapshot(
    config: dict,
    output: Path,
    local_downloads: Path | None = None,
    page_file: Path | None = None,
) -> None:
    """Cache immutable archives, retaining provenance for local imports."""
    if (output / "manifest.json").exists():
        read_snapshot(output)
        logger.info("Reusing verified medication snapshot without network access")
        return
    if output.exists() and any(output.iterdir()):
        raise ValueError("Use an empty output directory for a new snapshot")

    def download(url: str) -> bytes:
        request = urllib.request.Request(
            url, headers={"User-Agent": "PharmaAssistantPrototype/0.1"}
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = response.read(20 * 1024 * 1024 + 1)
        if len(raw) > 20 * 1024 * 1024:
            raise ValueError("Bulk file exceeds size limit")
        return raw

    page = page_file.read_bytes() if page_file else download(config["page_url"])
    dates = published_dates(page.decode("utf-8"), config["files"])
    output.mkdir(parents=True, exist_ok=True)
    (output / "download_page.html").write_bytes(page)
    manifest = {
        "dataset": config["source_name"],
        "country": "FR",
        "page_url": config["page_url"],
        "license_url": config["license_url"],
        "format_url": config["format_url"],
        "captured_at": datetime.now(UTC).isoformat(),
        "download_page_sha256": hashlib.sha256(page).hexdigest(),
        "import_method": (
            "local_copy_of_bulk_downloads"
            if local_downloads
            else "direct_bulk_download"
        ),
        "files": {},
    }
    for name, encoding in config["files"].items():
        url = config["page_url"].rsplit("/", 1)[0] + "/download/file/" + name
        raw = (
            (local_downloads / name).read_bytes() if local_downloads else download(url)
        )
        # Validate decoding and tabular shape before caching; no replacement characters.
        if not raw.decode(encoding).strip() or b"\t" not in raw:
            raise ValueError(f"Invalid bulk file {name}")
        archive = gzip.compress(raw, mtime=0)
        archive_name = name + ".gz"
        (output / archive_name).write_bytes(archive)
        manifest["files"][name] = {
            "url": url,
            "encoding": encoding,
            "published_date": dates[name],
            "archive": archive_name,
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "archive_sha256": hashlib.sha256(archive).hexdigest(),
        }
    (output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def parse_rows(raw: bytes, encoding: str, expected: int) -> list[list[str]]:
    """Respect source encodings, tabs and trailing fields; fail on schema drift."""
    rows = list(csv.reader(io.StringIO(raw.decode(encoding)), delimiter="\t"))
    for index, row in enumerate(rows, 1):
        if len(row) != expected or not re.fullmatch(r"\d{8}", row[0]):
            raise ValueError(
                f"Invalid source row {index}: expected {expected} fields and CIS ID"
            )
    return rows


def build_medications(config: dict) -> dict:
    """Import raw specialty/composition/presentation facts and flagged aliases."""
    manifest, contents = read_snapshot(Path(config["snapshot_dir"]))
    files = manifest["files"]
    specialties = parse_rows(
        contents["CIS_bdpm.txt"], files["CIS_bdpm.txt"]["encoding"], 12
    )
    compositions = parse_rows(
        contents["CIS_COMPO_bdpm.txt"], files["CIS_COMPO_bdpm.txt"]["encoding"], 8
    )
    packages = parse_rows(
        contents["CIS_CIP_bdpm.txt"], files["CIS_CIP_bdpm.txt"]["encoding"], 13
    )
    by_composition = defaultdict(list)
    by_package = defaultdict(set)
    for row in compositions:
        by_composition[row[0]].append(
            {
                "substance": row[3].strip(),
                "strength": row[4].strip(),
                "reference": row[5].strip(),
                "nature": row[6].strip(),
                "link_id": row[7].strip(),
            }
        )
    for row in packages:
        if row[2].strip():
            by_package[row[0]].add(row[2].strip())
    records = []
    seen = set()
    for row in specialties:
        cis, name, form = row[0], row[1].strip(), row[2].strip()
        if cis in seen or not name:
            raise ValueError("Duplicate CIS or blank source name")
        seen.add(cis)
        # Keep full_name intact; brand_name is a derived lexical family.
        stem = re.split(r"\s+(?=\d)", name.split(", ", 1)[0], maxsplit=1)[0].strip()
        composition = by_composition[cis]
        active = sorted(
            {part["substance"] for part in composition if part["nature"] == "SA"}
        )
        # Preserve the entire stated strength fragment, including combinations.
        prefix = name.split(", ", 1)[0]
        match = re.search(
            r"\b\d+(?:[.,]\d+)?\s*(?:mg|g|microgrammes?|UI|pour cent)",
            prefix,
            re.I,
        )
        dosage = prefix[match.start() :].strip() if match else None
        source = MedicationSource(
            dataset=manifest["dataset"],
            country="FR",
            source_id=cis,
            url=files["CIS_bdpm.txt"]["url"],
            license_url=manifest["license_url"],
            source_updated=files["CIS_bdpm.txt"]["published_date"],
            raw_sha256=files["CIS_bdpm.txt"]["sha256"],
        )
        records.append(
            MedicationRecord(
                id="bdpm_fr_" + cis,
                brand_name=stem,
                full_name=name,
                dci=" + ".join(active) or None,
                dosage=dosage,
                form=form or None,
                presentation=" | ".join(sorted(by_package[cis])) or None,
                laboratory=row[10].strip() or None,
                source=source,
                aliases=generate_aliases(stem, name, dosage),
                composition=composition,
                authorization_status=row[4].strip() or None,
                marketing_status=row[6].strip() or None,
            )
        )
    records.sort(key=lambda item: item.id)
    MedicationRepository(Path(config["database_path"])).replace_all(records)
    metrics = {
        "source": manifest,
        "records": len(records),
        "aliases": sum(len(row.aliases) for row in records),
        "with_dci": sum(row.dci is not None for row in records),
        "with_name_strength": sum(row.dosage is not None for row in records),
        "with_presentation": sum(row.presentation is not None for row in records),
        "with_arabic_source_name": 0,
        "with_moroccan_price": 0,
    }
    target = Path(config["metrics_path"])
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    logger.info(
        "Loaded %s specialties and %s aliases", metrics["records"], metrics["aliases"]
    )
    return metrics


def main() -> None:
    """Build offline by default; --fetch first obtains an immutable source snapshot."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/medications.yaml"))
    parser.add_argument("--fetch", action="store_true")
    parser.add_argument("--import-download-dir", type=Path)
    parser.add_argument("--download-page", type=Path)
    args = parser.parse_args()
    config = load_config(args.config)
    if args.fetch or args.import_download_dir:
        if bool(args.import_download_dir) != bool(args.download_page):
            parser.error(
                "Local import requires both bulk-download directory and saved page"
            )
        fetch_snapshot(
            config,
            Path(config["snapshot_dir"]),
            args.import_download_dir,
            args.download_page,
        )
    build_medications(config)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()

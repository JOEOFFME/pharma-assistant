"""Clean a hash-verified Overpass snapshot into CSV, SQLite and a coverage report."""

import argparse
import csv
import hashlib
import json
import logging
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from pharma_assistant.data.pharmacies import (
    PharmacyRecord,
    PharmacyRepository,
    haversine_km,
)
from pharma_assistant.data_tools.fetch_pharmacies import load_config, validate_payload
from pharma_assistant.data_tools.pharmacy_normalize import (
    display_text,
    normalize_city,
    normalize_name,
    normalize_phones,
)

logger = logging.getLogger(__name__)


def quality_score(row: PharmacyRecord) -> float:
    """Completeness only: equal weight to name, city, phone, hours and coordinates."""
    return (
        sum(
            (
                bool(row.name),
                bool(row.city),
                bool(row.phones_e164),
                bool(row.opening_hours),
                True,
            )
        )
        / 5
    )


def record_from_element(
    element: dict[str, Any], region: str, aliases: dict[str, str]
) -> PharmacyRecord | None:
    """Preserve display names and unknowns; use way/relation centers when available."""
    if (
        element.get("type") not in {"node", "way", "relation"}
        or type(element.get("id")) is not int
    ):
        return None
    tags = element.get("tags", {})
    if not isinstance(tags, dict) or tags.get("amenity") != "pharmacy":
        return None
    coordinates = element if element["type"] == "node" else element.get("center", {})
    if not isinstance(coordinates, dict):
        return None
    try:
        if isinstance(coordinates.get("lat"), bool) or isinstance(
            coordinates.get("lon"), bool
        ):
            return None
        lat, lon = float(coordinates["lat"]), float(coordinates["lon"])
    except (KeyError, TypeError, ValueError):
        return None
    if not (
        math.isfinite(lat)
        and math.isfinite(lon)
        and -90 <= lat <= 90
        and -180 <= lon <= 180
    ):
        return None
    name_ar, name_fr = display_text(tags.get("name:ar")), display_text(
        tags.get("name:fr")
    )
    name = display_text(tags.get("name")) or name_fr or name_ar
    names = [
        name,
        name_fr,
        name_ar,
        display_text(tags.get("official_name")),
        display_text(tags.get("alt_name")),
    ]
    names = sorted({name for name in names if name})
    raw_city = display_text(tags.get("addr:city"))
    city = normalize_city(raw_city, aliases)
    raw_phones = sorted(
        {
            value
            for key in ["phone", "contact:phone", "contact:mobile", "mobile"]
            if (value := display_text(tags.get(key)))
        }
    )
    phones, rejected = normalize_phones(raw_phones)
    hours = display_text(tags.get("opening_hours"))
    source_id = f"{element['type']}/{element['id']}"
    row = PharmacyRecord(
        id=source_id,
        name=name,
        name_ar=name_ar,
        name_fr=name_fr,
        aliases=names,
        city=city,
        city_raw=[raw_city] if raw_city else [],
        latitude=lat,
        longitude=lon,
        phones_e164=phones,
        phones_raw=raw_phones,
        rejected_phones=rejected,
        opening_hours=hours,
        hours_variants=[hours] if hours else [],
        source_ids=[source_id],
        source_urls=[f"https://www.openstreetmap.org/{source_id}"],
        query_regions=[region],
        data_quality=0,
    )
    row.data_quality = quality_score(row)
    return row


def merge_records(target: PharmacyRecord, other: PharmacyRecord) -> None:
    """Fill missing fields and preserve alternative values and provenance."""
    for field in ["name", "name_ar", "name_fr", "city", "opening_hours"]:
        if getattr(target, field) is None:
            setattr(target, field, getattr(other, field))
    for field in [
        "aliases",
        "city_raw",
        "phones_e164",
        "phones_raw",
        "rejected_phones",
        "hours_variants",
        "source_ids",
        "source_urls",
        "query_regions",
    ]:
        setattr(
            target, field, sorted(set(getattr(target, field) + getattr(other, field)))
        )
    target.data_quality = quality_score(target)


def clean_elements(
    items: list[tuple[dict[str, Any], str]], config: dict[str, Any]
) -> tuple[list[PharmacyRecord], dict[str, int]]:
    """Deduplicate IDs and cautious same-name/nearby duplicate map objects."""
    aliases = {
        normalize_name(key): value for key, value in config["city_aliases"].items()
    }
    by_source: dict[str, PharmacyRecord] = {}
    stats = Counter(
        input_elements=len(items),
        dropped_invalid=0,
        duplicate_source_ids=0,
        merged_map_objects=0,
    )
    for element, region in sorted(
        items,
        key=lambda pair: (str(pair[0].get("type")), str(pair[0].get("id")), pair[1]),
    ):
        row = record_from_element(element, region, aliases)
        if row is None:
            stats["dropped_invalid"] += 1
            continue
        if row.id in by_source:
            merge_records(by_source[row.id], row)
            stats["duplicate_source_ids"] += 1
        else:
            by_source[row.id] = row
    kept: list[PharmacyRecord] = []
    name_groups: dict[str, list[PharmacyRecord]] = defaultdict(list)
    threshold = float(config["dedupe_distance_m"])
    if not 0 <= threshold <= 50:
        raise ValueError("Dedupe distance must be 0-50 m")
    generic = {"pharmacie", "pharmacy", "صيدلية", "الصيدلية"}
    for row in by_source.values():
        name_key = normalize_name(row.name or "")
        duplicate = None
        if name_key and name_key not in generic:
            for candidate in name_groups[name_key]:
                # Conflicting observed cities, phones or hours make a merge unsafe.
                conflict = (
                    (candidate.city and row.city and candidate.city != row.city)
                    or (
                        candidate.phones_e164
                        and row.phones_e164
                        and not set(candidate.phones_e164) & set(row.phones_e164)
                    )
                    or (
                        candidate.opening_hours
                        and row.opening_hours
                        and candidate.opening_hours != row.opening_hours
                    )
                )
                if (
                    not conflict
                    and haversine_km(
                        candidate.latitude,
                        candidate.longitude,
                        row.latitude,
                        row.longitude,
                    )
                    * 1000
                    <= threshold
                ):
                    duplicate = candidate
                    break
        if duplicate is None:
            kept.append(row)
            name_groups[name_key].append(row)
        else:
            merge_records(duplicate, row)
            stats["merged_map_objects"] += 1
    stats["retained"] = len(kept)
    return sorted(kept, key=lambda row: row.id), dict(stats)


def coverage_metrics(
    records: list[PharmacyRecord], stats: dict[str, int]
) -> dict[str, Any]:
    """Compute counts and percentages with explicit per-group denominators."""

    def summarize(rows: list[PharmacyRecord]) -> dict[str, Any]:
        total = len(rows)
        counts = {
            "name": sum(bool(row.name) for row in rows),
            "city": sum(bool(row.city) for row in rows),
            "phone": sum(bool(row.phones_e164) for row in rows),
            "hours": sum(bool(row.opening_hours) for row in rows),
            "duty_known": sum(row.is_on_duty is not None for row in rows),
        }
        return {
            "rows": total,
            "counts": counts,
            "percent": {
                key: round(value / total * 100, 2) if total else 0.0
                for key, value in counts.items()
            },
        }

    cities: dict[str, list[PharmacyRecord]] = defaultdict(list)
    for row in records:
        cities[row.city or "Unknown (addr:city absent)"].append(row)
    return {
        "cleaning": stats,
        "overall": summarize(records),
        "by_city": {city: summarize(rows) for city, rows in sorted(cities.items())},
        "rows_with_rejected_phones": sum(bool(row.rejected_phones) for row in records),
        "mean_completeness": (
            round(sum(row.data_quality for row in records) / len(records), 4)
            if records
            else 0
        ),
    }


def build_directory(manifest_path: Path, config: dict[str, Any]) -> dict[str, Any]:
    """Rebuild from verified saved bytes without network access or inferred facts."""
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    items = []
    for response in manifest["responses"]:
        raw = (manifest_path.parent / response["file"]).read_bytes()
        if hashlib.sha256(raw).hexdigest() != response["sha256"]:
            raise ValueError("Snapshot hash mismatch; refusing modified source data")
        payload = validate_payload(raw)
        items.extend((element, response["region"]) for element in payload["elements"])
    records, stats = clean_elements(items, config)
    csv_path = Path(config["csv_path"])
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(PharmacyRecord.model_fields)
    with csv_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in records:
            data = row.model_dump()
            writer.writerow(
                {
                    key: (
                        json.dumps(value, ensure_ascii=False)
                        if isinstance(value, list)
                        else value
                    )
                    for key, value in data.items()
                }
            )
    repository = PharmacyRepository(
        Path(config["database_path"]), config["city_aliases"]
    )
    repository.replace_all(records)
    metrics = coverage_metrics(records, stats)
    metrics.update(
        source=manifest,
        disclaimer="Directory completeness only; no stock or live duty information.",
    )
    # Reproducible real-data smoke queries; distances are not accuracy measurements.
    centers = {
        "Rabat": (34.0209, -6.8416),
        "Casablanca": (33.5731, -7.5898),
        "Marrakech": (31.6295, -7.9811),
    }
    metrics["nearest_smoke"] = {
        city: [
            {"id": nearby.pharmacy.id, "distance_km": round(nearby.distance_km, 6)}
            for nearby in repository.nearest(*coords, k=3)
        ]
        for city, coords in centers.items()
    }
    metrics_path = Path(config["metrics_path"])
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    write_report(metrics, Path(config["report_path"]))
    logger.info("Built %s records into %s", len(records), config["database_path"])
    return metrics


def write_report(metrics: dict[str, Any], path: Path) -> None:
    """Generate the Markdown coverage report solely from saved metrics."""
    manifest = metrics["source"]
    overall = metrics["overall"]
    lines = [
        "# Pharmacy directory coverage",
        "",
        "This saved OSM snapshot is not a census of Moroccan pharmacies.",
        "",
        "© OpenStreetMap contributors. Source/derived data: ODbL 1.0.",
        "[OSM attribution](https://www.openstreetmap.org/copyright)",
        "[ODbL licence](https://opendatacommons.org/licenses/odbl/1-0/)",
        "",
        f"Query scope: `{manifest['scope']}`.",
        "Regions: " + ", ".join(manifest["requested_regions"]),
        "",
        "## Source snapshots",
        "",
        "| Region | OSM timestamp | Elements | SHA256 |",
        "| --- | --- | ---: | --- |",
    ]
    for source in manifest["responses"]:
        lines.append(
            f"| {source['region']} | {source['osm_timestamp']} | "
            f"{source['elements']} | `{source['sha256']}` |"
        )
    lines += ["", "## Cleaning audit", "", "| Metric | Count |", "| --- | ---: |"]
    lines += [f"| {key} | {value} |" for key, value in metrics["cleaning"].items()]
    lines += [
        "",
        "## Field coverage",
        "",
        f"Denominator: {overall['rows']} retained directory records.",
        "",
        "| Field | Present | Percent |",
        "| --- | ---: | ---: |",
    ]
    lines += [
        f"| {key} | {value} | {overall['percent'][key]:.2f}% |"
        for key, value in overall["counts"].items()
    ]
    lines += [
        "",
        "## Coverage by observed city",
        "",
        "Unknown cities are not guessed from coordinates or query boxes.",
        "",
        "| City | Records | Name % | Phone % | Hours % |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for city, group in metrics["by_city"].items():
        safe_city = city.replace("|", r"\|").replace("\n", " ")
        pct = group["percent"]
        lines.append(
            f"| {safe_city} | {group['rows']} | {pct['name']:.2f}% | "
            f"{pct['phone']:.2f}% | {pct['hours']:.2f}% |"
        )
    lines += [
        "",
        "## Interpretation and limitations",
        "",
        f"Rows with rejected phone fragments: {metrics['rows_with_rejected_phones']}.",
        f"Mean completeness score: {metrics['mean_completeness']:.4f}.",
        "",
    ]
    lines += """A present phone passes the pinned phonenumbers syntax/metadata checks.
Ownership and reachability are unverified. Invalid fragments remain in the CSV
for audit; phone values are never guessed.

Opening hours are raw OSM strings, not parsed schedules or current status.
is_on_duty, duty_from and duty_to remain null: no authoritative garde feed exists
in this input. Directory results cannot establish stock, prices or duty status.

Data quality is completeness: (name + city + valid phone + hours + coordinates)
/ 5. It is not factual confidence. Coordinates are present for all retained rows.

Deduplication merges identical OSM IDs and cautious nearby same-name objects,
not all real-world duplicates. Invalid coordinates are dropped; way/relation
centers are not guaranteed entrances. Cities come only from addr:city/aliases.
Unknown-city records remain eligible for nearest search. Missing mapped
pharmacies cannot be quantified without an external reference.

## Rebuild

```bash
make pharmacies
```

Rebuild uses the committed snapshot and needs no network. See
[data instructions](../data/pharmacies/README.md) for refresh and licensing.
Machine-readable counts, hashes and nearest-query smoke results:
[pharmacy_coverage.json](pharmacy_coverage.json).

The original fetch_pharmacies.py was not supplied. This is a new fetcher;
behavior-preserving equivalence with the missing script is unverified.
""".splitlines()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    """Load a saved manifest and generate derived artifacts."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/pharmacies.yaml"))
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    config = load_config(args.config)
    build_directory(
        args.manifest or Path(config["output_dir"]) / "manifest.json", config
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()

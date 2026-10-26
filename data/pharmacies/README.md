# Pharmacy directory - TASK 3

© OpenStreetMap contributors. The committed OSM extract and derived pharmacy
database/CSV are available under the
[Open Database License 1.0](https://opendatacommons.org/licenses/odbl/1-0/).
[OSM source and attribution](https://www.openstreetmap.org/copyright).
This data licence does not assign a licence to unrelated application code.

## Rebuild the saved snapshot offline

From the repository root, after `make install`:

```bash
make pharmacies
```

Outputs:

- `data/pharmacies/pharmacies_morocco.csv`: normalized records, source links,
  raw/rejected phone values and completeness scores.
- `data/pharmacies/pharmacies.sqlite3`: populated `pharmacies` table.
- `docs/data_pharmacies.md`: field and city coverage report.
- `docs/pharmacy_coverage.json`: machine-readable audit, source hashes and
  nearest-query smoke results around Rabat, Casablanca and Marrakech anchors.

The generated CSV and database are ignored by Git. The immutable raw response
and manifest in `data/raw/osm_snapshot/` are committed for deterministic rebuilds.
Never edit raw JSON manually. Every rebuild verifies its SHA256 first. The report
and metrics are tracked; identical source bytes/config produce identical results.
No schema test makes a network request.

## Refresh, reuse and fallback

```bash
make fetch-pharmacies
```

The default snapshot already exists, so this command verifies/reuses it without
another request. To fetch a new national snapshot, use a **new directory**:

```bash
uv run --frozen python -m pharma_assistant.data_tools.fetch_pharmacies \
  --output-dir data/raw/osm_refresh
uv run --frozen python -m pharma_assistant.data_tools.clean_pharmacies \
  --manifest data/raw/osm_refresh/manifest.json
```

If the national query times out, allow the reported cooldown before explicitly
requesting a few configured city boxes in another new directory:

```bash
uv run --frozen python -m pharma_assistant.data_tools.fetch_pharmacies \
  --cities Rabat Casablanca Marrakech --output-dir data/raw/osm_city_fallback
uv run --frozen python -m pharma_assistant.data_tools.clean_pharmacies \
  --manifest data/raw/osm_city_fallback/manifest.json
```

Such a run is **selected bounding boxes only**, not national coverage. Query
regions are provenance; they are never assigned as if they were observed cities.
The refresh/fallback command regenerates the tracked report for that new scope;
review the diff before committing it. Keep the original snapshot immutable.

Configure endpoint, timeouts, attempt count, cooldown, size limit, paths,
city aliases, boxes and dedupe distance in `configs/pharmacies.yaml`. Requests
are sequential; default backoff is exponential, Retry-After is honored, and
nonretryable errors abort. A partial JSON response with an Overpass remark is
rejected. Use `--attempts 1` to disable retries during a one-off diagnostic.
The script does not hop endpoints or automatically cascade into many city queries.

[Overpass public-instance policy](https://dev.overpass-api.de/overpass-doc/en/preface/commons.html)
was consulted on 2026-10-26. Cache extracts, avoid repeated harvesting and use
an appropriate hosted/self-run service for a production backend. This prototype
uses Overpass only as an offline data source, never per patient request.

## Cleaning and query semantics

- Names retain display values. Search keys casefold, remove diacritics/tatweel
  and normalize common Arabic alef/ya variants; no translation is invented.
- City correction uses explicit aliases. A multilingual city label is reduced
  to its Latin part only if that part matches a configured alias. Unknown labels
  stay raw; numeric/placeholder city fields become unknown with city_raw kept.
  No reverse geocoder or city assignment by query box is used.
- Phones are split conservatively and validated for Morocco under pinned
  `phonenumbers` metadata, then formatted as +212 E.164. Syntactic validity does
  not prove ownership, active service or reachability. Original values and
  rejected fragments remain available. No source phone is guessed or called.
  See [upstream documentation](https://daviddrysdale.github.io/python-phonenumbers/).
- `opening_hours` is preserved verbatim, without asserting the pharmacy is open
  now. `is_on_duty`, `duty_from`, `duty_to` are nullable and stay unset until an
  authoritative, time-stamped garde source is integrated. `24/7` alone does not
  establish an official on-duty designation.
- Deduplicate exact OSM IDs, then non-generic normalized names within 10 m when
  observed city, valid phone and hours do not conflict. Keep all source IDs,
  names and observed alternatives. This may still miss or merge map duplicates;
  provenance permits audit. Different names and generic `Pharmacie` points are
  not merged just for proximity. Seven map objects were merged into retained records in this snapshot.
- Drop invalid/missing world coordinates; all retained records use node points
  or way/relation centers. Polygon centers are not necessarily entrances.
- `data_quality` is `(name + city + valid phone + hours + coordinates) / 5`,
  a completeness score, not factual correctness or confidence.
- `nearest(lat, lon, k)` uses spherical straight-line distance over the stored
  snapshot. It does not compute road travel, enforce city limits or guarantee a
  nearby result if the mapped directory is sparse. At most 100 results can be
  requested. Scanning this small snapshot is acceptable; an R-tree is future work.
- `search_by_name` matches literal normalized substrings, not SQL wildcard input.
  `by_city` searches the observed/corrected city, not an inferred catchment area.

## Repository usage

```python
from pathlib import Path
from pharma_assistant.data.pharmacies import PharmacyRepository
from pharma_assistant.data_tools.fetch_pharmacies import load_config

config = load_config(Path("configs/pharmacies.yaml"))
repo = PharmacyRepository(Path(config["database_path"]), config["city_aliases"])
near_rabat = repo.nearest(34.0209, -6.8416, k=3)
in_marrakech = repo.by_city("Marrakech")
name_matches = repo.search_by_name("صيدلية", limit=10)
```

The original fetch_pharmacies.py mentioned in AGENTS.md was not provided. This
new fetcher implements the stated purpose, but preservation of the missing
script's exact behavior cannot be verified. No medication source or TASK 4
scraper is part of this task.

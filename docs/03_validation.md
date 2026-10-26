# TASK 3 - Validation Report

Date: 2026-10-26. TASK 2 was validated before work began.
Status: implemented and ready for review; original-script equivalence unverified.

## Built and changed files

| File/group | Purpose |
| --- | --- |
| configs/pharmacies.yaml | Endpoint, cooldowns/retries, output paths, city aliases, optional bbox queries and dedupe threshold. |
| src/pharma_assistant/data_tools/fetch_pharmacies.py | New sequential Overpass CLI with retries/backoff, Retry-After, caching, response checks and immutable provenance. |
| src/pharma_assistant/data_tools/pharmacy_normalize.py | Arabic/French search keys, city normalization and Moroccan E.164 phone validation. |
| src/pharma_assistant/data_tools/clean_pharmacies.py | Hash-verified ingestion, deduplication, CSV/database build and coverage generation. |
| src/pharma_assistant/data/{__init__,pharmacies}.py | Typed records and SQLite repository: search_by_name, nearest and by_city. |
| data/raw/osm_snapshot/{manifest,pharmacies_morocco_raw}.json | Real attributed OSM response, query/timestamps, source checksum and scope. |
| data/raw/README.md, data/pharmacies/README.md | Source/data licensing, rebuild/refresh/fallback instructions, query semantics and limitations. |
| docs/data_pharmacies.md, docs/pharmacy_coverage.json | Generated Markdown/JSON counts, percentages, audit and nearest-query smoke results. |
| tests/test_pharmacies.py | Forty added cases, using synthetic unit fixtures and the saved real snapshot offline. |
| pyproject.toml, uv.lock | Pin phonenumbers 9.0.41 and PyYAML 6.0.3 as runtime dependencies; frozen dependency resolution. |
| Makefile, README.md, .gitignore | Rebuild/fetch targets, directory documentation and narrow raw-snapshot tracking exceptions. |
| docs/03_validation.md | This report. |

The generated CSV and SQLite file exist locally and are rebuilt with one command;
they are ignored by Git to avoid duplicating the raw source and derived data.
The committed raw bytes make both outputs reproducible after a fresh clone.
No medication dataset, scraper or TASK 4 code is introduced.

## Source and actual coverage

A single live national-area request succeeded. It queried OSM's area tagged
ISO3166-1=MA for amenity=pharmacy nodes, ways and relations; this is the query's
scope, not a verified complete national registry or a boundary claim.

- OSM source timestamp: 2026-10-26T19:10:31Z.
- Fetch timestamp: 2026-10-26T19:11:41.986949+00:00.
- Raw response: 2,383,815 bytes, 6,952 elements.
- SHA256: 54add4786d5447e40763998396a4dc65b4ff28b7d2f35a2377c2bf9bc6648a90.
- Seven same-name nearby map objects merged; 6,945 records retained.
- No invalid-coordinate rows or repeated source IDs occurred in this snapshot;
  both failure modes are exercised by synthetic tests.

| Field | Present / 6,945 | Coverage |
| --- | ---: | ---: |
| Name | 6,732 | 96.93% |
| Observed/corrected city | 5,886 | 84.75% |
| Valid Moroccan E.164 phone | 658 | 9.47% |
| Raw opening-hours tag | 48 | 0.69% |
| Known duty status | 0 | 0.00% |

All values above derive from docs/pharmacy_coverage.json. Unknown-city records
remain in nearest search; cities are not filled from query boxes. Invalid city
labels and rejected phone fragments remain traceable to raw fields/source bytes.
Phone validation does not verify ownership or contactability; hours are not
parsed schedules or proof that a pharmacy is open now.

© OpenStreetMap contributors. Source and derived data: ODbL 1.0.
https://www.openstreetmap.org/copyright
https://opendatacommons.org/licenses/odbl/1-0/

## Exact commands and expected output

From the repository root after cloning/pulling:

```bash
make install
make pharmacies
make lint
make test
uv run --frozen pytest tests/test_pharmacies.py -v
uv run --frozen pre-commit run --all-files
git diff --check
```

Expected: build logs 6,945 records into data/pharmacies/pharmacies.sqlite3;
CSV, database, JSON metrics and Markdown report are generated; Ruff/Black pass;
320 total tests pass, including 40 pharmacy cases. Rebuild makes no HTTP request.

To verify cache reuse explicitly:

```bash
make fetch-pharmacies
```

Expected: reuses the checked snapshot and logs that there is no network request.
For a new fetch, use a new output directory. Explicit per-city fallback commands
are in data/pharmacies/README.md; bbox coverage is labelled as partial. Requests
are not made per patient query. Public-instance policy was consulted:
https://dev.overpass-api.de/overpass-doc/en/preface/commons.html

## Actual validation results

Executed with CPython 3.11.17, uv 0.13.4 and the updated frozen dependencies:

```text
uv run --frozen python -m pharma_assistant.data_tools.fetch_pharmacies --attempts 1
  Fetched Morocco: 6952 elements
make pharmacies
  Built 6945 records into data/pharmacies/pharmacies.sqlite3
make fetch-pharmacies
  Reusing checked snapshot ... (no network request)
make lint
  Ruff: All checks passed!
  Black: 21 files would be left unchanged.
make test
  collected 320 items
  320 passed, 1 warning in 3.98s
```

Tests include coordinate/center validation, Arabic/accent/city normalization,
metadata example-phone formatting, conservative deduplication/conflict handling,
SQL escaping, atomic snapshot replacement, invalid query arguments, national/bbox
scope, timeout/partial-response rejection, 429 cooldown, nonretryable HTTP errors,
cache scope/hash checks, and empty-report denominators. No test makes live HTTP
requests. Real-data tests rebuild into a temporary database, compare all saved
metrics/report text, and run nearest queries around all three city anchors.
Pre-commit and staged whitespace checks are run before the single task commit.
The existing Starlette/AnyIO deprecation warning remains unchanged.

Real nearest smoke queries (straight-line distance to first stored location):

| Anchor (latitude, longitude) | First source ID | Distance km |
| --- | --- | ---: |
| Rabat (34.0209, -6.8416) | node/8191100944 | 0.145007 |
| Casablanca (33.5731, -7.5898) | node/5593149218 | 0.220225 |
| Marrakech (31.6295, -7.9811) | node/8483710823 | 0.189168 |

These are smoke results, not accuracy, travel time, stock or duty verification.

## Acceptance checklist

- ✅ Pharmacy fetch CLI, logging, bounded attempts/backoff and explicit city bbox fallback.
- ✅ Real pharmacy table populated with 6,945 records and rebuildable from committed bytes.
- ✅ Names/cities normalized, Moroccan phones formatted to E.164, coordinate rejection and deduplication implemented.
- ✅ data_quality completeness score defined and exported.
- ✅ search_by_name, nearest and by_city implemented and tested.
- ✅ nearest tested with Rabat, Casablanca and Marrakech anchors on fixtures and actual data.
- ✅ Coverage report counts by observed city and name/phone/hours percentages generated.
- ✅ Null is_on_duty, duty_from and duty_to reserved for a future authoritative feed.
- ✅ OSM attribution, data licence, source hashes, timestamp/scope and sparse-data limits documented.
- ⚠️ Original fetch_pharmacies.py was never supplied: exact behavior preservation cannot be verified. A new implementation fulfills the described purpose.

## Remaining limitations

OSM is incomplete and may contain stale or incorrect information. Name/proximity
merges are heuristic and auditable through retained source IDs. Completeness
scores are not factual confidence. No live garde feed, stock or price source is
available. Directory coordinates can be polygon centers rather than entrances;
nearest is a spherical scan suitable for this snapshot, not a routing engine.
Unknown city labels are preserved unless a configured alias resolves them.
Synthetic test phones come from phonenumbers example metadata and are never
loaded into production data. No phone numbers were invented for missing records.

TASK 4 has not started. Continue only after VALIDATED TASK 3.

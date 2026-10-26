# Medication reference - TASK 4

**This is the official French BDPM bulk reference, used as an open fallback. It
is not a Moroccan authorization, product-availability, stock or PPV database.**

The Moroccan CNOPS listing was discoverable on data.gov.ma, but its dataset
page/resource/API returned HTTP 503 or timed out during the 2026-10-26 source
check. No proprietary medication site was scraped. A Moroccan source can be
added later through a separate, reviewed importer; do not relabel French IDs.

## Producer, source and licence

Producer: Base de données publique des médicaments (ANSM/HAS/UNCAM), France.
Source: https://base-donnees-publique.medicaments.gouv.fr/telechargement
Linked Licence Ouverte **version 1.0**, not an assumed version 2.0:
https://base-donnees-publique.medicaments.gouv.fr/docs/telechargement/licence_bdpm.pdf

The published terms allow data reuse with source/update-date attribution and
without implying official endorsement. Retain the original bytes, identify
transformations, and check updates before any current operational use. This
prototype is an unofficial, dated reference demonstration. The source page and
per-file published dates are preserved in the snapshot manifest for review.

File-format documentation (v5):
https://base-donnees-publique.medicaments.gouv.fr/download/file/Contenu_et_format_des_fichiers_telechargeables_dans_la_BDM_v5.pdf

## Offline build and evaluation

After `make install`, from the repository root:

```bash
make medications
```

This verifies the compressed and original source hashes, rebuilds
`data/medications/medications.sqlite3`, writes inventory metrics, runs the fixed
50-query mini-set and regenerates the report. No live request, model download or
API key is required. The SQLite file is ignored by Git and recreated locally;
original source files are committed as deterministic gzip archives in
`data/raw/bdpm_snapshot/`. Decompression recovers the original bytes exactly.

- `docs/data_medications.md`: source dates, inventory, evaluation and limitations.
- `docs/medication_metrics.json`: counts and source hashes.
- `docs/examples/medication_queries_50.json`: fifty individually authored queries,
  source-derived acceptable ID sets and explicit pending-review status.
- `docs/medication_query_results.json`: ranked candidates, scores, correctness
  flags, query hash, matching config and source hashes.

The mini-set is unreviewed and purposive, not a gold set or an independent
real-world test. Underspecified brand queries can accept several compatible
source IDs. Its acceptable-ID accuracy is not unique-product accuracy. No
thresholds are tuned by the evaluator; native-speaker review and a larger
held-out query set are still needed.

## Schema and field mapping

One record per BDPM specialty (CIS). Namespaced ID: `bdpm_fr_<CIS>`.

| Field | Mapping / missing-value policy |
| --- | --- |
| full_name | Unchanged source specialty label, apart from outer whitespace. |
| brand_name | Derived lexical family: source name before strength and form; not an asserted official brand ontology. |
| brand_name_ar | Null: official Arabic labels are absent. Generated Arabic aliases do not populate it. |
| dci | Joined source `SA` active-substance names; not an inferred WHO-INN conversion. Raw SA/ST composition details remain available. |
| dosage | Whole stated strength fragment from the specialty-name prefix. Combination strengths remain intact. It is never a dosing regimen. |
| form | Source pharmaceutical form. |
| presentation | All distinct source presentation labels, joined with a pipe delimiter; no preferred package is inferred. |
| laboratory | Source marketing-authorization holder(s), not a manufacturer inferred from a brand. |
| price_ppv | Null: French price columns are not Moroccan PPV and are intentionally not imported as such. |
| source | Dataset, country FR, source CIS, URL, licence URL, source date and raw specialty-file SHA256. |
| authorization_status, marketing_status | Preserved source values, including non-active/non-marketed entries. No inference of present availability. |
| aliases | Exact source fragments/labels plus flagged programmatic variants. |

Source encodings are explicit: specialty/composition files are Windows-1252;
the observed presentation file is UTF-8. Tabs, trailing columns and Unicode are
preserved. Column counts and CIS identity shape are checked; unexpected source
changes fail rather than silently shifting fields. The current snapshot is
fully ingested, without sample-only catalogue rows.

## Aliases and search

`MedicationIndex.search(query, k=3)` returns candidates with reference records,
weighted similarity, name/TF-IDF components, matched alias, synthetic flag,
strength-match status and clarification flag. It never recommends an equivalent
medicine, fills a missing ingredient or gives clinical advice.

Retrieval combines RapidFuzz WRatio and character word-boundary TF-IDF (2-4
characters). Approximate cross-script keys are generated deterministically.
Spelling aliases include lowercase/accent folding, rough Arabic transliteration,
Arabizi lexical noise, deletion and transposition. Every generated alias is
flagged synthetic and needs native-speaker review. No generated spelling is
presented as an approved Arabic product name.

Explicit strength and form constraints filter candidates. Simple grams/milligrams
are compared arithmetically; concentrations remain distinct from plain mass and
compound expressions retain their components. A bare number such as `1000` can
filter a mentioned product number but does not infer a unit. This is reference
attribute matching, never dose selection. Unmatched/unknown queries may return
an empty list. A bare brand with several plausible variants retains ambiguity.
Scores are similarities in [0,1], not calibrated correctness probabilities.

```python
from pathlib import Path
from pharma_assistant.data_tools.fetch_pharmacies import load_config
from pharma_assistant.matching.medications import MedicationIndex

config = load_config(Path("configs/medications.yaml"))
index = MedicationIndex.from_database(
    Path(config["database_path"]), config["matching"]
)
candidates = index.search("دوليبران", k=3)
```

Do not force-select the first result when clarification is required. Even a
high name similarity can confuse products; catalogue identity and clinical
appropriateness are separate. No therapeutic substitution logic is implemented.

## Refresh

```bash
make fetch-medications
```

The existing snapshot is hash-verified and reused without network access. For a
new source capture, copy `configs/medications.yaml`, change `snapshot_dir` to a
new empty directory, then use:

```bash
uv run --frozen python -m pharma_assistant.data_tools.ingest_medications \
  --config configs/medications_refresh.yaml --fetch
```

The fetcher downloads the declared bulk files only and reads published dates
from their download-link metadata. It does not crawl product pages. Review file
dates, encodings, hashes, status fields and changed terms before publishing a
refreshed source. Update expected query IDs if the source changes, with review;
do not change labels just to improve scores.

The first snapshot was packaged from bulk bytes downloaded directly from the
source during this session. `import_method=local_copy_of_bulk_downloads` records
that packaging route honestly. The CLI also supports importing such previously
downloaded files with `--import-download-dir` and `--download-page`; those options
do not independently authenticate a supplied local file's origin.

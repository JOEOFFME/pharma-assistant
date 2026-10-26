# TASK 4 - Validation Report

Date: 2026-10-26. TASK 3 was validated before this work. The user confirmed that
no medication source file was available and requested a public source.
Status: implemented and ready for review, with an explicit France-only fallback.

## Source decision

The Moroccan CNOPS medication reference on data.gov.ma was identified, but
access to its page/resource/API returned HTTP 503 or timed out. The French
BDPM official bulk files were proposed before ingestion code was written.
No commercial product listing was scraped.

BDPM's official download page, linked Licence Ouverte 1.0 and file-format v5
document were checked. Source byte hashes, observed publication dates, URLs and
the saved download page are preserved. Git attributes prevent newline conversion
and preserve the original HTML whitespace instead of editing source bytes. This is an unofficial, dated reuse;
source attribution/update terms apply and the user should review them.

- Producer: BDPM (ANSM/HAS/UNCAM), France.
- Source page: https://base-donnees-publique.medicaments.gouv.fr/telechargement
- Licence: https://base-donnees-publique.medicaments.gouv.fr/docs/telechargement/licence_bdpm.pdf
- Specialties and compositions: published date observed 2026-09-29.
- Presentations: published date observed 2026-10-26.
- Country is explicitly FR. No Moroccan stock, authorization or PPV is inferred.

## Built and changed files

| File/group | Purpose |
| --- | --- |
| configs/medications.yaml | Source, encoding, output and matching configuration. |
| data/raw/bdpm_snapshot/ | Manifest, original download page and three losslessly compressed bulk source files. |
| src/pharma_assistant/data_tools/ingest_medications.py | Cached bulk download/local-import route, hash/shape checks and deterministic ingestion. |
| src/pharma_assistant/data_tools/medication_names.py | Normalization and synthetic Arabic/Arabizi/typo aliases. |
| src/pharma_assistant/data/medications.py | Typed normalized reference models and SQLite medication/alias tables. |
| src/pharma_assistant/matching/medications.py | RapidFuzz + character TF-IDF search, strength/form constraints and ambiguity flags. |
| src/pharma_assistant/eval/medication_resolution.py | Fixed 50-query evaluation and report generation. |
| docs/examples/medication_queries_50.json | Individually authored queries and source-derived acceptable IDs, pending review. |
| docs/medication_metrics.json | Reproducible inventory and source hashes. |
| docs/medication_query_results.json | Every candidate list, score, expected set and correctness flag. |
| docs/data_medications.md | Generated source/inventory/evaluation report. |
| data/medications/README.md | Licence attribution, schema mappings, offline build, refresh and limitations. |
| tests/test_medications.py | Twenty-five added cases, including offline real-source rebuild/evaluation. |
| pyproject.toml, uv.lock | Exact RapidFuzz 3.14.6 and scikit-learn 1.9.1 runtime dependencies plus locked transitives. |
| Makefile, README.md, .gitignore, .gitattributes | Build/fetch targets, documentation and narrow snapshot-tracking exceptions. |
| docs/04_validation.md | This report. |

The SQLite file is generated and ignored by Git; the compressed original bytes
are committed so it can be rebuilt after cloning. The original source bytes
were downloaded directly during source inspection, then packaged through the
CLI's local-import route. import_method records that route, not a fictional
execution of the automatic fetcher.

## Actual inventory and evaluation

- N = **15,883** source specialties loaded.
- **161,618** alias records; generated variants are explicitly synthetic.
- **15,881** records have source SA active-substance names.
- **12,689** have a source product-name strength fragment.
- **14,620** have source presentation labels.
- Official Arabic names: absent; brand_name_ar remains null.
- Moroccan PPV: absent; price_ppv remains null.

Similarity combines RapidFuzz WRatio and character word-boundary TF-IDF (2-4
grams). Explicit product strengths/forms filter candidates. Bare-family queries
preserve ambiguity; grams/milligrams are comparable arithmetically, while
concentrations remain separate from plain mass. No therapeutic relationship,
substitution, dose selection or diagnosis is inferred.

The 50 individually authored review queries produced:

| Measure | Result |
| --- | ---: |
| Top-1 acceptable-ID hits | 50/50 (100.00%) |
| Top-3 acceptable-ID hits | 50/50 (100.00%) |
| Queries with multiple acceptable IDs | 37/50 |

These are **unreviewed mini-set results**, not a gold benchmark or unique-product
accuracy claim. Thirty-seven queries accept several family/attribute-compatible
IDs; a correct hit can still require clarification. Expected sets were labelled
from the source catalogue, independently of the search output, and remain for
user review. Results/config/query and source hashes are saved; no numbers are
estimated or borrowed from another project. A held-out native-speaker set and
Moroccan-source evaluation remain future work.

## Exact commands and expected output

From the repository root after pulling/cloning:

```bash
make install
make medications
make lint
make test
uv run --frozen pytest tests/test_medications.py -v
uv run --frozen pre-commit run --all-files
git diff --check
```

Expected: offline build logs 15,883 specialties / 161,618 aliases; evaluation logs
50/50 top-1 and top-3 on the unreviewed mini-set; Ruff/Black pass; 345 total tests
pass (25 medication cases). The database appears at
`data/medications/medications.sqlite3`; reports/metrics regenerate from saved data.
No API key, GPU, patient data or model download is required.

Fetch/caching command:

```bash
make fetch-medications
```

Existing source bytes are verified/reused, without network access. For a new
capture use a new snapshot directory in a copied config, as documented in
data/medications/README.md. Raw files are never manually edited.

## Actual verification

Environment: CPython 3.11.17, uv 0.13.4, frozen dependencies.

```text
make medications
  Loaded 15883 specialties and 161618 aliases
  Top-1: 50/50; top-3: 50/50 (unreviewed mini-set)
make lint
  Ruff: All checks passed!
  Black: 27 files would be left unchanged.
make test
  collected 345 items
  345 passed, 1 warning in 35.39s
```

Tests cover required exact/misspelled/Arabic/Latin-numeric queries, strength
conflicts, equivalent mass units, distinct concentrations, compound strengths,
unknown input, invalid k/input sizes, synthetic-alias provenance, explicit
country/null unknowns, source encodings/tab shapes, page/archive/raw hash checks,
config bounds, empty catalogues, idempotent ingestion and complete reproduction
of the saved 50-query results/report. Existing API/schema/pharmacy tests pass.
No test contacts the upstream source. Pre-commit and staged whitespace checks
are run before the single feat(task4) commit. The existing upstream
Starlette/AnyIO deprecation warning remains unchanged.

## Acceptance checklist

- ✅ Asked which source file was available; user selected a public source.
- ✅ Public-source route proposed before ingestion; official open fallback and terms checked.
- ✅ N=15,883 real source specialties loaded, with explicit FR provenance.
- ✅ Required normalized fields exist, with missing Arabic labels/Moroccan prices kept null.
- ✅ Lowercase, accent, transliteration, Arabizi and typo variants generated/flagged.
- ✅ RapidFuzz and character TF-IDF MedicationIndex.search(query,k) returns scored candidates.
- ✅ Required exact/typo/Arabic/Arabizi-style numeric/strength-disambiguation tests pass.
- ✅ Fifty authored query strings, inspectable expected IDs and reproducible top-1/top-3 results.
- ⏳ User review of the 50 labels, Arabic spellings and source terms remains pending.
- ⚠️ Moroccan catalogue coverage is not delivered by this fallback; a suitable Moroccan source still needs ingestion later.

## Limitations and boundary

Source specialty names include withdrawn/non-marketed records, and statuses are
preserved. Brand_name is a derived lexical family; full_name remains the source
label. DCI stores SA substance names, not a new WHO-INN assertion. Laboratory
stores the source authorization holder, not an inferred manufacturer. Generated
Arabic spellings are approximate and unreviewed. High similarity does not prove
identity, availability or appropriateness. This reference layer does not answer
medical-advice requests; later pipeline refusal behavior is still required.

TASK 5 has not started. Continue only after VALIDATED TASK 4.

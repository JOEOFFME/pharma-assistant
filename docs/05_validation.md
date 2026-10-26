# Validation Report — TASK 5 correction

Scope: the requested dataset/schema correction only. TASK 6 has not started.
The old 100 candidates are development-only; no assistant-created gold exists.
This report supersedes the earlier candidate-review/promotion report.

## Files changed

| Files | Change |
| --- | --- |
| `data/nlu/dev_seed.jsonl` | Moved all 100 candidate texts unchanged; renamed IDs to dev_seed_001–100, source assistant_seed, verified false, split development_only. Corrected annotations and explicit relations. |
| `data/nlu/gold_human.jsonl` | New empty file, exactly 0 bytes. No gold rows generated. |
| `docs/examples/nlu_build_seed.jsonl` | Moved the existing 200 build seeds from data/nlu/seed.jsonl; updated metadata, span IDs, relations and boundaries. Keeps the build reproducible without duplicating generated texts under data/nlu/. |
| `data/nlu/generated/{train,dev,test}.jsonl` | Rebuilt with the new required annotation fields and corrected span conventions; no human verification claimed. |
| `src/pharma_assistant/api/schemas.py` | Relation and NLUAnnotation models; strict provenance/verification flags; endpoint/type/link checks, raw evidence and non-overlap validation. Public response adds relations and unsupported-clause flag. |
| `src/pharma_assistant/data_tools/nlu_dataset.py` | Uses new inputs, validates annotations, preserves family splits, checks leakage against development seeds and separately supplied human gold. No promotion operation. |
| `scripts/add_gold.py` | Human-operated helper using exact substrings and optional occurrence numbers to calculate Unicode offsets. Requires explicit --verified, validates full records and rejects duplicates/development copies. |
| `scripts/dataset_stats.py` | Prints per-file and combined intent/variety counts, distinct texts/medication surface forms, missing-medication counts and warnings below eight forms. |
| `scripts/export_schema.py`, `docs/response_v1.schema.json`, `docs/nlu_annotation.schema.json` | Reproducible response and JSONL contract exports. |
| `tests/test_nlu_dataset.py` | Recursive checks for every JSONL, cross-file duplicates, provenance guard, specified row regressions, negative cases, helper Unicode/duplicate behavior, deterministic generation and quality warnings. |
| `docs/02_nlu_spec.md`, `docs/examples/nlu_annotation_examples.{json,md}` | Updated mixed-request routing, clitics/generic pharmacy boundaries, complete time expressions, relations and illustrated DOSAGE/FORM/URGENCY/PHARMACY_NAME. Existing 200-example taxonomy coverage retained. |
| `docs/gold_annotation_howto.md`, `data/nlu/README.md`, `README.md` | Human-only collection instructions and permanent development-only status; no candidate-to-gold conversion. |
| `docs/nlu_stats.json`, `docs/nlu_quality.json`, `docs/data_nlu.md` | Actual regenerated statistics and coverage, without model evaluation claims. |
| `configs/nlu.yaml`, `Makefile`, `.gitignore`, `.gitattributes`, `.github/workflows/task5-dataset.yml` | Updated paths/tracking, removed gold-lock target, preserved annotation hashes, CI now checks schema/data rebuilds plus lint/tests on main. |
| Removed `data/nlu/gold_candidates.jsonl`, `data/nlu/gold_review.json`, `docs/gold_candidates_review.md`, `scripts/lock_gold.py`, `src/pharma_assistant/data_tools/gold_review.py` | Removed obsolete names and the assistant-candidate promotion path. |

## Requested row corrections

- 084, 088, 092, 096, 100: primary check_availability,
  contains_out_of_scope_request=true, expected action answers the in-scope part
  and refuses medical advice. No advice answers or stock claims were generated.
- 082, 083, 086, 087, 090, 091, 094, 095, 098, 099:
  needs_clarification=true; no fabricated medication entity.
- 081, 085, 089, 093, 097: two explicit QUANTITY_OF relations per row,
  targeting the corresponding medication span IDs.
- Generic pharmacy prefixes excluded from example name spans. TIME_REF now
  includes full `had lila` (043) and `هذه الليلة` (045), in addition to `ce soir`
  and `الليلة`. Original messages are preserved exactly.

## Actual quality counts

| JSONL file | Rows | Distinct texts | Distinct medication surface forms | Rows without MEDICATION |
| --- | ---: | ---: | ---: | ---: |
| dev_seed | 100 | 100 | 4 | 55 |
| generated/train | 520 | 520 | 31 | 70 |
| generated/dev | 50 | 50 | 6 | 20 |
| generated/test | 50 | 50 | 6 | 30 |
| gold_human | 0 | 0 | 0 | 0 |
| Union | 720 | 720 | 31 | 175 |

All eight intents and five varieties occur in development data. Combined counts:

- Intent: check_availability 145, request_medication 215, price_inquiry 185,
  pharmacy_info_phone 35, pharmacy_info_location 35, pharmacy_info_hours 35,
  greeting_smalltalk 35, out_of_scope 35.
- Variety: ar 138, darija_ar 138, darija_latn 138, fr 138, mixed 168.

Medication diversity counts normalize case/accents on **surface forms**; spelling
variants and Arabic/Latin aliases can inflate unique medication identities.
These are not counts of distinct active ingredients or clinically verified
products. The augmentation roster contains 12 source-backed catalogue entries.
Warnings below eight forms are printed for dev_seed, generated/dev,
generated/test and empty gold_human. The narrow development seed vocabulary is
reported honestly rather than padded with additional assistant messages.

## Commands run and actual output

From the repository root with Python 3.11.17 and frozen dependencies:

```bash
make install
make schema
make dataset
make lint
make test
git diff --check
```

Observed installation: `uv sync --frozen --python 3.11`, checked 42 packages.
Observed schema export: response and annotation schemas exported successfully.
Observed dataset build: train=520, dev=50, test=50, development-only seeds=100,
human gold=0. All shared-family, normalized-text and template-signature leakage
counts are zero. The script prints the counts above plus per-file warnings.

```text
uv run --frozen ruff check .
All checks passed!
uv run --frozen black --check .
31 files would be left unchanged.

uv run --frozen pytest
collected 369 items
369 passed, 1 warning in 35.22s
```

The warning is the existing Starlette/AnyIO BlockingPortal deprecation; it has
not been suppressed. A second `make dataset` reproduced all generated JSONL and
both statistics JSON files byte-for-byte (SHA-256 manifests compared using cmp).
A separate comparison with the previous commit confirmed all 100 original
candidate texts are unchanged and the human gold file is 0 bytes.
`git diff --check` passed after removing trailing blank lines.
These are local execution results; CI also runs the same core checks on push.

## Uncertain rows and limits

- dev_seed 022, 024, 026, 028, 030, 042, 044, 046, 048, 050 mention
  illustrative `المثال` / `Exemple`. There is no evidence of a registered real
  pharmacy name, so generic `صيدلية` / `Pharmacie` is excluded. No directory
  identity or existence is asserted. Review the wording if reusing it in development.
- dev_seed 061–070 are greetings/social expressions whose precise variety can
  depend on collection context. Their intended varieties remain unverified.
- All 100 development seeds, the 200 original build inputs and synthetic text
  still need native-speaker review. Passing structural tests does not establish
  linguistic correctness, medication identity or clinical truth.
- No automatic rule can prove human authorship, identify all semantic
  paraphrases, or establish that a generic word belongs to a real registered
  pharmacy name. Human annotation remains responsible for those judgments.
- The mixed-clause behavior is specified and structurally represented here;
  runtime extraction/response generation belongs to later tasks and is not
  implemented by this correction. No final evaluation metrics are claimed.
- The original TASK 5 requirement of ≥100 verified, locked gold rows remains
  unfulfilled. Per the user's correction, the human template is empty and no
  assistant development row can be promoted into it.

## Acceptance checklist

- ✅ 100 original texts moved to development-only assistant_seed rows, verified=false.
- ✅ Mixed routing, boundaries, full times, relations and missing-medication rules documented.
- ✅ DOSAGE, FORM, URGENCY and PHARMACY_NAME illustrated; models/schema exports updated.
- ✅ Every JSONL recursively checked for spans, non-overlap, enums and clarification.
- ✅ Exact duplicate texts rejected within and across files.
- ✅ All specifically identified row groups covered by regression tests.
- ✅ Empty gold_human template and human annotation helper/guide; non-human gold rejected.
- ✅ Required quality counts and low-diversity warnings printed.
- ✅ Lint, tests, leakage and byte-reproducibility checks passed.
- ✅ No next task started.
- ❌ Human gold collection/locking (intentionally pending; no rows invented).

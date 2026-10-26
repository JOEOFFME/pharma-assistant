# Validation Report — draft annotation proposals (TASK 5)

Implemented only the requested draft-import/review aid. No TASK 6 pipeline or
baseline evaluation has been started. These proposals are not verified gold.

## Files created or changed

| File | Purpose |
| --- | --- |
| `scripts/import_gold_draft.py` | Batch importer, full printed review table, protected gold/input paths, explicit overwrite guard and read-only --print-existing mode. |
| `configs/gold_draft.yaml` | Relative paths, label-typo alias and draft-specific mention/form/package/time/urgency lexicons. No catalogue identity claims. |
| `data/nlu/gold_human_draft.txt` | Byte-identical copy of the supplied attachment; all original messages retained. |
| `data/nlu/gold_review.jsonl` | 84 proposed annotations with source=assistant_seed, verified=false, split=review_only, original notes/labels and explicit warnings/duplicate references. |
| `docs/gold_draft_review.md` | Full table of every row, source line, original message, proposed spans/offsets/values/units, relations and clarification flags. |
| `docs/gold_draft_import.md` | Reproduction/correction instructions, annotation conventions, provenance and review-queue limitations. |
| `src/pharma_assistant/api/schemas.py` | Typed draft metadata; draft proposals cannot be marked verified, human or admitted to a non-review split. |
| `docs/nlu_annotation.schema.json` | Regenerated annotation contract with draft metadata. |
| `tests/test_import_gold_draft.py` | Per-row offsets/schema, original-text preservation, notes/relations, all entity types, Unicode/repeated mentions, malformed input, CLI table, read-only correction viewing and gold protection (including symlinks/hardlinks). |
| `tests/test_nlu_dataset.py` | Existing recursive checks now also cover review output. Accepted data remains globally unique; preserved review-only duplicates require exact references to real accepted records. Duplicates within review output still fail. |
| `docs/nlu_quality.json` | Updated raw inventory counts, including the separately listed review queue; not a train/evaluation admission. |
| `.gitignore`, `README.md`, `data/nlu/README.md`, `docs/02_nlu_spec.md` | Track supplied source/review output and document the review-only exception and correction workflow. |
| `docs/05_gold_draft_validation.md` | This report. |

`gold_human.jsonl` was not written or modified. Existing train/dev/test files are
unchanged. No rows were generated as human data, and no evaluation was run.

## Reproduction and observed output

From the repository root with frozen dependencies and Python 3.11.17:

```bash
# First import only; existing review output is protected by default.
uv run --frozen python scripts/import_gold_draft.py

# View/validate the committed or manually corrected proposals without writing files.
uv run --frozen python scripts/import_gold_draft.py --print-existing

# Explicitly discard prior proposals/corrections and regenerate, when intended.
uv run --frozen python scripts/import_gold_draft.py --overwrite

uv run --frozen pytest tests/test_import_gold_draft.py tests/test_nlu_dataset.py -q
make schema
make dataset
make lint
make test
git diff --check
```

The importer was run to create output, then explicitly regenerated to verify the
updated table rendering. It printed all 84 rows, followed by:

```text
Proposed 84 rows; all verified=false. gold_human.jsonl untouched.
Review JSONL SHA-256: 1275b5ccd5d83fe638994d056cfc8e348e6b22d840e9e8b98fcdaff165a51ab3
```

Actual focused test result:

```text
119 passed in 1.74s
```

Actual full check results:

```text
uv run --frozen ruff check .
All checks passed!
uv run --frozen black --check .
33 files would be left unchanged.

uv run --frozen pytest
464 passed, 1 warning in 33.05s
```

The warning is the pre-existing Starlette/AnyIO BlockingPortal deprecation.
It has not been hidden or suppressed. `git diff --check` passed.

## Output counts and integrity

| Proposed entity / relation | Count |
| --- | ---: |
| MEDICATION | 56 |
| DOSAGE | 29 |
| FORM | 4 |
| QUANTITY | 12 |
| PHARMACY_NAME | 8 |
| LOCATION | 16 |
| TIME_REF | 9 |
| URGENCY | 5 |
| DOSAGE_OF | 29 |
| QUANTITY_OF | 12 |

84 proposals, all eight entity types represented, 28 needing clarification,
three mixed in-scope/advice requests. Every entity selects exactly
`text[start:end]`, with no overlapping spans and valid mention links.
The helper recomputes offsets on original Unicode text; it does not normalize
or rewrite the message. Tests additionally cover emoji, accented text, Arabic,
repeated medications, apostrophe clitics, extra pipe characters and whitespace.

SHA-256 of both the supplied attachment and tracked draft:
`7617fd99da8fdc91b465c0b7c751984ad77eb06b7fcdd196778681e56ebb886b`.
The gold file is still 0 bytes, SHA-256
`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
Temporary test fixtures exercise writing proposals; no tests add production gold.

The inventory now has 804 records and 802 distinct texts because the raw review
queue preserves two explicitly flagged development duplicates. The accepted
train/dev/test and dev_seed datasets still have 720 unique texts. Review records
are not inputs to the dataset builder, training, tuning or final evaluation.

## Rows needing particular correction/review

- 013 / source line 20: `price_inquiy` proposes `price_inquiry`; the original
  label and text are retained. `protex` is an unresolved product/name proposal,
  with no verified catalogue identity or medication fact asserted.
- 026 / source line 33: `preservative` is unclear/generic; no MEDICATION name
  was invented. Clarification is proposed. Review intent/product scope yourself.
- 063 / source line 70: the message labelled greeting asks where to find
  `Amoxline`. Availability is proposed and flagged; spelling/product identity
  and routing need your correction.
- Unitless strengths (e.g. `1000`, `500`, `50`, `75`, `850`, `100`, `400`)
  remain unnormalized and trigger clarification for supported intents. No mg or
  regimen is inferred. Explicit `1g`, `1غ`, `1 غ`, `500 mg` retain their stated unit.
- 009, 010 and 051 contain bare counts without a stated package word; unit is
  `unit`, never an inferred bottle/box. The quantity/form spans in `1 sirop`
  do not overlap. Review these choices in context.
- 076 / source line 84: notes mention FORM, but `2 boîtes` is packaging. No
  physical form was fabricated, and the unsupported note is flagged.
- 046 / source line 53 (`السلام عليكم`) exactly matches
  `generated/dev.jsonl:greeting_smalltalk.darija_ar.01`.
- 071 / source line 78 (`شكرا لكم`) exactly matches
  `generated/train.jsonl:greeting_smalltalk.ar.03`.
  Both messages remain in the requested review output unchanged, with duplicate
  references. Only the review queue may retain such flagged duplicates; neither
  is eligible for human gold.

The draft header itself says assistant-written, NOT verified. All rows retain
that provenance. Names, intended varieties, naturalness and unknown phrases
need human correction. The lexicon is specific to this supplied draft and is
not a general-purpose NLU model or catalogue resolver. Exact structural tests
cannot establish human authorship, pharmacy existence or medication truth.

## Acceptance checklist

- ✅ Import every non-comment message; preserve the source text exactly.
- ✅ Propose all eight entity types, relations and clarification from notes/evidence.
- ✅ Preserve original labels/notes; flag typo correction, ambiguous evidence and duplicates.
- ✅ Write only unverified review proposals and a full per-row review table.
- ✅ Gold file unchanged; direct, symlink and hardlink writes to it rejected.
- ✅ Every output row passed exact span, non-overlap, enum, relation and clarification tests.
- ✅ Existing accepted-data uniqueness remains enforced; queue duplicates explicitly quarantined.
- ✅ Lint and full tests pass; no new dependencies or evaluation numbers.
- ✅ No next task started.
- ❌ Human correction/independent final gold collection remains pending.

# TASK 2 - Validation Report

Date: 2026-10-26. TASK 1 was validated before this work.
Status: **ready for user review; specification approval pending**.

## Built

- Final proposed taxonomy: eight canonical intents, with request_medication as
  the single request/order wire label, plus an explicit primary-intent priority.
- Eight tagged entity types with raw evidence spans, assertion status, typed
  strength/count/form attributes and optional medication mention associations.
- Pydantic v2 response models with strict numeric constraints and cross-field
  checks for clarification, pharmacy queries, evidence and entity references.
- Deterministic JSON Schema export and 10 illustrative response payloads.
- Annotation guidelines covering language assignment, boundaries, multi-medication
  requests, negation, missing quantities, ambiguous strengths and unsafe requests.
- 200 authored annotation examples: exactly five per intent per language variety
  (8 intents x 5 varieties x 5 examples), with exact spans and explicit provenance.

## Files created/changed

| File | Action | Purpose |
| --- | --- | --- |
| src/pharma_assistant/api/schemas.py | Created | Response, input, intent, entity, query and clarification models. |
| scripts/export_schema.py | Created | Portable deterministic JSON Schema export CLI. |
| docs/02_nlu_spec.md | Created | Taxonomy, field contracts, annotation and edge-case guidelines. |
| docs/response_v1.schema.json | Created | Generated response JSON Schema. |
| docs/examples/response_v1_samples.json | Created | Ten schema-only fixtures covering five varieties and voice. |
| docs/examples/nlu_annotation_examples.json | Created | Canonical authored annotations, pending human review. |
| docs/examples/nlu_annotation_examples.md | Created | Readable table of all 200 examples. |
| tests/test_schemas.py | Created | Valid/invalid payload, export and annotation checks. |
| Makefile | Updated | Added make schema target. |
| README.md | Updated | Linked TASK 2 artifacts and export/test commands. |
| docs/02_validation.md | Created | This validation report and review gate. |

No inference endpoint, dataset training split, source database, speech recognizer
or learned model was implemented. Dependencies and lockfile are unchanged.

## Exact commands

From the repository root, after cloning/pulling main:

```bash
make install
make schema
make lint
make test
uv run --frozen pytest tests/test_schemas.py -v
uv run --frozen pre-commit run --all-files
git diff --check
```

Alternative export destination:

```bash
uv run --frozen python scripts/export_schema.py --output docs/response_v1.schema.json
```

Expected: schema export logs its destination; Ruff/Black pass; all 280 tests pass;
the targeted test file passes 275 cases; pre-commit passes; git diff --check
reports no errors. Open docs/02_nlu_spec.md and its linked examples for review.
The export/schema tests need no API keys, model downloads or dataset downloads.

## Actual results

Environment: CPython 3.11.17, uv 0.13.4, unchanged frozen dependencies.

```text
make schema
  INFO:__main__:Exported response schema to docs/response_v1.schema.json
make lint
  Ruff: All checks passed!
  Black: 15 files would be left unchanged.
make test
  collected 280 items
  tests/test_health.py ...
  tests/test_schemas.py ...
  tests/test_study_references.py ..
  280 passed, 1 warning in 1.65s
```

The schema test file includes 200 independently checked annotation records,
10 response fixtures, and positive/negative tests for confidence/count/strength
bounds, unknown fields/labels, disclaimer, modality, Unicode/emoji offsets,
repeated mentions, catalogue-field shape, mention links, clarification,
pharmacy-query consistency, negation and ambiguous evidence on refusal routes.
The CLI is exercised from a temporary working directory and its output compared
to the live model and checked-in schema. Coverage/provenance checks verify the
full 8x5x5 matrix. These are software correctness checks, not NLU performance.

Pre-commit Ruff/Black and staged whitespace checks are run before committing.
One logical commit: feat(task2): define NLU schema and annotation guidelines.

## Acceptance checklist

- ✅ docs/02_nlu_spec.md defines canonical intents, entities and annotation rules.
- ✅ At least five examples per intent in Darija-Arabic, Darija-Latin, MSA,
  French and code-mixed input: 200 authored examples, pending native review.
- ✅ Edge cases include multiple meds, negation, missing quantity and ambiguous
  product strength, with clarification and association rules.
- ✅ Pydantic v2 implements the response contract and rejects invalid shapes.
- ✅ JSON Schema is exportable and matches the checked-in artifact.
- ✅ Sample payloads validate and serialize; 280 tests pass overall.
- ⏳ Specification reviewed by the user: **pending VALIDATED TASK 2**.

## Limitations and decisions to review

- The examples and intended language labels are authored, unreviewed specification
  examples, not a hand-verified gold set or real patient data. No inference
  accuracy, F1, WER or model latency is claimed.
- JSON Schema expresses types, enums and field bounds; Pydantic additionally
  enforces cross-field rules that generic JSON Schema consumers will not get.
- Catalogue IDs/ingredients are structurally constrained but not fact-checked:
  the later matcher must validate them against the approved source database.
- A valid schema cannot detect unsafe prose or incorrect intent labels. Later
  pipeline refusal tests and safe response templates remain required.
- The public schema keeps the original response keys and adds optional offsets,
  assertion status, entity_id and medication_ref. Review these refinements and
  the single-primary-intent policy before data collection.
- Product strengths are extracted verbatim; compound/ambiguous strengths remain
  raw and require clarification for supported requests. No dose advice is added.
- The unchanged upstream Starlette/AnyIO deprecation warning remains documented.

TASK 3 has not started. Continue only after VALIDATED TASK 2.

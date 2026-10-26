# Adding human gold annotations

`data/nlu/gold_human.jsonl` starts empty. No assistant-generated evaluation rows
have been added. Write/collect new messages yourself and check every annotation.
Do not copy or paraphrase development seeds, training rows or specification
examples into the final evaluation set. In particular, `dev_seed.jsonl` is
permanently development-only, even after corrections or review.

Keep gold separate from model development, prompting, tuning and threshold
selection. Do not inspect model predictions while annotating. Aim for at least
100 independently collected rows across all eight intents and five varieties;
record disagreements and adjudicate them with another speaker before final use.
The gold set is not yet complete or locked. Counts and evaluations must say so.

## JSONL format

One complete JSON object per UTF-8 line, no enclosing array. Required fields:
`id`, `text`, `language`, `intent`, `entities`, `relations`,
`needs_clarification`, `contains_out_of_scope_request`, `source`, `verified`,
`family_id`, `split`. For gold use `source="human"`, `verified=true`,
`split="gold_human"`. A boolean declaration records your annotation; it cannot
prove who authored the text. Never relabel assistant output as human.

Each entity has `entity_id`, `type`, `text`, `start`, `end`, plus type-specific
fields from [the specification](02_nlu_spec.md). Offsets are zero-based Python
Unicode code points, end excluded. No overlaps. Use the exact original substring;
exclude clitics and generic pharmacy words. Include complete time phrases.
QUANTITY requires positive integer `value` and `unit`; DOSAGE product strength
uses `value` and `unit` together, or both absent if ambiguous. Add `QUANTITY_OF`
and `DOSAGE_OF` relations with `from` / `to` span IDs when association is known.
For ambiguous strength or association, set clarification true. Never add medical
advice, inferred ingredients, stock or prices.

## Minimal helper

After `make install`, use `uv run --frozen python scripts/add_gold.py --help`.
Supply your own message via `--text`, one of `darija_ar`, `darija_latn`, `ar`,
`fr`, `mixed` via `--language`, and a canonical `--intent`. Repeat `--span` with
JSON describing each exact substring and its `entity_id` / `type`; repeat
`--relation` with JSON links. Add `--verified` only after checking the result.
The helper supplies source/verification metadata and calculates offsets; it does
not generate messages, infer entities, classify intent or recommend treatment.

Example **syntax only** (replace all angle-bracket placeholders yourself;
this is not a runnable gold example):

```bash
uv run --frozen python scripts/add_gold.py \
  --text '<your independently collected message>' \
  --language fr --intent request_medication \
  --span '{"entity_id":"m1","type":"MEDICATION","text":"<exact medication substring>"}' \
  --span '{"entity_id":"q1","type":"QUANTITY","text":"<exact quantity substring>","value":2,"unit":"box"}' \
  --relation '{"type":"QUANTITY_OF","from":"q1","to":"m1"}' \
  --verified
```

For repeated substrings add `"occurrence":2` (1-based) to select the second
occurrence; ambiguous occurrences are refused. Give every span a unique ID.
For missing medication, the helper automatically sets clarification true for
availability/request/price intents. Use `--needs-clarification` for other missing
context or ambiguous evidence. Use `--contains-out-of-scope-request` when needed;
retain the in-scope primary intent and refuse only the unsupported clause.

The helper rejects invalid labels, mismatched spans, overlap, dangling relations,
exact duplicates and exact copies from current development data. It cannot detect
semantic paraphrases or prove independent collection: that remains your review
responsibility. It appends one validated record to the gold file only when you
run it. Review your git diff after each annotation session.

Run `make dataset && make lint && make test` after editing. Tests visit every
JSONL under `data/nlu/`, including future nested files; they reject non-human gold
and duplicate texts across files. Empty gold is valid during preparation, but
cannot support final evaluation. Final sealing/versioning will happen after your
independent gold collection; the old assistant-candidate promotion path is removed.

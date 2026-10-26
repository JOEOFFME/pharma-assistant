# Draft span proposals for human correction

The supplied `data/nlu/gold_human_draft.txt` is copied byte-for-byte from the
attached draft. Its header identifies the messages as assistant-written and
unverified. These are **not human gold**. No message text was corrected,
normalized, deduplicated, translated or replaced.

Run from the repository root after `make install`:

```bash
uv run --frozen python scripts/import_gold_draft.py
```

The first run writes `data/nlu/gold_review.jsonl` and
[the complete review table](gold_draft_review.md), and prints the table for
**every row**. Each row is `source="assistant_seed"`, `verified=false`,
`split="review_only"`, `review_status="pending_human_correction"`.
`draft` metadata retains the source line, supplied intent and notes, plus
proposal warnings and exact duplicate references. No catalogue identity,
active ingredient, availability, price or medical recommendation is inferred.

The config file `configs/gold_draft.yaml` holds relative paths and a small
lexicon of **mention spellings in this draft**. These are extraction hints, not
verified catalogue entries. This is a batch annotation aid for TASK 5; no API,
text pipeline or TASK 6 baseline has been implemented.

## Correcting the proposals

Open `gold_review.jsonl` and correct entity types, substrings, numeric fields,
relations, intent and clarification flags. Keep source messages unchanged and
all rows unverified. `entity_id` is a span ID; `medication_ref` and relation
`from` / `to` fields point to these IDs. The table shows exact `[start:end]`
Unicode code-point offsets plus proposed values, units, normalizations and links.

To validate and print the existing (possibly corrected) JSONL without rewriting it:

```bash
uv run --frozen python scripts/import_gold_draft.py --print-existing
```

The importer refuses to overwrite an existing JSONL or report by default.
`--overwrite` explicitly discards existing proposals/corrections and rebuilds
both outputs. Use it only when that is intended. It cannot target
`gold_human.jsonl`, including through a symlink. Draft/schema errors are
validated before either proposal/report is written. There is no gold promotion
or verification operation.

## Text and annotation conventions

Each non-comment source line is `variety | proposed_intent | notes | text`.
Only one ASCII padding space immediately after the third separator is consumed
as format syntax. Every subsequent character belongs to the message, including
additional leading/trailing spaces, accents, Arabic characters, apostrophes,
misspellings and extra `|` characters. CRLF/LF terminates records and is not part
of a message. The original file itself is unchanged.

- Notes are hints, not evidence. No span is generated unless it is present in
  the original text. A missing note does not hide explicit time/form/strength.
- `needs_clarification` is set from its note and also when required by the spec:
  unnamed medication, unitless strength, unresolved attribute association or
  missing directory target. Unknown note tags are flagged for review.
- Unitless strength remains raw with no numeric/unit normalization; no mg is
  inferred. `1g` / `1غ` / `1 غ` mean explicitly stated product strength only.
- Bare counts retain `unit="unit"`; package words are not borrowed from another
  medication. `1 sirop` becomes non-overlapping quantity `1` and form `sirop`.
- `boîtes` is packaging, not a physical FORM. Generic `Pharmacie` / `صيدلية`
  and attached clitics are excluded from proper-name spans. `ce soir` and
  `had lila` are complete TIME_REF spans.
- Mixed in-scope/advice messages retain the supported intent and set the
  unsupported-request flag. Medical mentions in the advice clause are evidence
  only, not additional purchase/stock requests.
- The known label typo `price_inquiy` proposes `price_inquiry` while retaining
  the original label in metadata. The greeting followed by a medication-finding
  request proposes availability and flags that choice for review. No text edit.

## Review queue versus datasets

There are 84 messages, all kept in order. Rows 046 (`السلام عليكم`) and 071
(`شكرا لكم`) exactly duplicate existing development texts. They are **flagged**,
not silently dropped or altered. To preserve every source line as requested,
only this unverified review queue is permitted to reference such duplicates.
Accepted data remains globally unique; duplicate references in review rows must
match actual existing rows exactly. Duplicates within the queue still fail.
All span/schema/non-overlap/clarification tests still cover the queue.

The dataset builder never reads the review queue into train/dev/test or gold.
The statistics inventory lists it separately and reports raw total versus
distinct text counts; inclusion in that inventory is not admission for training
or final evaluation. Human gold remains empty and unchanged. None of this
assistant-authored draft is eligible for the human-only final evaluation set.

Validation:

```bash
uv run --frozen pytest tests/test_import_gold_draft.py tests/test_nlu_dataset.py -q
make schema
make dataset
make lint
make test
```

The printed table and JSONL are proposals; structural validation does not prove
linguistic correctness or that a name is a medication or registered pharmacy.
Review unclear names, intent corrections, unitless strengths and all flagged
notes manually. The lexicon will miss unfamiliar names/phrases in future drafts;
update it or annotate those spans manually, without inventing medical facts.

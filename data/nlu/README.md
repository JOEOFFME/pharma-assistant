# NLU annotations — development and human evaluation

- `dev_seed.jsonl`: 100 assistant-authored development-only messages,
  `source=assistant_seed`, `verified=false`. Never final evaluation data.
- `generated/train.jsonl`: family-grouped seed examples and synthetic variants.
- `generated/dev.jsonl`, `generated/test.jsonl`: unverified development splits;
  the filename `test` does not make this a final human evaluation set.
- `gold_human_draft.txt`, `gold_review.jsonl`: supplied assistant-written draft
  and unverified review proposals. Never train/evaluation inputs. See
  [import and correction guide](../../docs/gold_draft_import.md).
- `gold_human.jsonl`: empty human-only final evaluation template. No assistant
  may generate its rows or promote development examples into it.
- `medication_roster.json`: 12 source-backed French BDPM reference entries for
  augmentation, without Moroccan stock/price claims.

The 200 assistant-authored build inputs now live in
`docs/examples/nlu_build_seed.jsonl`. Generated splits partition those inputs;
keeping build inputs outside this directory avoids duplicate storage of texts
inside the recursively checked annotation dataset. All JSONL rows include exact
Unicode spans, explicit span IDs, relations, clarification and unsupported-clause
flags, creation provenance and verification booleans. See the
[specification](../../docs/02_nlu_spec.md).

Run `make dataset` for deterministic seed-42 family splits, training-only
augmentation, leakage checks and statistics. `scripts/dataset_stats.py` prints
rows per intent/variety, distinct texts/medication surface forms, missing-medication
counts and warnings below eight medication forms. Surface diversity is not a
claim about unique resolved catalogue identities; aliases and spelling variants
can inflate the count. The roster itself contains 12 distinct catalogue IDs.
Reports: `docs/nlu_stats.json`, `docs/nlu_quality.json`, `docs/data_nlu.md`.

Every JSONL under this directory is tested for schema validity, raw span equality,
non-overlap, recognized intents/varieties, required clarification and exact-text
duplicates within and across accepted files. The review queue retains all source
messages and explicitly flags any duplicate of accepted data; this exception is
restricted to unverified review-only rows. Leakage checks additionally reject shared
families, normalized texts and delexicalized signatures across generated splits
and development seeds. Semantic paraphrase leakage still requires human review.

Follow [human gold instructions](../../docs/gold_annotation_howto.md) to add your
own independently collected and checked messages. `scripts/add_gold.py` derives
span offsets from substrings you supply. It requires explicit verification and
refuses exact copies of development data. There is no candidate promotion or
`make gold-lock` command. Baseline/development measurements now appear in
[the evaluation report](../../docs/10_evaluation.md), with provisional entity
reference status explicitly stated. The original TASK 5 requirement of at least
100 verified locked gold
rows remains unfulfilled until you provide that separate human set.

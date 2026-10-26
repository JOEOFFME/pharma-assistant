# NLU data - TASK 5 preparation

The 200 hand-style seed examples are assistant-authored, reused from the TASK 2
specification, and remain `source=authored_unreviewed`. They are not collected
patient data. The 100 held-out candidates are separately authored and likewise
unreviewed. No build command may claim that a human verified either set.

## Rebuild

After `make install`, run `make dataset` from the repository root.
It creates `data/nlu/generated/{train,dev,test}.jsonl`,
`docs/nlu_stats.json` and `docs/data_nlu.md`. Generated splits are versioned for inspection alongside recipes, inputs and the
medication roster. Rebuilding must reproduce their committed hashes.

Each JSONL record contains id, raw text, intent, variety, entity spans, source,
review status, template family and split. Synthetic records also identify their
parent and augmentation settings. Offsets count original Unicode code points.
All records are checked against the TASK 2 entity/response contract.

Configuration: `configs/nlu.yaml`, fixed seed 42. No stochastic sampling, hosted
LLM calls, model downloads or additional libraries are needed. Optional
provider-assisted paraphrasing is not enabled. No rows with a fabricated human
review status are created.

## Family split and augmentation

Translations with the same TASK 2 example position start in one family.
Before assignment, families with matching delexicalized signatures are joined.
The signature masks medication/location/name mentions and removes optional
quantity, strength, form, time and urgency attributes. Groups are assigned
deterministically per intent, reserving one complete group each for development
and test; remaining groups go to training.

Only training seeds are augmented. A 12-item roster is derived from source-backed
candidates saved in TASK 4, selected across available families with simple,
explicit strength fragments. Its IDs, full source labels and specialty-file hash
are recorded. It is a subset of the French BDPM fallback, not a Moroccan market
list. Generated requests do not assert stock, prices or therapeutic suitability.

Augmentation replaces annotated medication, strength and quantity spans, recomputes
offsets, and introduces flagged Arabizi/typo variants. Original script/style and
code-mixed phrasing are inherited from the seed. Arabic transliterations and
quantity grammar need native-speaker review. No ingredient facts are generated.

Checks reject shared family IDs, normalized text or simple delexicalized
signatures between train/dev/test and held-out candidates. Exact normalized
duplicates are removed within each split. These checks cannot prove absence of
all semantic paraphrase leakage; review remains necessary. Synthetic class
imbalance is reported rather than described as representative patient behavior.

## Human review and gold admission

1. Read [the review table](../../docs/gold_candidates_review.md) alongside
   `gold_candidates.jsonl` and the TASK 2 specification. Review variety, intent,
   spans, mention relations, negation and clarification needs for every row.
2. Correct annotations if necessary. Each changed record needs a fresh SHA256
   computed with `nlu_dataset.digest`; do not reuse an old approval hash.
3. In `gold_review.json`, populate each row's reviewer identity and explicit
   timezone-aware ISO review timestamp, and set approved=true only after review.
   The prefilled hash binds the complete original annotation.
4. Run `make gold-lock`. It rejects incomplete, stale or blank reviews.
   It produces `gold_test.jsonl` and `gold.lock.json` only after all 100 approvals.
   Run `make dataset` again to refresh the verified-gold count and consistency checks.
5. Keep locked gold separate from training/tuning; use
   `load_locked_gold` to verify its hash before evaluation. Changing a locked
   file fails verification. Revisions need a new versioned destination and review.

The metadata is an audit declaration, not cryptographic proof of human identity.
Unit tests use explicitly simulated approvals only in temporary directories.
They never approve production candidates. Neither this build nor a successful
test run substitutes for the required human verification.

Current status: **100 candidates, zero verified production gold records**.
TASK 5's human-verified/locked-gold acceptance criterion remains pending.

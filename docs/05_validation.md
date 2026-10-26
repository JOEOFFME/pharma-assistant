# TASK 5 - Validation Report

Date: 2026-10-26. TASK 4 was validated before this work.
**Software/data preparation verified; human-verified gold acceptance pending.**

## Built and files

| File/group | Purpose |
| --- | --- |
| configs/nlu.yaml | Fixed seed 42, input/output paths and augmentation settings. |
| data/nlu/seed.jsonl | 200 assistant-authored hand-style seed examples, reused from the TASK 2 specification with provenance. |
| data/nlu/medication_roster.json | 12 source-backed French BDPM records with explicit strengths and original specialty-file hash. |
| data/nlu/generated/{train,dev,test}.jsonl | Reproducible, annotated, family-disjoint splits, versioned for inspection. |
| data/nlu/gold_candidates.jsonl | 100 separately authored held-out candidates, pending human review. |
| data/nlu/gold_review.json | Per-record annotation hashes; every approval initially false and reviewer/timestamp null. |
| data/nlu/README.md | Build, split, augmentation, provenance, review and lock instructions. |
| src/pharma_assistant/data_tools/nlu_dataset.py | Annotation validation, family grouping, training-only augmentation, leakage checks and statistics. |
| src/pharma_assistant/data_tools/gold_review.py | Review-bound admission, immutable lock and hash verification. |
| scripts/dataset_stats.py, scripts/lock_gold.py | Reproducible dataset/report and reviewed-gold entry points. |
| tests/test_nlu_dataset.py | Twelve added cases for preparation, provenance, leakage and review controls. |
| docs/gold_candidates_review.md | Readable table of all 100 candidate messages, intents, varieties and spans. |
| docs/nlu_stats.json, docs/data_nlu.md | Actual split/class/language/source/length counts, hashes and limitations. |
| Makefile, README.md, .gitignore, .gitattributes | Commands, artifact tracking and byte-preserving JSONL attributes. |
| .github/workflows/task5-dataset.yml | Isolated TASK 5 verification because no local execution environment was available. |

No dependencies changed. Optional provider-assisted paraphrasing is disabled.
No patient data, stock/price facts or human review was fabricated.
Source flags retain assistant-authored versus programmatically synthetic origin.

## Actual dataset

| Split | Authored seed rows | Synthetic rows | Total | Template families |
| --- | ---: | ---: | ---: | ---: |
| train | 100 | 420 | 520 | 18 |
| dev | 50 | 0 | 50 | 8 |
| test | 50 | 0 | 50 | 8 |
| gold candidates | 100 | 0 | 100 | held out, unreviewed |

All eight intents and five varieties occur in every training/development/test
split. Gold candidates contain 20 messages per variety, covering all eight
intents. The training set is intentionally not described as representative:
augmentation increases medication-related classes; the stats report exposes
that imbalance. Gold candidates are excluded from training and tuning.

Translations initially share a semantic/example-position family. Exact
delexicalized collisions are grouped before deterministic per-intent splitting.
Synthetic descendants stay only in their training parent's family. Leakage
checks passed for family IDs, normalized text and simple template signatures,
including held-out candidates. These checks do not prove semantic independence.

## Exact commands and expected output

From the repository root after installing prerequisites:

```bash
make install
make dataset
make lint
make test
```

Expected: 520 train / 50 dev / 50 test records, counts/lengths and split hashes
regenerated; Ruff/Black pass; 357 total pytest cases pass. Dataset preparation
needs no API key, model download or source-network request.

```bash
make gold-lock
```

Expected **failure** with "Human review missing" until all 100 annotations have
genuine, hash-bound review. Neither production gold file should be created yet.
After actual review, the same command seals gold_test.jsonl and gold.lock.json;
load_locked_gold rejects changed or unreviewed files. Existing locks are not
overwritten. Review metadata is an audit declaration, not proof of identity.

## Actual software verification

Verified on GitHub Actions with CPython 3.11.17, uv 0.13.4 and frozen dependencies.
A passing preparation run reported:

```text
make dataset
  Built NLU splits: {'train': 520, 'dev': 50, 'test': 50}
  Gold remains pending human review: 100 candidates
make lint
  Ruff: All checks passed!
  Black: 32 files would be left unchanged.
make test
  357 passed, 1 warning in 30.70s
git diff --exit-code
  passed
```

Evidence: [passing preparation run](https://github.com/JOEOFFME/pharma-assistant/actions/runs/40399128088).
The final branch also runs the read-only workflow, including an explicit check
that the pending-review lock command fails and creates no gold files, before
main is updated. No local test run is claimed. The pre-existing upstream
Starlette/AnyIO deprecation warning remains unchanged.

Tests check coverage, annotation/offset validity, input hashes, deterministic
rebuilds, training-only descendants, family/text leakage, Unicode offsets,
stale/pending review rejection, lock integrity and no-overwrite behavior.
Simulated approvals are confined to pytest temporary directories and do not
approve any production candidate.

## Acceptance checklist

- ✅ At least 150 hand-style seeds: 200 covering all intents and varieties.
- ✅ Template/medication/quantity/script/noise augmentation, flagged synthetic.
- ✅ Deterministic family-based train/dev/test splits with provenance.
- ✅ Statistics report and machine-checkable leakage checks pass.
- ✅ At least 100 held-out candidates and a documented review/lock process.
- ❌ Human-verified production gold set: **0 verified / 100 required**.
- ❌ Production gold lock: intentionally not created before review.

AGENTS.md explicitly requires a "gold test set (≥ 100) that is hand-verified".
A successful software test run cannot satisfy that human-review requirement.
The [review table](gold_candidates_review.md), annotations and review template
are ready; native-speaker correction and per-record approvals are the remaining
input. TASK 5 cannot be declared fully complete until that condition is met.
TASK 6 has not started.

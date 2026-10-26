# TASK 1 - Validation Report

Date: 2026-10-26. TASK 0 was validated by the user before this work.

## Built

A focused problem study and related-work review for Challenge 1. The study covers
scope, multilingual/script variation, Arabizi numerals, medication transliteration,
short/noisy speech, uncertainty, comparison of approaches, justified proposed
choices, evaluation design and a manual resource-verification queue.

There are 13 related-work entries, including papers and implementation/terminology
resources, with 14 reference definitions (AraBERT has a separate maintainer link).
DODa's two publications are explicitly identified as one evolving resource family.
Nine entries are research publications (R01-R09); R10-R12 are implementation or
terminology resources and R13 is a published review. These categories are not
independent replications or project evaluation results.

## Files created or changed

| File | Action | Purpose |
| --- | --- | --- |
| docs/01_problem_study.md | Created | Main TASK 1 deliverable and linked bibliography. |
| docs/01_validation.md | Created | This report, commands, evidence and limitations. |
| tests/test_study_references.py | Created | Two offline citation-integrity pytest checks. |
| README.md | Updated | Current scope and links to study/report. |

No runtime API behavior, dependency versions, datasets or models changed.

## Exact commands to run

From the repository root after cloning or pulling main:

```bash
make install
make lint
make test
uv run --frozen pytest tests/test_study_references.py -v
git diff --check
```

Expected: frozen installation succeeds; Ruff and Black pass; all 5 tests pass;
the targeted command passes 2 tests; git diff --check emits no errors.
Read docs/01_problem_study.md on GitHub or in a Markdown reader. No model download,
API key or network access is needed to run the tests after dependencies install.

## Actual verification

Executed on CPython 3.11.17 with uv 0.13.4 and the unchanged frozen dependencies:

```text
make lint
  Ruff: All checks passed!
  Black: 12 files would be left unchanged.
make test
  collected 5 items
  tests/test_health.py ... [60%]
  tests/test_study_references.py .. [100%]
  5 passed, 1 warning in 0.39s
git diff --check
  exit status 0, no output
```

The existing warning concerns the deprecated AnyIO BlockingPortal alias used by
Starlette's TestClient; it is not suppressed. Pre-commit Ruff/Black checks are
also run on the staged files before committing.

Sources were checked through publication/author pages (arXiv, ACL Anthology,
PMLR, Cambridge and JAMIA) and maintainer/official documentation (AraBERT,
CAMeLBERT, faster-whisper, RapidFuzz and NLM). Bibliography entries record which
parts were consulted. Identity and the broad contribution used in the review
were checked; R05 explicitly leaves full-text transfer suitability unverified.
Uncertain access, licensing, exact checkpoint and dataset suitability are marked
[TO VERIFY]. No source scores were copied as project metrics.

## Acceptance checklist

- ✅ docs/01_problem_study.md exists with the required problem statement.
- ✅ Discusses code-switching, Darija orthography, Arabizi numerals,
  transliteration and noisy/short voice input.
- ✅ At least 8 related-work items: 13 documented entries.
- ✅ Covers Darija resources, intent/NER, speech, matching and health chatbots.
- ✅ Candidate comparison table with limitations and proposed roles.
- ✅ Justified decisions clearly distinguished from measured results.
- ✅ Manual dataset/model checklist, missing inputs and [TO VERIFY] markers.
- ✅ References linked to verified existing sources; no invented performance.
- ✅ Two new pytest checks and all prior tests passing.
- ✅ One logical feat(task1) commit for the study, report and checks.

## Known limitations

This is an engineering literature study, not a systematic survey, full-paper
replication or clinical evaluation. Reference tests detect broken citation IDs,
not misinformation, link uptime, legal permission or real-world accuracy.
Resources and checkpoints have not been downloaded/adopted. Data/source licences,
native-speaker review, user-recorded audio and a verified Moroccan medication
catalogue remain prerequisites for later tasks. No Darija-adapted Whisper
checkpoint is selected; no WER/F1/latency result exists for this project yet.

TASK 2 has not started. Next validation gate: VALIDATED TASK 1.

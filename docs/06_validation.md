# Validation Report — TASK 06: Text baseline

The user authorized self-validation and completion without per-task approval pauses.

## Files created/changed

- `configs/baseline.yaml`
- `src/pharma_assistant/nlp/{normalize,langid,intent,entities}.py`
- `src/pharma_assistant/pipeline/text_pipeline.py`
- `src/pharma_assistant/eval/text_baseline.py`
- `scripts/evaluate_baseline.py`
- `tests/test_text_baseline.py; tests/conftest.py`
- `docs/baseline_results.json; docs/draft_review_attestation.json`

## Commands

```bash
make baseline-eval
uv run --frozen pytest tests/test_text_baseline.py -q
```

## Results and limitations

84 user-reviewed draft messages: intent accuracy 0.880952, macro-F1 0.876969. Entity exact agreement 0.853755 against automatic proposals, not verified-gold entity accuracy. Raw offsets, unknown/ambiguous strengths and explicit alternatives are tested. Independent human gold remains empty.

Shared project checks: Ruff and Black passed. The complete suite passed with **519 tests and one existing Starlette/AnyIO deprecation warning**. Detailed aggregate evidence and unresolved external-input validations are in [the final report](11_validation.md).

- ✅ Required implementation paths and reproducible commands provided.
- ✅ Relevant automated and actual execution evidence recorded.
- ✅ Provenance and observed failures retained; no fabricated metrics.
- ❌ Any unavailable scientific validation described above remains unclaimed.

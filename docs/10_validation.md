# Validation Report — TASK 10: Scenarios and evaluation

The user authorized self-validation and completion without per-task approval pauses.

## Files created/changed

- `scripts/run_scenarios.py; scripts/run_ablations.py`
- `docs/10_test_scenarios.md; docs/10_evaluation.md`
- `docs/scenario_results.json; docs/ablation_results.json`

## Commands

```bash
make scenarios
uv run --frozen python scripts/run_ablations.py
```

## Results and limitations

40 scenarios across all eight intents/five varieties were run: 33 primary-intent matches, 7 failures. Saved results preserve every prediction. Evaluation includes confusion matrices, per-type entity counts, 20 observed intent failures, normalization/resolution ablations and measured CPU latency. The full ablation observed p50 1.51 ms, p95 158.93 ms, excluding initialization, ASR and network. Entity agreement is provisional and latency is one machine/run; no independent human-gold accuracy is claimed.

Shared project checks: Ruff and Black passed. The complete suite passed with **519 tests and one existing Starlette/AnyIO deprecation warning**. Detailed aggregate evidence and unresolved external-input validations are in [the final report](11_validation.md).

- ✅ Required implementation paths and reproducible commands provided.
- ✅ Relevant automated and actual execution evidence recorded.
- ✅ Provenance and observed failures retained; no fabricated metrics.
- ❌ Any unavailable scientific validation described above remains unclaimed.

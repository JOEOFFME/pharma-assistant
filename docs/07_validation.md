# Validation Report — TASK 07: Learned NLU and strict JSON provider

The user authorized self-validation and completion without per-task approval pauses.

## Files created/changed

- `src/pharma_assistant/nlp/supervised.py`
- `src/pharma_assistant/nlp/llm.py`
- `src/pharma_assistant/pipeline/hybrid.py`
- `scripts/train_nlu.py; scripts/compare_tracks.py; scripts/fine_tune_encoder.py; scripts/evaluate_encoder.py`
- `docs/supervised_results.json; docs/track_comparison.json`

## Commands

```bash
make train-nlu
uv run --frozen python scripts/compare_tracks.py
```

## Results and limitations

Two supervised alternatives actually trained on 520 train rows: word intent dev accuracy 0.24, char intent dev accuracy 0.40; both BIO NER exact F1 0.947368 on 50 dev rows. Rule baseline and conservative hybrid dev intent accuracy 0.74. The small imbalanced data justifies lightweight experiments, but does not substitute for a pretrained-encoder benchmark. LLM adapter/FakeLLM/fallback tested. No real-provider or encoder experiment is claimed. Optional local-encoder fine-tuning path and pinned torch/transformers extras are provided. Trained model files/cards are locally saved under ignored models/ and reproducible by command.

Shared project checks: Ruff and Black passed. The complete suite passed with **519 tests and one existing Starlette/AnyIO deprecation warning**. Detailed aggregate evidence and unresolved external-input validations are in [the final report](11_validation.md).

- ✅ Required implementation paths and reproducible commands provided.
- ✅ Relevant automated and actual execution evidence recorded.
- ✅ Provenance and observed failures retained; no fabricated metrics.
- ❌ Any unavailable scientific validation described above remains unclaimed.

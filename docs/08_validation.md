# Validation Report — TASK 08: Speech pipeline

The user authorized self-validation and completion without per-task approval pauses.

## Files created/changed

- `configs/asr.yaml`
- `src/pharma_assistant/asr/transcriber.py`
- `src/pharma_assistant/eval/speech.py`
- `scripts/cache_asr.py; scripts/evaluate_speech.py`
- `data/audio/README.md; docs/asr_smoke.json`

## Commands

```bash
make speech-install
uv run --frozen --extra speech python scripts/cache_asr.py
```

## Results and limitations

Pinned tiny model weights were downloaded and real CPU/int8 inference executed on temporary flite synthetic speech; the poor transcript is retained in asr_smoke.json. Actual ffprobe/ffmpeg duration validation and mono/16 kHz conversion are tested. Forty recording prompts and a manifest-based WER/CER runner are supplied. No user recordings exist, so no real-recording WER/CER or ASR model-comparison score is claimed. Source/license: https://huggingface.co/Systran/faster-whisper-tiny/tree/d90ca5f ; implementation: https://github.com/SYSTRAN/faster-whisper .

Shared project checks: Ruff and Black passed. The complete suite passed with **514 tests and one existing Starlette/AnyIO deprecation warning**. Detailed aggregate evidence and unresolved external-input validations are in [the final report](11_validation.md).

- ✅ Required implementation paths and reproducible commands provided.
- ✅ Relevant automated and actual execution evidence recorded.
- ✅ Provenance and observed failures retained; no fabricated metrics.
- ❌ Any unavailable scientific validation described above remains unclaimed.

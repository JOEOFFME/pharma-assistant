# Final Validation Report — remaining project implementation

The user authorized completing the remaining tasks together and self-validation
without approval pauses. The runnable prototype is implemented through packaging.
Scientific acceptance is distinguished from implementation: no missing human
annotations, recordings, encoder runs or real-provider scores are invented.

## Delivered files and behavior

| Area | Main files | Result |
| --- | --- | --- |
| TASK 6 baseline | nlp/normalize.py, langid.py, intent.py, entities.py; pipeline/text_pipeline.py; configs/baseline.yaml | Original Unicode spans preserved, five language varieties, eight intents/entities, reference matching, relations and clarification. |
| TASK 7 supervised/LLM/hybrid | nlp/supervised.py, llm.py; pipeline/hybrid.py; train_nlu.py, compare_tracks.py, fine_tune_encoder.py | Two small supervised models trained; strict JSON provider/fallback and safe hybrid tested; optional local encoder training/evaluation supplied. |
| TASK 8 speech | asr/transcriber.py; eval/speech.py; configs/asr.yaml; cache_asr.py, evaluate_speech.py; data/audio/README.md | Real pinned Whisper inference, actual ffmpeg/ffprobe validation, explicit cache/download step, 40 recording prompts and WER/CER tooling. |
| TASK 9 API | api/app.py, api/service.py; .env.example; tests/test_project_service.py | Health/version, text/voice, medication search, nearby directory, IDs/errors, CORS, optional API key, body/rate limits and privacy-conscious structured logs. |
| TASK 10 evaluation | run_scenarios.py, run_ablations.py; docs/10_evaluation.md; saved JSONs | Forty actual scenarios, confusion matrices, 20 failure examples, entity metrics, normalization/resolution ablations and latency samples. |
| TASK 11 delivery | README.md, web/index.html, docs/architecture.md, 11_checklist.md, Dockerfile, Compose, Makefile, CI | Runnable text/audio demo with highlighting, reproducible setup, explicit models/data preparation, non-root container recipe and complete artifact map. |

Source paths for scripts are `scripts/`; modules are under
`src/pharma_assistant/`. Full per-task reports: [6](06_validation.md),
[7](07_validation.md), [8](08_validation.md), [9](09_validation.md),
[10](10_validation.md). The original corrected draft messages are preserved.
Their regenerated review annotations remain assistant-sourced and unverified;
user intent-review attestation is recorded separately with exact file hashes.
`gold_human.jsonl` is still empty and unchanged.

Follow-up checks enforce fixed safe clarification templates for LLM output,
source-consistent numeric quantities/strengths, and adjacent BIO subtoken merging.
Local encoder evaluation is provided by scripts/evaluate_encoder.py; no encoder
experiment is claimed without actual local weights and a completed run.

## Actual commands and checks

```bash
make install
make medications
make pharmacies
make schema
make dataset
make baseline-eval
make train-nlu
uv run --frozen python scripts/compare_tracks.py
make scenarios
uv run --frozen python scripts/run_ablations.py
uv run --frozen --extra speech python scripts/cache_asr.py
make lint
make test
git diff --check
```

Actual final local output:

```text
uv run --frozen ruff check .
All checks passed!
uv run --frozen black --check .
58 files would be left unchanged.

uv run --frozen pytest
519 passed, 1 warning in 41.01s
```

The one warning is the existing Starlette/AnyIO BlockingPortal deprecation, not
suppressed. Frozen Python 3.11.17 and uv 0.13.4 were used. Unit/integration tests
cover Unicode alignment, language rules, supported/unsupported routing,
negation/alternatives, product ambiguity, exact entity spans, schema consistency,
metric counts, empty/non-human gold rejection, provider retries/fallback,
authentication, rate limits, request validation, safe unexpected errors, actual
audio decoding/resampling, learned model training and hybrid refusal behavior.

The source data rebuilt successfully: 15,883 BDPM specialties and 161,618 aliases;
the saved 50-query medication mini-test remained 50/50 top-1 and top-3 acceptable
family IDs (authored/unreviewed mini-test, not final gold). OSM and NLU reports
were regenerated from the committed sources. No missing source facts were filled.

## Real runtime smoke tests

A real uvicorn subprocess was started and stopped. Over HTTP, health, demo,
text analysis, medication search, nearby directory and voice analysis all
returned **200**. The voice call used actual faster-whisper weights on the
synthetic flite test audio, not the fake model used by unit tests. Evidence:
[http_smoke.json](http_smoke.json), [asr_smoke.json](asr_smoke.json).

Actual model inference succeeded, but its French synthetic-voice transcript was
poor and is retained. This establishes that the speech path runs; it does not
validate natural French/Darija recognition or supply user-recorded WER/CER.
The temporary synthetic audio is not a human recording or a gold example.

## Measured outcomes

| Cohort / method | Observed result |
| --- | --- |
| 84 user-reviewed draft labels, rule baseline | Intent accuracy 88.10%; all-eight-class macro-F1 0.876969 |
| Same draft, automatically proposed entity reference | Exact entity agreement F1 0.853755; provisional, not verified-gold entity accuracy |
| 50 dev examples, word supervised | Intent accuracy 24%; macro-F1 0.193803 |
| 50 dev examples, character supervised | Intent accuracy 40%; macro-F1 0.284722 |
| Both supervised token models on dev | Exact entity F1 0.947368 on unverified dev annotations |
| Baseline / conservative hybrid on dev | Intent accuracy 74%; macro-F1 0.750776 |
| Forty development scenarios | 33 matching primary intents; 7 failures retained |
| Full rule ablation run on draft | P50 1.51 ms, P95 158.93 ms; warm CPU pipeline only |

Every number is backed by saved result JSON, with predictions/counts in
[the evaluation report](10_evaluation.md). Latency excludes initialization, ASR
and network; one hardware run is not a deployment guarantee. Poor learned intent
scores are reported as observed. The baseline remains the default.

## Remaining externally dependent validation

- Independent human-only >=100-row locked gold is absent. The 84 reviewed draft
  messages retain their original assistant provenance; two duplicate greetings
  are explicitly quarantined. No automatic annotation was silently promoted.
- Two/three pretrained encoder fine-tuning benchmarks were not run. A real local
  encoder training path and pinned optional dependencies are provided. The two
  executed experiments are lightweight supervised alternatives, not encoders.
- No real LLM endpoint/key was supplied. The adapter/FakeLLM tests do not establish
  real-provider extraction quality or latency. Real-provider metrics are unclaimed.
- No user-recorded audio was supplied. The WER/CER runner and 40-prompt protocol
  are ready; no recorded-audio WER/CER or comparative ASR quality is fabricated.
- Docker is absent in this workspace. A container build is part of GitHub CI;
  local container execution is not claimed. Check the linked repository Actions
  result for the actual image-build outcome after publication.
- The API is a development prototype with a process-local rate limiter and
  heuristic clinical routing; it never provides medical advice, confirms stock
  or validates prescription/dispensing decisions. It is not clinically validated.

## Acceptance status

- ✅ All remaining implementation layers, commands, tests, UI and packaging supplied.
- ✅ Final local lint and 519-test suite pass; real text/voice HTTP smoke passes.
- ✅ Source attribution, original texts, provenance and failures remain explicit.
- ✅ No approval pauses or next-task gates retained after the user's instruction.
- ✅ Scientific measurements that were actually executed are saved and reproducible.
- ❌ Full scientific acceptance remains incomplete for the external-input items above.

Use [README](../README.md) for setup and [the mapping](11_checklist.md) for every
challenge requirement. No deployment, external messaging or paid provider call
was performed.

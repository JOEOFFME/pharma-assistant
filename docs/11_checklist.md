# Challenge deliverables and self-validation checklist

The user authorized completion of the remaining tasks together and self-validation,
replacing the per-task approval pause. Status below distinguishes implemented code
from scientific validation that requires additional external inputs.

| Requirement | Artifact | Status |
| --- | --- | --- |
| Problem study, related work and approach choices | docs/01_problem_study.md | Implemented; referenced sources retained |
| Eight intents, eight entities, five varieties, strict JSON | docs/02_nlu_spec.md; api/schemas.py | Implemented and tested |
| Directory ingestion, cleaning, SQLite, nearest/city/name | data_tools/clean_pharmacies.py; data/pharmacies.py | Implemented; actual attributed OSM snapshot |
| Medication ingestion, variants, hybrid name retrieval | data_tools/ingest_medications.py; matching/medications.py | Implemented; France fallback explicit |
| Reproducible seed/augmentation/family split | configs/nlu.yaml; data_tools/nlu_dataset.py | Implemented; provenance explicit |
| Independent >=100-row human-verified locked gold | data/nlu/gold_human.jsonl | Not supplied; empty, never fabricated |
| User review attestation for latest draft | docs/draft_review_attestation.json | Recorded for 84 corrected draft messages/intents |
| Unicode/Arabic/Arabizi normalizers with offset alignment | nlp/normalize.py | Implemented and tested |
| Script/lexicon language ID and rule baseline | nlp/langid.py; nlp/intent.py; nlp/entities.py | Implemented and measured |
| Full text/voice v1 pipeline | pipeline/text_pipeline.py; api/service.py | Implemented; real HTTP smoke passed |
| Learned intent and token-level NER | nlp/supervised.py; scripts/train_nlu.py | Two lightweight variants trained; dev results saved |
| Fine-tune and benchmark 2–3 pretrained encoders | scripts/fine_tune_encoder.py; optional encoder deps | Training path implemented; encoder snapshots/experiments not run |
| Strict JSON LLM and provider swapping, timeout/retry/FakeLLM | nlp/llm.py | Implemented/tested; real-provider benchmark not run |
| Hybrid and safe reference grounding | pipeline/hybrid.py | Implemented and measured on dev |
| Configurable CPU Whisper, VAD, audio limits/resampling | asr/transcriber.py; configs/asr.yaml | Real pinned model inference executed |
| >=40 real user recordings and WER/CER per variety | data/audio/README.md; scripts/evaluate_speech.py | Protocol/tooling implemented; recordings absent, metrics unclaimed |
| Text/voice analyze, version/health, search/nearby | api/app.py; api/service.py | Mandatory routes implemented/tested |
| Errors, IDs, CORS, optional API key, body/rate limits | api/app.py | Implemented; single-process rate limiter |
| At least 25 multilingual end-to-end scenarios | docs/10_test_scenarios.md; scenario_results.json | 40 run; 33 matching intents, 7 failures retained |
| Metrics, confusion, >=20 errors, ablations, latency | docs/10_evaluation.md; saved result JSONs | Actual measurements; reference limitations explicit |
| Docker and Compose | docker/Dockerfile; docker-compose.yml | Recipe provided; build checked in GitHub CI |
| Demo with text, audio and entity highlighting | web/index.html | Served locally; real HTTP routes smoke-tested |
| Setup, architecture and expected-output mapping | README.md; docs/architecture.md; this checklist | Implemented |
| Frozen dependencies, lint and tests | pyproject.toml; uv.lock; CI | Local lint passed; 514 tests passed before final documentation |

No live stock, Moroccan PPV, missing pharmacy contact, human authorship, clinical
recommendation, LLM score, encoder score or real-recording WER is invented.
The remaining validations are substantive: this is a runnable prototype, not a
clinically validated or fully benchmarked production service.

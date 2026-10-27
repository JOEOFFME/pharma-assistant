# Consumer answer and speech safeguards

## Reproduced issues and fixes

1. Demo keyword routing returned the Panadol stock fixture for unrelated questions such
   as `Panadol al Irfane est périmé ?`, and returned the scenario duty/list while ignoring
   changed cities, pharmacies and dates. Only complete rehearsed questions in
   `configs/jury_scenario.yaml` now unlock fixture facts. Other formulations get a
   clarification with no records. Fiction labels remain in every simulated answer.
2. A named-pharmacy directory query ignored its explicit city. Name search results now
   also have to match that city; a same-name pharmacy elsewhere is excluded.
3. Consumer chat could use the optional `NLU_TRACK` extraction track. Consumer text and
   legacy consumer voice replies now use a separate deterministic baseline, independent
   of research/LLM settings. Analysis endpoints retain their configurable research tracks.
4. The chat answered speech immediately, even if the transcript was wrong. Microphone
   and attachment input now use `/v1/transcribe/voice`, which returns only unconfirmed
   text. The composer is filled for review/correction, and an answer is requested only
   when the user presses Send. This improves the evidence flow; it does not improve or
   certify the speech model's recognition accuracy.
5. HTML now uses `Cache-Control: no-store`, the script URL has a new cache marker, and
   `/version` exposes the consumer-policy/voice-flow markers for update diagnosis.

## Files

- `api/service.py`: grounded consumer initialization, shared bounded audio transcription,
  evidence-only endpoint, backward-compatible machine voice/analysis endpoints.
- `api/jury_scenario.py` and `configs/jury_scenario.yaml`: complete-question matching.
- `api/answers.py`: enforce name plus stated city when selecting directory records.
- `web/assets/assistant.js`: speech review before sending; no automatic answer/playback.
- `api/app.py` and `web/index.html`: browser cache/update markers.
- `tests/test_hallucination_guards.py`, `tests/ui_journeys.mjs`: adversarial and UI checks.
- README and jury guides: updated speech workflow and scenario matching limits.

## Commands and results

```bash
uv run --frozen --extra speech pytest -q
uv run --frozen --extra speech pytest tests/test_hallucination_guards.py -q
uv run --frozen --extra speech ruff check .
uv run --frozen --extra speech black --check .
node --check web/assets/assistant.js
npm test --prefix web
uv run --frozen --extra speech python scripts/check_jury_demo.py --require-voice
```

- Full suite: **621 passed**, one existing Starlette/AnyIO deprecation warning, 80.88 s.
- Latest focused guard suite: **15 passed**, same warning, 5.76 s.
- Ruff, Black, JavaScript syntax and DOM journeys passed.
- Preflight passed ten normal questions, three fictional cases and real Rabat map results.
  Its initial `--require-voice` run exited 1 because an environment restart removed the
  speech cache. The pinned weights were explicitly cached again; the subsequent runtime
  check verified readiness separately.
- UI checks verify recording only fills the composer, generates no assistant reply or
  text request before confirmation, and uses the current normal/demo text route on Send.
- Adversarial checks cover wrong date/city/product/pharmacy, negation and unrelated
  questions; consumer LLM isolation; named-city constraints; evidence-only transcription.

## Run the update on Windows

Stop the old server with Ctrl+C, then run from the repository directory:

```powershell
git pull origin codex/assistant-answers-voice
uv run --frozen --extra speech python scripts/start_service.py
```

Open http://localhost:8000 and Ctrl+F5. If the microphone reports unavailable, follow
`docs/jury_demo.md` to install audio tools and cache speech weights. The expected
`/version` values are `consumer_policy=grounded_v2`, `voice_flow=confirm_transcript`,
`jury_matching=exact_questions_v2`.

## Acceptance and limits

- [x] Demonstrated wrong-question fixture responses now clarify without returning facts.
- [x] Normal directory answers enforce the stated city alongside the pharmacy name.
- [x] Consumer answers are independent of optional generative extraction.
- [x] Consumer UI requires review/Send before a voice transcript generates an answer.
- [x] New regressions, full suite and lint checks pass.
- [ ] The user's exact latest failing input/output was not supplied; these fixes address
  reproduced cases, not a claim that every possible request is now understood.
- [ ] Human microphone accuracy and audible/visual browser rehearsal remain unverified.

Legacy `/v1/analyze/voice`, `/v1/assistant/voice` and `/v1/demo/assistant/voice` remain
available to API clients with their established behavior. The consumer UI uses the
new confirmation-first flow. No real stock, current duty provider, follow-up memory or
held-out language/speech evaluation was added. Unsupported scenario paraphrases now
intentionally clarify rather than guessing; use the Examples picker for the jury script.

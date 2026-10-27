# Jury MVP validation

## Implemented

- Full viewport chat on desktop and mobile; removed the side illustration panel and
  retained the supplied robot as a compact avatar/welcome image.
- Ten editable demonstration questions in `web/assets/demo-questions.json`, covering
  French, Arabic, Darija, quantity/strength/form summary, spelling variation, Rabat
  directory/phone queries, unavailable prices, unverified duty and medical boundaries.
- Examples use the normal `/v1/assistant/text` route. No canned-answer bypass or fake
  stock/price/duty rows were introduced. Expected full replies and the presentation
  script are in `docs/jury_demo.md`.
- Single-medicine summaries quote supplied quantity/strength/form. Clarification asks
  about missing form/strength rather than asking for details already supplied.
  Multi-medicine details are not assigned to arbitrary products.
- Per-answer browser speech playback, explicit opt-in automatic playback, stop control,
  French/Arabic voice selection and graceful unsupported-browser handling.
- Existing microphone/attachment transcription remains available, with visible transcript
  correction, recording cancellation without upload, idempotent microphone cleanup and
  a retry button for readiness. Conversation reset/navigation stops speech and recording.
- Privacy copy mentions that device speech voices can depend on an external service.

## Reproduce

From repository root:

```bash
uv sync --frozen --extra speech
uv run --frozen --extra speech python scripts/cache_asr.py
uv run --frozen --extra speech python scripts/check_jury_demo.py --require-voice
uv run --frozen --extra speech pytest -q
uv run --frozen --extra speech ruff check .
uv run --frozen --extra speech black --check .
node --check web/assets/assistant.js
npm ci --prefix web --ignore-scripts --no-audit --no-fund
npm test --prefix web
```

The preflight runs the actual API through TestClient using the saved databases and
configured pipeline. It checks all ten intent/reply contracts, a nonempty real Rabat map,
and speech prerequisites. `--require-voice` makes missing prerequisites a failure.

## Results

- Ten curated questions passed; real Rabat map returned records; voice prerequisites READY
  after explicitly caching the pinned weights. These are development regression results.
- Pytest: 584 passed, one existing Starlette/AnyIO deprecation warning.
- Ruff, Black, JavaScript syntax and DOM journeys passed.
- DOM journeys exercise selection/editing without automatic sends, French/Arabic playback
  selection, automatic-playback opt-in, stopping/resetting speech, recording cancellation
  without upload, track cleanup, voice-readiness retry and the existing text/map journeys.
- A real cached-ASR request through TestClient returned HTTP 200 for a generated Flite
  recording. Its English synthetic voice pronouncing a French phrase produced recognition
  errors (`Benjure, j'ai vraie de l'apprain.`); the assistant asked for clarification.
  This is plumbing verification, not successful French/Darija speech evaluation.

## Limits / outstanding checks

- No real microphone recordings were supplied, so no human speech accuracy/WER or
  Windows microphone success is claimed. Rehearse recognition on the actual laptop.
- Browser speech output depends on installed voices; Darija pronunciation is not guaranteed.
- A Chromium download failed with an invalid/truncated archive in this environment.
  No real-browser screenshot, visual rendering, or audible playback verification is claimed.
  DOM tests do not replace that manual rehearsal.
- Live stock, confirmed on-duty status, verified Moroccan prices and transactional ordering
  remain outside this MVP. The directory and French BDPM fallback are saved snapshots.
- Presets are complete independent requests; dialogue history does not provide follow-up context.

## Acceptance checklist

- [x] 5–10 question/answer demonstration contracts (10) and full expected replies.
- [x] Chat occupies the viewport, with technical details hidden from the consumer UI.
- [x] Recording/upload/transcript correction and answer playback controls implemented.
- [x] Real data/API preflight plus regression/lint checks.
- [ ] Microphone, audible output and responsive visual rehearsal on the presentation laptop.

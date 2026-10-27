# Consumer chat redesign — Validation Report

The supplied robot image and subsequent nearby-intent correction supersede the
original companion asset below. See `docs/nearby_request_fix_validation.md` for
the current image, routing behavior and 562-test validation.

## Delivered experience

The reference screenshot guided a blue outer frame, a spacious left conversation
area and a right companion panel. The implementation uses an original fictional
portrait of Amine, explicitly labeled a virtual assistant rather than a clinician.
On small screens the companion becomes a compact strip above the conversation.

The chat contains a greeting, simple suggestion buttons, message bubbles, an
attachment button, microphone recording and a send button. Spoken transcripts
appear as user messages with a correction action. Enter sends; Shift+Enter adds a
line, and composition events do not send incomplete Arabic/IME input.

**Full consumer abstraction:** JSON, entities, confidence scores, API credentials,
model names, dependency checks, install commands and raw coordinates do not appear
in the consumer UI. There is no expandable developer panel. Unavailable voice
shows a short, localized message while typing stays available. Setup remains in
the operator README; server errors are not exposed verbatim.

The map opens separately using a city selector, distance selector and optional
location sharing. Results show names, distance, known phone/hours and calling or
location links. No coordinate entry is required. Plotly is loaded only when the
map opens. The chat still avoids medical advice, live-stock guarantees, order
confirmation, invented prices and duty-status claims.

## Files changed for the redesign

- `web/index.html`: consumer markup, conversation, companion, composer, menu and
  map/privacy dialogs; all developer panels removed.
- `web/assets/assistant.css`: blue reference-inspired styling, desktop/mobile
  layouts, Arabic direction, keyboard focus and reduced-motion support.
- `web/assets/assistant.js`: consumer interaction controller, safe text rendering,
  localized errors, message/voice lifecycle, reset/race handling, map and location.
- `web/assets/companion.webp`: original project-bound companion portrait, 25,164
  bytes, served locally rather than from a temporary image URL.
- `src/pharma_assistant/api/app.py`: public static UI assets; protected analysis
  endpoints still require credentials when configured.
- `src/pharma_assistant/api/answers.py`: remove raw coordinate text from readable
  directory answers while retaining coordinates in machine-readable data.
- `tests/test_assistant_answers.py`: update consumer-page expectations.
- `tests/test_consumer_ui.py`: no technical panels/credentials in consumer copy,
  asset delivery, authenticated API boundary and safe presentation checks.
- `tests/ui_journeys.mjs`, `web/package.json`, `web/package-lock.json`: pinned,
  development-only DOM interaction verification (Happy DOM 20.0.11; Node >=20).
- `.github/workflows/task5-dataset.yml`: run DOM journeys on pull requests and
  pushes alongside Python checks and existing container smoke checks.
- `.gitignore`, `.dockerignore`: exclude optional UI-test dependencies from Git
  and the runtime container.
- `README.md`: current interface and operator configuration instructions.
- This validation report. Earlier Windows/voice fixes remain included in PR #2.

## Verification

```bash
uv run --frozen --extra speech ruff check .
uv run --frozen --extra speech black --check .
uv run --frozen --extra speech pytest -q
node --check web/assets/assistant.js
npm ci --prefix web --ignore-scripts --no-audit --no-fund
npm test --prefix web
```

Actual results:

- `551 passed, 1 warning in 47.68s`; existing Starlette/AnyIO deprecation warning.
- Ruff, Black and JavaScript syntax passed.
- DOM journey output:

```text
PASS: consumer text, safe rendering, private errors, Arabic, composition, reset/race, voice/correction, map/location and unavailable-voice journeys
```

DOM checks execute the actual HTML/JavaScript with deterministic network, media
and geolocation doubles. They cover sending and rendering answers, preserving
user evidence, hiding analysis, escaping untrusted pharmacy/answer text,
localizing errors, Arabic direction, IME composition, resetting in-flight
requests, recording cleanup, transcript correction, map opening and geolocation.
Voice unavailable leaves text sending enabled. These are not live microphone or
model-quality tests. The real Whisper HTTP smoke from the preceding implementation
is retained at `docs/assistant_smoke.json` without claiming new accuracy results.

The image was inspected directly. Pixel-layout QA in a real browser was not
available: the workspace has neither a supported externally accessible Python
preview nor an installed local Chromium executable. Responsive CSS and DOM flows
are verified separately; browser visual/microphone checks remain to be done on
the running app.

## Acceptance checklist

- ✅ Two-panel blue chat/companion design based on the supplied screenshot.
- ✅ Readable chat, attachment/microphone/send controls and voice corrections.
- ✅ No technical details, setup commands, credentials or coordinates in the UI.
- ✅ Consumer map and location controls, mobile adaptation and keyboard access.
- ✅ No frontend secret; backend API protection remains intact.
- ✅ Python tests, static assets, syntax and DOM interaction journeys passed.
- ⚠️ Real-browser pixel layout and native Windows microphone QA remain unverified.
- ⚠️ Speech must be configured by the operator. Hiding setup from consumers does
  not install packages or model weights on the user's PC.
- ⚠️ Replies remain template-based and requests are analyzed independently; a
  displayed conversation does not add unrestricted chat or LLM conversation memory.
- ⚠️ Local-only conversation history resets on refresh and is never persisted by
  this UI. Map data remains incomplete and may be out of date.

## Authentication and operation

The local default does not require an API key. If an operator sets `API_KEY`, the
consumer interface does not reveal it or bypass it. Protected deployments require
an authenticated upstream gateway to supply server-side credentials for approved
visitors. An unauthorized visitor receives a simple reserved-space message. This
change does not add an authentication service.

Follow the Windows/speech commands in README, start the Python service, and open
`http://localhost:8000/` on that machine. Hard-refresh after updating. Technical
setup remains operator documentation; the consumer never sees those instructions.

## Generated asset provenance

Built-in ImageGen was used (not CLI fallback). Final project asset:
`web/assets/companion.webp`. The generated original was copied into the project
as an optimized WebP for local serving; it does not depend on a temporary URL.

Final generation prompt:

> Use case: photorealistic-natural. Asset type: portrait asset for the right
> companion panel of a pharmacy-request assistant web UI. Create an original
> fictional friendly male Moroccan/North African pharmacy service assistant,
> approximately 35 years old, warm confident smile, short dark hair and neatly
> trimmed beard, wearing a clean pale blue overshirt over a white T-shirt,
> holding a slim tablet at waist level. Professional approachable service
> representative; no medical coat, no stethoscope, no badges, no logos, no text.
> Portrait from upper thighs to head, facing slightly left toward the conversation
> with eyes toward camera. Studio photograph with soft natural daylight and
> realistic skin detail. Very light powder blue seamless studio background,
> subtle blue gradient. Portrait 2:3 composition, subject occupies lower two-thirds,
> generous clean background above his head. No other people, no rendered
> interface or frame. This is a fictional virtual-assistant illustration, not
> a clinician endorsement.

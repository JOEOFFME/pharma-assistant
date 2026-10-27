# Readable answers and voice compatibility — Validation Report

## User-visible changes

The demo now displays a localized readable answer instead of a JSON wall.
JSON and entity highlighting are inside a closed, optional technical-details
section. French/mixed, Arabic, Arabic-script Darija and Latin-script Darija use
localized deterministic templates. The reply explains stock/price uncertainty,
asks a product-specific clarification when needed, and never claims an order was
sent. Directory replies use stored pharmacy records and preserve unknown values.
Mixed requests receive an in-scope answer plus a medical-advice refusal.

The voice UI checks readiness and shows setup instructions if tools, the speech
extra or locally cached weights are absent. It chooses a supported recorder MIME
type, handles denied microphone access, stops microphone tracks and timers, and
shows the transcript so the user can correct it before another text submission.
Selected Arabic/Darija/French is also used as an ASR hint.

## Root causes addressed

1. The old UI presented machine-oriented JSON as its main result.
2. On Windows, the open `NamedTemporaryFile` could prevent ffprobe/ffmpeg from
   reopening an uploaded recording. Uploads now use a temporary directory and a
   file closed before decoder access; cleanup occurs after inference/errors.
3. Streaming WebM produced by browser recording may omit duration metadata.
   Such audio now undergoes bounded decoding and sample-count measurement, with
   the same maximum duration enforced. Oversized/invalid audio remains rejected.
4. Missing ffmpeg/ffprobe now produces a clear 503 setup error; prerequisites and
   cached weights can be checked at `GET /v1/voice/status` without downloads.
5. Startup data-tool metrics/manifests use explicit UTF-8 instead of Windows ANSI
   defaults. See `docs/windows_utf8_validation.md`.

The screenshots supplied showed the JSON UI, but did not include a voice error.
The compatibility fixes above address observed code defects; they do not claim
to identify the complete configuration state of the user's Windows computer.

## API compatibility

Existing `/v1/analyze/text` and `/v1/analyze/voice` keep their structured contracts.
New `/v1/assistant/text` and `/v1/assistant/voice` return `answer`, `language`,
`transcript`, `pharmacies`, `analysis` and `disclaimer`. Authentication, rate and
upload limits still apply. No LLM credentials or provider are needed for replies.

## Files changed

- `web/index.html`: readable response, collapsed JSON, voice readiness, microphone
  lifecycle, recorder MIME selection, setup/error messages, Unicode highlighting.
- `src/pharma_assistant/api/answers.py`: grounded localized presenter.
- `src/pharma_assistant/api/service.py`: assistant/status routes, closed-file
  upload lifecycle, tool error and voice language-hint handling.
- `src/pharma_assistant/asr/transcriber.py`: bounded duration-less WebM validation.
- `src/pharma_assistant/asr/readiness.py`: offline prerequisite inspection.
- `src/pharma_assistant/data_tools/{clean_pharmacies,fetch_pharmacies,ingest_medications}.py`:
  UTF-8 file I/O on the startup ingestion path.
- `tests/test_assistant_answers.py`, `tests/test_browser_audio.py`,
  `tests/test_windows_encoding.py`: readable-answer safety, APIs, voice lifecycle,
  real duration-less WebM, missing tools and simulated Windows text encoding.
- `README.md`: human-answer API and PowerShell voice setup.
- `docs/assistant_smoke.json`: actual HTTP/model smoke output on synthetic audio.
- This report and `docs/windows_utf8_validation.md`.

## Commands and results

```bash
uv run --frozen --extra speech ruff check .
uv run --frozen --extra speech black --check .
uv run --frozen --extra speech pytest -q
```

- Ruff and Black: passed.
- Extracted inline JavaScript: `node --check` passed.
- New answer/browser-audio tests: `13 passed, 1 warning in 5.69s`.
- Windows-encoding regression: `1 passed in 0.03s`.
- Full suite: `548 passed, 1 warning in 51.14s` (existing Starlette/AnyIO deprecation).
- Actual local HTTP `/v1/assistant/text`: 200; returns a Latin-script Darija answer
  for `Wach kayn dolipran`, explains lack of live stock and asks which presentation.
- Actual local HTTP `/v1/assistant/voice`: 200 with real cached tiny Whisper
  inference. Synthetic flite speech transcript: `Hello, I am looking for a pharmacy.`
  The reply is out-of-scope because English is outside the configured varieties.
  This tests inference and response plumbing, not supported-language accuracy.
- Real WebM created through a non-seekable ffmpeg pipe has no duration tag; the
  new tests decode it successfully and reject it when above the duration limit.

## Windows setup

Install FFmpeg once, then reopen PowerShell inside the project folder:

```powershell
winget install --id Gyan.FFmpeg --exact
```

```powershell
$env:PYTHONUTF8 = "1"
uv sync --frozen --extra speech
uv run --frozen --extra speech python scripts/cache_asr.py
uv run --frozen --extra speech python scripts/start_service.py
```

Keep `--extra speech` when launching voice. The cache step intentionally downloads
weights; requests never silently download a model. Open `http://localhost:8000/`,
hard-refresh the page, allow the microphone and check **Voix prête**.

## Acceptance and limits

- ✅ Readable localized answers with optional technical output.
- ✅ No fabricated stock, price, orders, duty status or clinical recommendations.
- ✅ Windows-safe upload file lifecycle and explicit UTF-8 ingestion.
- ✅ Browser-style WebM duration validation and language hint forwarding.
- ✅ Readiness/setup messages and actual real-model voice HTTP smoke.
- ⚠️ No native Windows/browser-microphone QA was available in this environment.
- ⚠️ Human answers are templated; this does not add general chat, follow-up memory,
  a live pharmacy stock integration or a medical question-answering model.
- ⚠️ Small Whisper may misunderstand Darija, accents and medication names. Users
  can review and correct the visible transcript. No recorded-audio WER/CER claim.
- ⚠️ FFmpeg, the speech extra, cached weights and browser permissions still need
  to be present on the user's machine.

References checked: https://github.com/SYSTRAN/faster-whisper/blob/master/faster_whisper/utils.py
and https://www.ffmpeg.org/ffprobe-all.html .

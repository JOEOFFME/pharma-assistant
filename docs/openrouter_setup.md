# Main OpenRouter assistant using the pharmacy data

OpenRouter is the default conversational model, not just an intent extractor. It
interprets the request, retrieves matching saved pharmacy contacts, and writes the
reply using those records plus bounded conversation context.

Defaults:

- Primary: `openai/gpt-4.1`
- OpenRouter answer-routing fallback: `anthropic/claude-sonnet-4.6`
- Explicit offline option: `ASSISTANT_NLU=baseline`

You can swap the primary and fallback model IDs to make Claude primary. Both must
support structured JSON output. These are configurable compatibility choices; no
live Darija-quality comparison or provider latency benchmark was performed.

## Windows: configure once in .env

Stop the old server with Ctrl+C. From the repository folder:

```powershell
git pull origin codex/assistant-answers-voice
uv sync --frozen --extra speech
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
notepad .env
```

Put these settings in the local `.env` file, replacing the placeholder privately:

```dotenv
ASSISTANT_NLU=openrouter
OPENROUTER_API_KEY=YOUR_PRIVATE_OPENROUTER_KEY
OPENROUTER_MODEL=openai/gpt-4.1
OPENROUTER_FALLBACK_MODEL=anthropic/claude-sonnet-4.6
```

For Claude first, swap the two model IDs. An empty fallback disables model failover.
`OPENROUTER_API_KEY` is the external model credential. The separate `API_KEY` setting
is optional local API protection; leave it empty for this local demo unless you use an
authenticated gateway. The repository ignores `.env`; never put the real key in `.env.example`, the web UI,
a screenshot, a public commit or chat. Startup now loads `.env` automatically.
Existing PowerShell environment variables take precedence. If an older terminal has
`ASSISTANT_NLU=baseline`, set it to `openrouter` or open a new terminal before starting.

```powershell
uv run --frozen --extra speech python scripts/check_openrouter.py
uv run --frozen --extra speech python scripts/start_service.py
```

The check makes **one API request** for a non-personal Panadol example. Expected:

```text
OpenRouter main-model connection and grounded reply: OK
Model used: <the actual model returned by OpenRouter>
<the generated answer, normally asking for the city>
```

The script reports safe authentication/credit/rate-limit errors without exposing the
key or raw provider error bodies. A successful configuration marker alone is not a
live connection check. No user key was supplied during implementation, so running
this check with your account is still necessary.

Open **http://localhost:8000** and Ctrl+F5. Keep **Scénario du jury off** for real-data
conversation. Try: `Bonjour , ou je peux trouver panadol?`, then `À Rabat`.
The current and recent user questions select fresh directory results; past assistant
messages are not trusted as factual evidence. A new chat clears the page-local history.

## What changed

- OpenRouter writes the final answer from retrieved records; it no longer only labels
  an intent while a template supplies every reply.
- Medicine availability and duty questions can retrieve pharmacy names/phones for the
  specified city or pharmacy. Missing location prompts for a city rather than guessing.
- The French unaccented `ou` in `ou je peux trouver Panadol` no longer marks a single
  medication as an unresolved alternative. `Doliprane ou Spasfon` still does.
- Missing credentials or provider failure leave a useful saved-directory fallback,
  with explicit internal fallback metadata and a simple consumer status message.
- The key and mode persist in `.env` across terminal restarts; shell settings still win.
- The answer request supplies an OpenAI/Claude model fallback list to OpenRouter.
- Up to ten recent turns (maximum 4,000 characters each) stay in page memory and are
  submitted with the next question. They are not persisted as server conversation history.
- Voice still transcribes locally, requires review/Send, then uses the same main model.

## Data and model boundaries

The model receives confirmed text, bounded conversation history and a projection of
relevant pharmacy records: names, city, recorded phones/hours and source URLs. For a
shared position it receives computed straight-line distances, not the raw user GPS
coordinates or original audio. The privacy dialog explains online conversation/data use.

Live stock, verified Moroccan prices and current dated guard schedules are still absent.
The model is instructed to state this and use real saved contacts, not make positive
availability claims. Source IDs, cited names, numeric values and common unsupported
live/clinical statements are checked before showing a generated answer. Rejected output
falls back to saved-directory text. These checks reduce errors; they do not prove every
possible natural-language statement correct. Rehearse the selected model with your key.

Normal chat uses at most one interpretation call (12-second network timeout, 1,200-token
completion cap) and one answer call (30-second timeout, 1,600-token cap), without an
application retry loop. OpenRouter's model failover is provider-side. No specific bill,
quality or uptime is promised. Pytest forces offline defaults and mocks all paid requests.

The three fictional jury scenarios remain explicitly separate, finite and labeled.
Research `/v1/analyze/*` endpoints retain their configurable `NLU_TRACK` setting.
`/version` exposes configuration/model names and key-present status, never the key;
`answer_source` in API replies distinguishes model output from local fallback.

## Official references

- https://openrouter.ai/docs/quickstart
- https://openrouter.ai/docs/guides/features/structured-outputs
- https://openrouter.ai/openai/gpt-4.1
- https://openrouter.ai/anthropic/claude-sonnet-4.6

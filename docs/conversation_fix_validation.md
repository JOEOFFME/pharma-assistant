# Reported conversation fixes — 2026-10-27

The reported conversation lost directory results after explicit location replies and
confirmation, and replaced recoverable errors with an unrelated medical-verification
message. General migraine questions could also receive an unsourced treatment list
labelled as a clarification.

## Reproduced causes

The saved directory already returns five records for both `je suis a rabat madinat
al irfane` and `Rabat AL Irfane`. Two valid model outputs were deterministically
rejected by the old validator: `1. <real pharmacy name> — Rabat.` and
`Hadi <real pharmacy name> — 3la Rabat.`. It interpreted list indices and Arabizi
letters as new numeric claims. This establishes an application bug, not the exact
provider error behind every message in the user's Windows session.

The agent fallback discarded existing directory evidence. It had no prepared local
results for `oui` or a location-only response. The agent could ask permission to
search again even after the user had agreed. A response labelled `clarification`
could contain an unsourced treatment list without triggering the factual-source gate.
The research pass also depended on a second model independently choosing web search.

## Changes

- `api/chat_context.py` resolves current/prior explicit user locations, pharmacy and
  medication requests, and confirmations of preceding pharmacy offers. It prepares
  actual directory results, source links and location-sharing actions. Assistant
  messages can establish an offer, not supply factual locations or contacts.
- `nlp/agent.py` preloads those results, asks the model to answer the already requested
  search, and keeps the existing tool registry. `api/data_chat.py` retains usable local
  results on model failure or another unnecessary permission question. The API analysis
  still describes the current request rather than a previous location turn.
- Directory validation excludes list labels and digits embedded in words, and accepts
  a saved phone formatted with separators. Unsupported factual numbers remain checked.
- City-only results explicitly do not establish the closest pharmacies within Madinat
  Al Irfane. Shared GPS can rank nearby saved entries; no district centroid is invented.
- A factual list without sources is rejected even if labelled `clarification`.
- Once the main agent selects web research, the research pass now uses OpenRouter's
  documented `web` plugin with Exa, domain restrictions and three results. It searches
  once before answering, rather than relying on another optional beta server-tool call.
  Actual provider citation annotations are still required for a successful web result.
- `data/health/references.json` and `nlp/health_reference.py` contain concise paraphrased
  NHS evidence checked on 2026-10-27. This supports general migraine-name examples when
  research/model access fails. Saved references are explicitly labelled, never presented
  as a new web search, a personal treatment choice or Moroccan availability evidence.
- Safe diagnostic codes expose failure categories to operator logs/the live-check script,
  without provider bodies, keys or prompts. The consumer status uses saved-source wording
  when a useful local answer is returned. The UI cache marker is `conversation-v5`.

Sources verified during implementation:

- https://www.nhs.uk/conditions/migraine/ — general treatment classes/examples;
  page last reviewed 2026-03-10.
- https://www.nhs.uk/medicines/sumatriptan/ — migraine-attack use and suitability limits;
  page last reviewed 2026-09-24.
- https://openrouter.ai/docs/guides/features/plugins/web-search — compatibility research
  plugin, Exa, domain filtering and citation annotations.

## Validation

```bash
uv run --frozen pytest -q
uv run --frozen ruff check .
uv run --frozen black --check .
node --check web/assets/assistant.js
npm test --prefix web
```

Full suite: **696 passed**, one existing Starlette/AnyIO deprecation warning, 115.12s.
Lint, formatting, JavaScript syntax and the existing DOM journeys passed. A later
focused rerun of `tests/test_reported_conversation.py` passed **14 tests** in 5.43s,
covering the final current-request analysis metadata adjustment.

A real FastAPI TestClient smoke used the full locally built source databases and
injected a provider HTTP 400 before each main-model response. Every reported directory
turn returned HTTP 200, five source-backed Rabat records and `local_directory`:

- `je suis a rabat madinat al irfane`
- `Rabat AL Irfane`
- `Je voudrais 2 boîtes de Doliprane 1000 mg en comprimés.`
- `oui`

The migraine-name query returned `saved_health_reference` with both NHS source links
during that same outage. Safe logs reported `provider_http_400`; no paid model call
occurred. This is an induced failure test, not a claim that the user's account returns 400.

## Acceptance

- [x] Both location replies return actual saved entries during a provider outage.
- [x] `oui` completes the directory request without another permission prompt.
- [x] Quantity, strength and form from the Doliprane request remain in the local answer.
- [x] General migraine names have attributed saved evidence during an outage.
- [x] Negative/unrelated follow-ups do not replay a past directory request.
- [x] Numbered lists, Arabizi and saved phone formatting pass validation.
- [x] Unsupported numeric facts and unsourced treatment lists remain rejected.
- [x] Saved city results do not pretend to establish exact neighborhood proximity.
- [x] Safe operator diagnostics and updated setup instructions are included.
- [ ] Live user-account search permissions/model quality remain untested: no private key supplied.

## Windows update and limits

Stop the old server, run `git pull origin codex/assistant-answers-voice`, then
`uv run --frozen --extra speech python scripts/start_service.py`. Open
http://localhost:8000 and press Ctrl+F5. Keep jury simulation off for real records.
Run `uv run --frozen python scripts/check_agent.py` separately to check live research.
Its safe diagnostic codes may be shared; do not share the API key.

The directory is incomplete and its phones/hours may be outdated. There is no live
stock, verified Moroccan price or dated duty feed. The saved health reference is a
small general-education fallback, not a prescribing database or proof of suitability.
Provider citation validation cannot prove every generated summary accurate. No new
human voice/Windows microphone accuracy or live paid-search success is claimed.

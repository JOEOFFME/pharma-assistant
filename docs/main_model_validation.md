# OpenRouter as the main data-grounded assistant

## Result

Normal consumer chat now uses OpenRouter to write the final answer from retrieved
pharmacy records. It no longer uses the model only for intent/span extraction.
Defaults are `openai/gpt-4.1` and answer-routing fallback
`anthropic/claude-sonnet-4.6`, configurable in the ignored local `.env` file.

The screenshot's generic error can arise from several server/configuration failures;
its exact HTTP error/credential state was not supplied. Two reproduced problems were
fixed: missing OpenRouter settings caused an unhelpful service error, and `ou` in
`Bonjour , ou je peux trouver panadol?` marked Panadol as an unresolved alternative,
so the assistant asked for the medicine name again.

## Implementation

- Normal default `ASSISTANT_NLU=openrouter`. Baseline remains an explicit offline mode.
- Interpretation then retrieval then actual model-written response, with structured
  source IDs and explicit unverified stock/duty fields. Medicine and duty questions can
  retrieve saved pharmacy contacts for their stated pharmacy/city or shared position.
- Responses are checked for unknown source IDs, missing cited names, new numeric facts,
  and common unsupported stock/duty/open-now or clinical claims. Rejected/unavailable
  model responses return local directory information with explicit fallback metadata.
- At most one interpretation request and one answer request per normal question,
  bounded completion tokens/timeouts/body sizes. OpenRouter receives the configured
  OpenAI/Claude fallback list for answer generation; the returned model is recorded in
  API metadata, never portrayed as a successful call when a local fallback was used.
- Missing keys preserve local directory answers with `openrouter_key_missing` status;
  no false claim of a connected model. Provider exceptions log only error type/status,
  not keys, request bodies or private provider messages.
- Up to ten bounded page-local turns support conversational follow-ups. Prior user
  location/pharmacy text can select a fresh database lookup; prior assistant prose is
  never treated as verified evidence. History resets on new chat or mode change.
- Startup and the live-check script load the local `.env` automatically, without
  overriding existing shell settings. `python-dotenv==1.1.1` and its lock entry are pinned.
- The single-product French “ou je peux trouver …” case stays affirmed. “Doliprane ou
  Spasfon” still marks a product alternative, with a separate regression test.
- Confirm-first voice, separate finite fictional jury scenarios and medical boundaries
  remain. Privacy copy discloses online conversation and relevant directory data use.

## Validation

```bash
uv run --frozen --extra speech pytest -q
uv run --frozen --extra speech ruff check .
uv run --frozen --extra speech black --check .
node --check web/assets/assistant.js
npm test --prefix web
```

- **656 passed**, one existing Starlette/AnyIO deprecation warning, 94.30 s.
- Latest focused main-model suite: **14 passed**, same dependency warning, 5.87 s.
- Ruff, Black, JavaScript syntax and DOM journeys passed.
- New tests cover main-model generation rather than planning alone, exact screenshot
  wording, retained medicine alternatives, real saved Rabat contacts, rejected live
  claims/numeric facts/citations, useful provider-failure fallback, bounded history,
  OpenAI/Claude request routing, follow-up retrieval during outage and actual `.env`
  loading with shell precedence.
- A real local HTTP/TestClient request for the screenshot wording returned HTTP 200
  with Panadol acknowledged and unverified-stock wording, using the missing-key fallback.
  This is a directory-path smoke check, not a live OpenRouter success.
- All provider requests in automated tests are mocked. No user key was supplied and
  no paid inference was made. No real model availability, account authentication,
  semantic quality, billing, speed, Windows mic or visual/audible browser result is claimed.

## User startup / acceptance

Follow `docs/openrouter_setup.md`: update, sync dependencies, privately add the key to
`.env`, run `scripts/check_openrouter.py`, then `scripts/start_service.py`. The explicit
check makes one real API request on the user's account and prints the actual model
and generated answer, or a safe authentication/credit/rate-limit explanation.

- [x] OpenRouter writes main consumer answers using relevant saved data.
- [x] Configurable OpenAI primary / Claude fallback, including primary-model swapping.
- [x] Automatic private `.env` configuration and meaningful fallback information.
- [x] Screenshot-input regression, bounded follow-up context and source checks.
- [x] Full automated suite and required formatting/lint checks pass.
- [ ] User must run the live check with their private account key.
- [ ] Real language quality and presentation-laptop voice/visual rehearsal remain pending.

## Limits

Source/number checks and structured output reduce errors; they cannot prove every
natural-language statement correct. Phone/hours records are a saved, incomplete source,
not live business verification. No current stock, dated duty schedule, verified Moroccan
price feed, ordering or clinical advice was added. The fictional jury dataset remains
separate and must not be interpreted as real observations. A fixed guard was not removed
to make the model pretend those unavailable facts are known.

# Optional OpenRouter integration: validation

## Implemented

- Server-side OpenRouter chat-completions adapter using bearer authentication, the
  documented chat response envelope and strict JSON-schema structured output.
- A small `QueryPlan` contains only intent, response language, a medical-request flag
  and literal medication/pharmacy/location spans. It has no answer, stock, price,
  phone, ingredient or duty-schedule fields.
- The optional consumer pipeline validates source offsets, retains locally known city
  constraints and negation, then validates the existing complete analysis contract.
  Source directory lookups and fixed local answer templates remain authoritative.
- Opt in with `ASSISTANT_NLU=openrouter`, `OPENROUTER_API_KEY` and `OPENROUTER_MODEL`.
  Baseline remains the default; consumer selection is separate from research `NLU_TRACK`.
  Missing requested provider configuration returns 503 rather than claiming connection.
- Bounds: one application-level request, 12-second network timeout, 1,200 completion
  tokens and 128 KiB response limit. Invalid/truncated/unsupported/rate-limited or
  unavailable results fall back to the local parser, without exposing provider bodies.
- Clinical rules bypass the provider; additional model-detected clinical requests get
  a fixed refusal. The three fictional jury scenarios remain finite and explicitly labeled.
- No new SDK dependency. Tests force offline consumer defaults to avoid inheriting an
  operator's paid-provider setting. OpenRouter tests mock all transport/model responses.
- Private Windows setup and an explicit one-request connection script are documented
  in `docs/openrouter_setup.md`. The UI privacy copy discloses online text processing.

## Files

`nlp/openrouter.py`, `api/service.py`, `api/answers.py`, `.env.example`,
`scripts/check_openrouter.py`, `tests/test_openrouter.py`, `tests/conftest.py`,
README, setup/validation documents and consumer privacy copy.

## Validation

```bash
uv run --frozen --extra speech pytest -q
uv run --frozen --extra speech ruff check .
uv run --frozen --extra speech black --check .
node --check web/assets/assistant.js
npm test --prefix web
```

- **642 pytest tests passed**, one existing Starlette/AnyIO deprecation warning, 85.10 s.
- Includes **21 new mocked OpenRouter cases**, covering the exact named-pharmacy Darija
  stock request, source-span/city checks, medication negation, clinical boundaries,
  connection failures, 401/402/429/503 responses, malformed/truncated/oversized results,
  missing settings, explicit consumer opt-in and key isolation from request body/UI.
- Ruff, Black, JavaScript syntax and consumer DOM journeys passed.
- No user key was supplied, no paid API request was made during implementation, and no
  actual model quality, availability, billing, latency or authentication result is claimed.

## Acceptance and limits

- [x] OpenRouter-compatible transport and optional consumer integration implemented.
- [x] Model interpretation cannot directly supply factual answer fields.
- [x] Safe local fallback and existing text/voice/jury behavior retained.
- [x] Private local key/model configuration and explicit live-check command provided.
- [x] Reproducible mocked tests, full suite and lint checks passed.
- [ ] User must configure their local key/model and run the explicit connection check.
- [ ] Real French/Arabic/Darija interpretation quality needs evaluation on that model.

The example setup uses `openai/gpt-4.1`, whose OpenRouter model page lists structured
outputs. It is a compatibility example, not a measured best-model recommendation.
A valid JSON schema or literal source span cannot guarantee correct intent recognition;
the model can still misinterpret a question. Real pharmacy stock, dated duty schedules,
verified Moroccan prices, conversation memory and speech-model improvements are not
provided by this integration. Audio remains locally transcribed and must be reviewed;
only confirmed text is sent to the optional online language service.

## Official references consulted

- https://openrouter.ai/docs/quickstart
- https://openrouter.ai/docs/guides/features/structured-outputs
- https://openrouter.ai/openai/gpt-4.1

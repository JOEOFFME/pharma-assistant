# Tool-agent validation — 2026-10-27

## Outcome

Normal OpenRouter chat now chooses and executes read-only tools rather than being
blocked by the directory-only clinical-intent gate. General health education can
use trusted web research with displayed source links. Personal prescribing, dosage,
diagnosis and substitution remain excluded. The original research analysis API and
explicitly fictional jury scenario keep their existing contracts.

## Files

- `src/pharma_assistant/nlp/agent.py`: bounded OpenRouter function-calling loop,
  pharmacy/medicine/web tools, search-domain/citation validation and final reply checks.
- `src/pharma_assistant/api/data_chat.py`, `api/service.py`: agent dispatch, explicit
  fallback, shared live-claim checks, no preceding intent-model gate for text chat,
  and version capability markers.
- `src/pharma_assistant/nlp/mcp_stdio.py`, `scripts/run_mcp.py`: shared tool registry
  exposed through a minimal MCP stdio protocol process.
- `scripts/check_agent.py`: explicit paid live rehearsal; safe diagnostics and UTF-8 output.
- `.env.example`: default agent/search switches; no real credentials committed.
- `web/assets/assistant.js`, `assistant.css`, `web/index.html`: HTTPS source links,
  safe text rendering, online-search privacy copy and script-cache version.
- `tests/test_agent.py`, `tests/conftest.py`, `tests/ui_journeys.mjs`: controlled
  tool-agent/transport/protocol regressions, isolated offline tests and source-link safety.
- `docs/agent_setup.md`, `docs/openrouter_setup.md`, `README.md`: setup and scope.

No new dependency was needed. Existing pinned libraries and `uv.lock` remain valid.

## Commands and results

```bash
uv run --frozen pytest -q
```

**678 passed**, one existing Starlette/AnyIO deprecation warning, 109.04 seconds.
After the final general-existence language adjustment and four added cases:

```bash
uv run --frozen pytest -q tests/test_agent.py tests/test_data_chat.py tests/test_openrouter.py
```

**61 passed**, the same warning, 19.32 seconds. This focused rerun covers the changed
shared live-claim validator and both conversation paths. The full suite was not
rerun after that final adjustment; no larger final test total is claimed.

```bash
uv run --frozen ruff check .
uv run --frozen black --check .
node --check web/assets/assistant.js
npm test --prefix web
```

All passed. UI tests use the real HTML/JS in HappyDOM with mocked network, speech,
media and geolocation. Source titles remain text, JavaScript URLs and credentialed
URLs are rejected, external links use `noopener noreferrer`. Existing text/voice,
confirmation, chat-reset, race, map and fictional-mode journeys still pass.

A real subprocess smoke launched `scripts/run_mcp.py` from `/tmp`, outside the project,
using the project's environment and actual local databases. It successfully negotiated
initialization, advertised `search_pharmacies` and `search_medications`, and returned
three catalogue matches for Doliprane. Web was explicitly disabled for this smoke.
Stdout parsed as protocol-only JSON. No paid inference was executed.

## Acceptance checklist

- [x] Main normal-chat agent chooses function tools and consumes tool results.
- [x] Web research is implemented with OpenRouter's documented server tool, the
  existing private key, fixed public-health domains and bounded search results.
- [x] All three supplied Darija migraine messages and follow-up history are covered
  by mocked tool/research/final-answer regressions; no fixed live treatment Q/A is inserted.
- [x] The API no longer runs the refusal-prone extraction model before text-agent execution.
- [x] General sourced `kayn ... traitement` wording is allowed, while explicit pharmacy
  availability, stock and duty assertions are still rejected in focused tests.
- [x] Tool allowlists, strict query arguments, response bounds, source-ID checks,
  dosing-pattern rejection, unknown tool errors and loop limits are tested.
- [x] Missing/invalid web citations become a tool failure visible to the model;
  failed research does not masquerade as a cited successful search.
- [x] Source links display safely in the UI without exposing keys or structured internals.
- [x] MCP initialization, discovery, catalogue execution, errors, notifications and
  foreign-working-directory launch are verified.
- [x] Private live-check command and exact Windows configuration are documented.
- [ ] Live account authentication, paid server-tool permission, real generated answer
  quality and Darija pronunciation: no user's key supplied, so not tested.
- [ ] Independent third-party MCP host interoperability/certification: not performed.

## Known limitations

Provider/model availability, strict-schema/tool compatibility and search permissions
require a live check with the user's account. Tests mock paid HTTP responses; their
medicine examples demonstrate control flow, not clinical validation or real web retrieval.
A successful source citation does not prove that every model summary is accurate.
Clinical and live-data checks are conservative patterns plus model instructions, not
formal guarantees. General education is broader than the repository's original
pharmacy-only response policy, implementing the user's explicit new feature request.

The agent does not create a live Moroccan stock, price or duty feed. The source
catalogue is not a Moroccan prescribing registry. It cannot choose an individual's
medicine safely. Search inputs use model-instructed generic topic words; full chat is
still sent to the configured model service as explained in the privacy dialog. The
MCP server is local stdio, not a remote HTTP service or an arbitrary-MCP-server loader.
No shell, purchase, ordering or messaging tool is available to the agent. Voice retains
its earlier confirmation flow; no real Windows microphone/audible playback claim is made.

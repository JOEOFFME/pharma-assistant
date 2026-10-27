# Pharma-AI research agent and MCP tools

Normal OpenRouter chat now runs a bounded tool-calling agent. It can interpret a
question, choose a tool, read its result, then answer with source links. The old
consumer rule that refused every treatment-topic question no longer blocks this
agent. The research analysis API and the explicitly fictional jury mode are unchanged.

## Windows setup

These changes are on `codex/assistant-answers-voice` in PR #2. Stop the old server,
then update your checkout (preserve any local edits):

```powershell
git pull origin codex/assistant-answers-voice
uv sync --frozen --extra speech
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
notepad .env
```

Keep your real key private in `.env` and include:

```dotenv
ASSISTANT_NLU=openrouter
OPENROUTER_API_KEY=YOUR_PRIVATE_KEY
OPENROUTER_MODEL=openai/gpt-4.1
OPENROUTER_FALLBACK_MODEL=anthropic/claude-sonnet-4.6
ASSISTANT_AGENT=true
ASSISTANT_WEB_SEARCH=true
```

Existing environment variables override `.env`; remove old overrides or open a new
terminal. Models must support function tools and strict JSON output. Model IDs are
configurable; the fallback uses the same tool/schema contract.

```powershell
uv run --frozen --extra speech python scripts/start_service.py
```

Open http://localhost:8000, press Ctrl+F5 and leave **Scénario du jury off**. In a
second terminal, you can explicitly test the live agent:

```powershell
uv run --frozen python scripts/check_agent.py
```

This runs the public sample `chnu smiya dyal dwa dyal la migraine ?`. Expected after
an actual successful research run:

```text
Agent tool execution and cited web answer: OK
Model used: <actual model>
<source-supported answer in Darija>
<source title and URL>
```

The check fails if research has no usable citation or the model does not complete a
cited web answer. It does not claim clinical correctness or language quality from a
successful connection alone. Web search incurs additional OpenRouter charges. No
additional search key is needed; the OpenRouter account must permit web research.
The older `scripts/check_openrouter.py` checks basic model access only, not tools.

## Conversation reliability update

The directory is retrieved before the model answers when the user supplies a city,
asks for nearby pharmacies, or confirms a previous search offer. Explicit user places
persist through bounded conversation context; assistant prose supplies intent only.
`Rabat AL Irfane` and `oui` now retain the Rabat lookup. Model failure or a repeated
permission question returns actual saved entries and source links. City results do
not claim to be ranked by proximity within Al Irfane; sharing GPS enables distance
sorting. Requested quantity, strength and form remain request details, not dosing advice.

A small saved NHS educational reference supports general migraine medicine-name
questions even if live research fails. Saved information is identified as such and
linked to its source; it does not masquerade as a fresh search or Moroccan stock data.
The source summaries were checked on 2026-10-27. They contain no dosage instructions.

Numbered lists, Arabizi words such as `3la`, and formatting a saved phone with spaces
no longer count as unsupported new numeric facts. Actual unsupported numeric claims
remain rejected. An unsourced treatment list cannot bypass citation checks merely
by being labelled a clarification. Safe diagnostic codes distinguish validation
failures from provider HTTP errors without logging keys, prompts or error bodies.

## Available tools

| Tool | Data / action | Limits |
| --- | --- | --- |
| `search_pharmacies` | Saved SQLite directory by city/name, or a user-shared position | No inferred GPS, stock or dated guard data; incomplete coverage |
| `search_medications` | Named-product fuzzy lookup with source country, ingredient and form | Source catalogue, not symptom-based prescribing or proof of Moroccan availability |
| `search_health_web` | OpenRouter `web` research plugin via Exa | Fixed public-health domains, one research request per chat turn, three results per search |

The main model still chooses whether to invoke `search_health_web`. Once invoked,
the research pass uses OpenRouter's documented `web` plugin, which performs the
search before answering. This replaces reliance on a second model independently
choosing to call a beta server tool. It uses `include_domains`, Exa and three results;
responses still require provider citation annotations. No HTML/model-invented link
is accepted as proof of a successful live search.

Health domains: NHS, Ameli, WHO, MedlinePlus, NINDS, ANSM, the French public medicine
database, and Morocco's Ministry of Health. Returned citations must be HTTPS URLs
within that list. A response without attributable health citations is a failed
research result, not a successful search. The app itself does not fetch arbitrary
URLs, execute shell commands, make purchases, or contact pharmacies.

The language model receives up to ten page-local conversation turns. It can resolve
`bghit ghir smya dyalo` from an earlier migraine question before constructing a
generic search query. It should provide general names/categories backed by sources,
explain that these are educational examples, and avoid choosing a personal treatment.
This is generated behavior, not a fixed Q/A answer or a claim that all medicines are
suitable for the user. Diagnosis, personal prescribing, dosing and substitution
remain outside the assistant's scope. Urgent symptoms should prompt urgent help.

The UI renders plain answer text plus HTTPS source links, without JSON or model
internals. New chat clears history and shared position. Voice keeps the existing
review-transcript-before-send and per-answer playback flow.

## Agent budgets and failures

At most four main-model turns, eight tool calls and one web research request are
allowed per user message. The overall application deadline is approximately 85
seconds, checked between operations; individual main calls have at most 30 seconds
and research at most 40 seconds within the remaining deadline. OpenRouter may have
its own internal search executions. The compatibility plugin requests up to three results in its single research pass; do not interpret this as a guaranteed monetary charge cap.

Unknown tools, extra arguments, invented source IDs, unreferenced factual answers,
common live-stock/duty claims and obvious dosing-like answers are rejected. Directory
answers additionally use the existing numeric/name/citation validation. These checks
and prompts reduce risk; they do not prove every claim in every generated sentence.
A valid citation can still support an incorrect summary. Live account rehearsal and
human review remain necessary. On agent failure, the UI gets an honest temporary
verification failure, not a claim that a web search succeeded. Missing credentials
retain the existing local-directory mode.

Set `ASSISTANT_WEB_SEARCH=false` to disable online research. Set
`ASSISTANT_AGENT=false` to retain the previous directory-grounded conversation path.
Set `ASSISTANT_NLU=baseline` for offline directory responses.

## MCP stdio server

The same validated tool registry is exposed to local MCP clients. Chat invokes the
registry directly; it does not spawn an MCP subprocess for each message. The MCP
adapter lets another MCP host discover and call those tools independently.

```powershell
uv run --frozen python scripts/run_mcp.py
```

This is a stdio protocol process, not a browser URL or an interactive chat prompt.
Configure an MCP host with command `uv`, args `run --project <ABSOLUTE_PROJECT_PATH>
--frozen python <ABSOLUTE_PROJECT_PATH>/scripts/run_mcp.py`. The process loads the
project `.env` privately and supports being launched from a different working directory.
Never put a key in the public host configuration. Web research is only advertised
when a key is configured and `ASSISTANT_WEB_SEARCH=true`.

The adapter supports JSON-RPC initialization/version negotiation for 2024-11-05,
2025-03-26 and 2025-06-18, `ping`, `tools/list`, `tools/call`, notifications without
responses, text/structured tool results and safe errors. It is a minimal read-only
stdio implementation, without remote HTTP/SSE hosting, OAuth, subscriptions, remote
server installation, or arbitrary MCP server connections. Tool discovery, initialization
and catalogue execution have been tested; no third-party MCP host certification is
claimed. Stdout contains only protocol messages.

## References

- https://openrouter.ai/docs/guides/features/tool-calling
- https://openrouter.ai/docs/guides/features/server-tools/web-search
- https://modelcontextprotocol.io/specification/2025-06-18/server/tools
- Validation: `docs/agent_validation.md`

Latest conversation regression report: [conversation_fix_validation.md](conversation_fix_validation.md).

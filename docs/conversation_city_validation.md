# Conversation city and package follow-up validation — 2026-10-27

## Reported behavior and changes

The new transcript showed an Al Irfane stock question returning same-name pharmacies
in Oujda/Fes/Dakhla despite the user's earlier Rabat. City and pharmacy name were
selected together from one turn, dropping the previous explicit city. The directory
resolver now resolves the latest explicit user city independently, constructs an
internal retrieval query with it, and preserves the original public user analysis.
Named results are filtered by city; without a city, a named stock question asks for
one rather than displaying mixed cities. Subsequent local directory tool queries
inherit the resolved city when they omit a location.

A Panadol-finding request is recognized as directory intent even without an explicit
city in the current turn. It uses prior city evidence without inheriting an old
pharmacy name; with no city it asks for one. On agent failure it can return saved
contacts instead of a generic clinical fallback. Attributed saved contact enrichment
can cover a named business absent from the OSM snapshot, and is labelled saved rather
than fresh research. Nothing here establishes current stock.

A one-word `dosage` immediately after a package clarification explains that it means
the mg/g printed on the box, not the amount to take. It does not prescribe a personal
dose. Unrelated or personal-dose questions do not trigger this shortcut. Ambiguous
CNOPS spelling/price clarification now cites the historical reference generically,
not the arbitrary first matching brand. Unrelated factual answers clear inherited
map/contact actions.

## Checks

- Full suite on the intermediate implementation: 755 passed, one existing
  Starlette/AnyIO deprecation warning, 151.79 seconds. This preceded final tool-city
  scoping, presentation wording/source-label refinements and added regression cases.
- Final targeted agent/CNOPS/conversation tests: 95 passed, one existing
  dependency warning, 41.79 seconds. Command: `uv run --frozen pytest -q
  tests/test_latest_transcript.py tests/test_reported_conversation.py
  tests/test_data_chat.py tests/test_agent.py tests/test_cnops_agent.py`.
- Ruff and Black checks pass (77 Python files); JavaScript syntax checked.
- Existing consumer DOM journeys pass; no UI markup changed.

New regressions cover the reported named-stock city, Panadol city inheritance without
sticky pharmacy names, missing city, provider outage, the `dosage` package explanation,
non-prescriptive behavior, reference source labels and subsequent tool city scope.
Provider calls in these final regression cases are mocked; they do not validate live
OpenRouter language quality, account configuration, search coverage or medicine stock.
A failed preliminary regression used the test fixture's agent-disabled mode; final
agent tests explicitly select agent mode so the mocked transport is exercised.

## Reproduce

Stop the server and preserve `.env`, then:

```powershell
git pull origin codex/assistant-answers-voice
uv sync --frozen --extra speech
uv run --frozen --extra speech python scripts/start_service.py
```

Use Ctrl+F5 and a new conversation. Send a named contact request, `Rabat`, a Panadol
finding question, the named Panadol stock question, then `ch7al prix dyal amoxiline`
and `dosage`. Stock must stay unconfirmed, the stock-contact reply must not jump to
Oujda, and `dosage` must ask for package information rather than a personal dose.

Acceptance: city inheritance/filtering, absent-city clarification, useful saved-data
fallback, package follow-up and generic reference attribution are regression-covered.
Live paid provider evaluation remains to be performed with the user's local key.

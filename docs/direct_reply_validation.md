# Direct replies and research attribution — 2026-10-27

The reported migraine example was supported by the displayed NHS references, but
answered a request for one example with a broad explanation and an unsolicited
follow-up. The following Panadol reply implied a completed research attempt without
displaying corresponding source evidence, then asked for the missing location only
at the end. These observations do not establish that every medical statement was
factually false; they establish presentation and research-attribution defects.

Changes:

- `api/reply_policy.py`: narrow presentation rules for a general medicine-name
  example backed by the saved reference, and a named-product search lacking location.
  A source-backed example gives one name and a short professional-suitability boundary.
  A missing city yields one question, without invented stock/research claims. Existing
  user location/history and shared GPS prevent another redundant location question.
- `api/data_chat.py`: apply these bounded replies in normal agent mode, retaining the
  OpenRouter agent for other questions and explicit web research. The research API,
  explicitly disabled agent mode and fictional jury endpoints retain their contracts.
- `nlp/health_reference.py`: optional concise rendering, with the same attributed
  sources. A name follow-up only uses the most recent user topic, so a new Panadol
  question does not revive an earlier migraine reference.
- `nlp/agent.py`: shorter-answer instructions and a research-attribution check. Phrases
  claiming a completed research effort require a successful web-tool result or an
  explicitly identified saved directory/catalogue lookup.
- `tests/test_direct_replies.py`: exact reported inputs, preserved user city, personal
  dosing exclusion, explicit-web exclusion, false research claims, changed topic,
  negative examples and questions about a physician rather than a medicine.

Expected Panadol reply when no location was supplied:

`Dans quelle ville ou quel quartier cherchez-vous « Panadol » ?`

The general migraine example uses the saved NHS evidence and shows its source links.
It does not claim that a new web search occurred. The direct branch is deliberately
limited to this attributed reference scope, not a general catalogue of prescriptions.
Requests for dosing, a personal treatment choice, explicit online research or a
negated example do not use that branch. The safeguards reduce errors; they do not
prove every possible free-form model answer correct.

Validation:

```bash
uv run --frozen pytest -q
uv run --frozen pytest -q tests/test_direct_replies.py tests/test_reported_conversation.py tests/test_agent.py
uv run --frozen ruff check .
uv run --frozen black --check .
```

Full suite: **715 passed**, one existing Starlette/AnyIO deprecation warning, 322.01s.
After the last topic/negative-example guards and three added tests, the focused
suite passed **52 tests**, 36.71s. The larger full suite was not repeated after those
final scoped guards; no full-suite total including the three added tests is claimed.
Ruff and Black passed before those final guards; the final formatting/lint check is
also part of the handoff. The earlier focused set passed 63 tests before those guards.
No paid provider call or live account quality test occurred; provider tests use mocks.

Acceptance:

- [x] The exact request for one migraine example returns one sourced short example.
- [x] The exact Panadol search without location asks only for that location.
- [x] An explicit user city is retained.
- [x] Personal dosing and explicit web questions do not use the example template.
- [x] Changed topic, negation and a physician-name question cannot reuse that example.
- [x] Claimed research is rejected without corresponding successful search evidence.
- [ ] Real model quality across arbitrary questions still requires live evaluation.

Windows: stop the old server, update `codex/assistant-answers-voice`, restart with
`uv run --frozen --extra speech python scripts/start_service.py`, and refresh the UI.
The current changes remain on PR #2, not main. Use a new conversation to rehearse
these exact questions without prior unrelated location context.

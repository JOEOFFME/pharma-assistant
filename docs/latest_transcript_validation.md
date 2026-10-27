# Latest conversation regression validation — 2026-10-27

## Problems and resulting behavior

- A short new question inherited the old named-contact intent. Only an explicit
  location statement immediately following a named-contact question can continue
  that question. A medicine/location or price question starts its own request.
- Telecontact's Elirfane listing labels 0537686317 as telephone and 0537770240 as
  fax. Contact extraction now excludes labelled fax numbers and truncates sibling
  pharmacy/footer blocks. This is role extraction, not evidence that the fax was
  an invented number. Sources inspected:
  https://www.telecontact.ma/annonceur/pharmacie-elirfane/2159702/rabat.php
  https://www.med.ma/pharmacy/rabat/pharmacie-el-irfane--45546
- CNOPS matching offers conservative spelling candidates from actual source
  names/DCIs. `amoxiline` proposes `amoxicilline`, explicitly requiring identity
  confirmation. The imported historical workbook has 157 matching rows for that
  DCI; no arbitrary first row is treated as the requested presentation.
- An ambiguous price request asks for trade name, strength, form and pack size.
  This source-derived clarification also survives a provider outage and prevents
  an unrelated saved Rabat pharmacy list or medical-refusal fallback. Explicit
  comparison/list requests remain agent research requests. A brand such as
  Panadol is preserved instead of silently replacing it with an ingredient.
- Duty research accepts explicit French shared-year date intervals and checks
  overlap with the requested week. It does not infer a missing year from today.
  Source retrieval without verified matching facts is displayed as information
  unconfirmed, retains consulted sources, and is distinct from transport failure.

## Validation

- `uv run --frozen pytest -q`: **749 passed**, 309.88 seconds; one existing
  Starlette/AnyIO dependency deprecation warning. This run preceded the final
  shared-year date helper refactor and endpoint regression test.
- After that final change: `uv run --frozen pytest -q
  tests/test_latest_transcript.py tests/test_pharmacy_web.py`: **24 passed**,
  25.79 seconds.
- `uv run --frozen ruff check .`: passed.
- `uv run --frozen black --check src tests`: passed (77 files).
- `node --check web/assets/assistant.js`: passed.
- `npm test --prefix web`: consumer DOM journeys passed.

Provider transports in tests are simulated. Actual CNOPS source bytes and matching
are used; the public business pages were independently inspected. No usable private
OpenRouter key is configured here, so no paid live inference/search or user-account
compatibility is claimed. No current duty schedule or Panadol stock was established
by this change. A cited source and these guards do not prove all model prose correct.
The CNOPS workbook remains the 2014 edition with 2017 resource metadata, not today's
price/stock evidence. Personal diagnosis, prescribing and dosing remain excluded.

## Reproduce on Windows

Stop the service, preserve your private `.env`, then:

```powershell
git pull origin codex/assistant-answers-voice
uv sync --frozen --extra speech
uv run --frozen --extra speech python scripts/start_service.py
```

Refresh http://localhost:8000 with Ctrl+F5 and start a new conversation. Test the
reported sequence, especially `fin nl9a pandol f rabat`, then `ch7al prix dyal
amoxiline`. The latter should confirm the likely medicine and presentation rather
than return the old pharmacy contact. Live research can be diagnosed privately
with `uv run --frozen python scripts/check_agent.py --cnops` and `--pharmacy`.

## Acceptance

- [x] New medicine/price requests do not revive an earlier named contact.
- [x] Labelled fax/sibling contact evidence is excluded from phone actions.
- [x] Ambiguous typo price requests ask a useful source-based clarification.
- [x] Shared-year date intervals and unconfirmed-source status are covered.
- [ ] Live paid OpenRouter quality/account compatibility: requires local key.

# Moroccan pharmacy web routing — 2026-10-27

## Problem and outcome

The reported Panadol response used legitimate saved directory records. That alone
was not proof of a web search. Worse, the following named-contact, location follow-up
and weekly-duty requests were replaced by that same generic Rabat list.

Two concrete causes were found: the only online tool searched public-health domains,
which excluded Moroccan business/duty listings; and the consumer's local-directory
fallback could replace a web-only answer because it had no local `pharmacies` rows.
The spelling `pharmacy` was also missing from literal named-pharmacy extraction.

Named contacts and duty requests now use a separate business-web route before final
response generation. They bypass the generic city-list override. A request for
`pharmacy Al Irfane` uses the explicit city from current/prior user messages; the
following `je suis a rabat madiant al Irafen` retains that named-contact request.
A city is requested if none was supplied. Nearby generic phrases such as
`3tini a9rab pharmacy lya` still request location consent rather than treating `lya`
as a pharmacy name.

## Implemented

- `nlp/pharmacy_web.py`: special-request resolution, Morocco-relative dates/weeks,
  business research invocation, cited phone/city/name checks and duty-date checks.
- `nlp/agent.py`: `search_pharmacy_web` in the shared agent/MCP registry, separate
  Moroccan listing-domain restrictions, correct lookup routing, safe diagnostics,
  and actual-search attempt/success metadata.
- `api/chat_context.py`: named-contact/duty routes are not ordinary saved city queries.
- `nlp/entities.py`: English `pharmacy` is accepted, with generic relative words
  excluded to preserve nearest-pharmacy/location-consent behavior.
- `data/pharmacies/contact_enrichment.json`: one attributed public contact record,
  independently checked on two sites; `.gitignore` explicitly versions it.
- `web/assets/assistant.js`, `web/index.html`: truthful visible search success/failure
  indicator and cache marker `pharmacy-web-v6`. Source links remain text-safe HTTPS links.
- `scripts/check_agent.py --pharmacy`: explicit private-account live research test;
  saved-cache fallback cannot pass it.
- `tests/test_pharmacy_web.py`, DOM journeys: route execution, source checks, failures,
  source provenance and display behavior.

The business search allowlist is Santé Service, Guide Pharmacies, Telecontact,
Medicalis, Med.ma and Sobrus pharmacy listings. Health education keeps its separate
NHS/Ameli/etc. allowlist. Both use the configured private OpenRouter credential and
its documented Exa `web` plugin. `ASSISTANT_WEB_SEARCH=false` disables both web tools.
The stdio MCP adapter exposes these same read-only tools; offline discovery remains
the two local tools.

## Source and validation rules

A contact phone must occur in a cited excerpt containing the distinctive pharmacy
name and requested city. A saved attributed contact can be used if online lookup
fails, explicitly labelled as saved, never a fresh search.

Duty requests compute an explicit interval in Africa/Casablanca time. `cette semaine`
means Monday–Sunday; `semaine prochaine` shifts that interval; `demain` shifts the
requested day. A cited excerpt must identify the city, mention duty, and include a
complete date within the interval. Undated opening hours and other-city/stale pages
are rejected. Phones, complete dates and pharmacy names in the summary must occur
in the matching evidence. Partial coverage is stated. A dated published listing is
not a live guarantee of opening or a verified inventory feed.

The independently retrieved public contact is:

- Pharmacie El Irfane, Campus Madinat Al Irfane, avenue Allal El Fassi, Rabat.
- Published telephone: +212537686317.
- Checked 2026-10-27 at:
  https://www.santeservice.ma/pharmacies-de-garde/rabat/pharmacie-el-irfane.html
  and https://medicalis.ma/fiche/PHARMACIE-ALIRFANE/4883

These were retrieved using web browsing during implementation. This establishes
public listing evidence, not a call to the pharmacy or live OpenRouter authentication.
No current duty schedule was inserted into the cache.

## Verification

```bash
uv run --frozen pytest -q
uv run --frozen ruff check .
uv run --frozen black --check .
node --check web/assets/assistant.js
npm test --prefix web
```

Focused business-web plus existing nearby-consent regressions: **21 passed**, one
existing Starlette/AnyIO deprecation warning, 15.97s. Business-web-only checks also
passed **10 tests**, 6.33s. DOM journeys passed, including the search-success indicator.
Formatting, lint and JavaScript syntax passed.

The full suite initially exposed the `pharmacy lya` extraction regression. Adding the
English spelling initially interpreted `lya` as a name, which broke location consent
and GPS-nearest results. This was fixed with generic-word exclusions and verified by
the existing nearby tests. A new wrong-city test also initially used Casablanca with
a deliberately Rabat-only fixture; it was corrected to test wrong-city evidence with
an actually recognized request city. Final full suite: **706 passed**, one existing dependency warning, **139.59s**.

All OpenRouter HTTP responses in automated tests are mocked. Tests verify that the
research function is invoked with appropriate domains, pharmacy identity and requested
week dates; they do not establish paid account connectivity or real model quality.
No private user key was provided. Excerpts may be absent/incomplete in provider
responses, so not every search can produce a verified contact or duty entry. These
checks do not formally prove every generated summary or identity association correct.

## Acceptance

- [x] Contact and weekly-duty requests actually invoke business web research.
- [x] Web-only answers survive the local-directory presentation layer.
- [x] A location reply retains the preceding named-pharmacy contact request.
- [x] A named contact is never replaced by five unrelated city records.
- [x] Stale, undated and other-city duty evidence is rejected.
- [x] Phone, complete-date and pharmacy-name evidence is checked.
- [x] Saved contact fallback is separately labelled and cannot pass the live check.
- [x] The UI distinguishes successful and unsuccessful attempted searches.
- [x] Existing nearby/location-consent regressions pass.
- [ ] Actual live OpenRouter account search permissions remain untested.

## Windows update

Stop the server, then:

```powershell
git pull origin codex/assistant-answers-voice
uv run --frozen --extra speech python scripts/start_service.py
```

Open http://localhost:8000, Ctrl+F5, jury simulation off. In a second terminal:

```powershell
uv run --frozen python scripts/check_agent.py --pharmacy
```

Expected successful live result: `Agent tool execution and cited web answer: OK`
with actual business-source links. Otherwise safe diagnostic codes explain the
failure category. Keep `.env` and the API key private. The code is on PR #2, not main.

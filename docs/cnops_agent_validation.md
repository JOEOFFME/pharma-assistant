# CNOPS and web-first agent validation — 2026-10-27

## Outcome

The default normal-chat path now uses web research before factual answers instead of
a finite saved migraine-example reply. CNOPS is the preferred source for Moroccan
medicine identification, composition, presentations, PPV and reimbursement bases.
A general public-web tool supports broader questions without a pharmacy-only refusal.
Diagnosis, personal prescribing, dosing and substitution remain excluded.

## Actual source acquisition

The official Morocco Open Data portal identifies CNOPS as publisher of “Réferentiel
des médicaments”. Initial browsing attempts returned 503; the public CKAN API and
the actual workbook then downloaded successfully through the command-line client.
No model generated these records.

- Dataset API: https://data.gov.ma/data/api/3/action/package_show?id=referentiel-des-medicaments
- Resource ID: 094733f5-5434-4163-b837-df0e7b665127
- Original filename: ref-des-medicaments-cnops-2014.xlsx
- Resource last modified: 2017-12-18, retained separately from dataset metadata changes.
- Retrieved: 2026-10-27.
- Original bytes: 530,243.
- SHA-256: e625e9f1db6193cde2db9f39853f2261d3a5c1bae03d1cbc4ac4809013f650d3.
- Actual parsed rows: **5,917**.
- Licence: ODbL, https://opendatacommons.org/licenses/odbl/1-0/.

The original workbook and provenance manifest are versioned under
`data/raw/cnops_snapshot/`. A standard-library OOXML reader preserves source cells.
Prices use decimal cents. EAN, name, DCI, strength/unit, form, pack presentation,
PPV, hospital price, reimbursement base, princeps/generic flag and source rate are
available to tools. Nothing in that historical reference establishes current stock,
current prices, present marketing authorization or an individual's reimbursement.

## Changes

- `data/cnops.py`: immutable cached source reader and literal name/DCI lookup with
  presentation constraints and strength normalization. 1 g and 1000 mg match, while
  unrelated/absent names do not become guessed source entries.
- `scripts/import_cnops.py`: explicit public-source refresh, original byte preservation
  and provenance. No network refresh runs silently at service startup.
- `nlp/agent.py`: CNOPS and general-web tools, a required research-tool first turn in
  default web-first mode, a two-search budget, distinct successful-search counting,
  source IDs and broader question policy. Health and business allowlists remain
  separate. Generic web citations require public HTTPS URLs without credentials.
- `nlp/cnops_policy.py`: money claims about medicines require CNOPS evidence, quoted
  amounts must appear in the cited evidence, historical source facts identify 2014,
  and old prices cannot be represented as current prices.
- `api/data_chat.py`, `api/chat_context.py`: disable the old canned example in default
  mode and preserve successful web answers instead of replacing them with a saved
  city list, including general questions mentioning a city.
- `api/service.py`, `.env.example`: `cnops_web_first_v8` marker and
  `ASSISTANT_WEB_FIRST=true` configuration. Existing private OpenRouter credentials
  remain the only required model/search key.
- `scripts/check_agent.py --cnops`: actual online/cited CNOPS rehearsal. Historical
  local records alone cannot count as a successful live search.
- `web/assets/assistant.js`, `web/index.html`: historical CNOPS provenance label,
  accurate broader-web privacy wording and cache marker `cnops-web-first-v8`.
- `tests/test_cnops_agent.py`, test fixture and setup docs: real snapshot provenance,
  source constraints, new defaults and mocked transport orchestration.

The existing French catalogue remains explicitly a separate matching/reference
source. It is not relabelled CNOPS. Legacy finite-demo behavior remains opt-in with
`ASSISTANT_WEB_FIRST=false`; the existing offline and fictional modes retain their
separate roles. The MCP stdio server shares the expanded six-tool registry when a
key and web access are enabled, otherwise only the two local tools.

## Checks and results

```bash
uv run --frozen pytest -q
uv run --frozen pytest -q tests/test_cnops_agent.py
uv run --frozen ruff check .
uv run --frozen black --check .
node --check web/assets/assistant.js
npm test --prefix web
uv run --frozen python scripts/check_agent.py --help
```

Full suite: **735 passed**, one existing Starlette/AnyIO deprecation warning,
**368.80 seconds**. After the last source-based monetary guard and its added case,
the focused CNOPS suite passed **18 tests**, **42.06 seconds**. The full suite was
not repeated after that last scoped guard; no larger final full-suite total is claimed.
The earlier focused combination passed 64 tests. Ruff/Black, JavaScript syntax and
DOM journeys passed; CLI help advertises both `--pharmacy` and `--cnops`.

Tests verify original bytes and 5,917 real rows, literal missing-name behavior,
1 g/1000 mg matching, basic form constraints, official search domains, honest
historical fallback on web error, required research execution, broad non-pharmacy
questions, safe public links, unsupported/current/undated medicine amounts and
foreign references being rejected as CNOPS evidence. General researched answers
about a city survive the consumer presentation layer.

The test fixture explicitly disables paid/agent/web-first defaults unless a test
enables them. New tests remove/enable the setting to test the actual production
web-first default. Model/web HTTP responses in automated tests are mocked.

## Acceptance and practical limits

- [x] Import actual attributed CNOPS data, with original bytes and source dates.
- [x] Prefer CNOPS for medicine facts and expose PPV/base as separate fields.
- [x] Enable web-first research as the default normal-chat behavior.
- [x] Preserve the OpenRouter main model and existing configurable OpenAI/Claude IDs.
- [x] General questions can research outside the former narrow health-domain list.
- [x] Do not silently use the old canned medicine example as the normal answer.
- [x] Retain research/source attribution and the distinction between old prices and current facts.
- [x] Include private live-check instructions and source licence/provenance.
- [ ] Live OpenRouter authentication, account search permissions and free-form answer
  quality: not tested. No usable key was configured in this build workspace.

A key on the user's Windows machine is not accessible from this workspace. No secret
was displayed or committed, and no paid inference/search was performed. Public CNOPS
source acquisition succeeded independently of OpenRouter. The source workbook is
old, and its last resource update must never be mistaken for a current price date.
A source citation or permitted amount does not prove every model interpretation,
amount label, temporal claim or clinical statement correct. No promise of answering
every possible question correctly is made. Run the live check before the jury.

Current Windows setup and example questions: `docs/cnops_agent_setup.md`.

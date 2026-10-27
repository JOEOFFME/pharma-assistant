# Pharma-AI duty/price response fixes — Validation Report

## Corrected behavior

The request `chno howa l pharmacie li fih la garde had lila` previously caused
`li fih` to be extracted as a pharmacy name, followed by a failed name lookup.
The extractor now treats these relative-clause words as generic request words,
not a pharmacy identity. Duty requests have their own response path rather than
falling through to an ordinary directory search.

Duty replies explain that the current information cannot confirm the requested
live duty schedule. They provide map/contact and location-sharing actions;
without a city or position they ask for the search area. A city already stated
in the request is carried into the map action and selected when it is one of the
supported city anchors. Ordinary opening-hours requests keep the directory path.
No pharmacy is labeled on duty or open merely because it is in the directory.

Price requests now produce one coherent answer: no verified Moroccan price is
available, and a pharmacy can be contacted for the exact presentation. A short
reminder about product details is included only when no dosage/form/quantity was
stated. The generic “Plusieurs présentations…” clarification is not appended to
this unavailable-price response. Map/contact actions make the next step usable.
No price amount or promise that another message will unlock live pricing is made.

The consumer brand is now **Pharma-AI**: page title, header, companion label,
greetings in each supported script, conversation sender name and API-docs title.
Python package names and API paths remain compatible. The supplied robot image
is retained and technical details remain absent from the consumer interface.

## Data limits

This correction does not add a Moroccan price database or a current duty-schedule
provider. The existing medication reference is France-only and has no verified
Moroccan prices; the pharmacy snapshot does not establish live guard schedules.
The assistant states these limits instead of presenting unavailable facts as
search failures or inventing a price/duty pharmacy. Integrating a verified source
is still required to answer those factual questions directly.

## Changed files

- `src/pharma_assistant/nlp/entities.py`: generic relative-clause words excluded
  from `PHARMACY_NAME` candidates.
- `configs/baseline.yaml`: explicit duty-expression vocabulary.
- `src/pharma_assistant/api/answers.py`: dedicated duty/price templates, context
  handling, appropriate next actions and Pharma-AI greetings.
- `src/pharma_assistant/api/app.py`: Pharma-AI OpenAPI title.
- `web/index.html`, `web/assets/assistant.js`: visible brand and conversation
  labels; safe map-city hint handling.
- `tests/test_duty_price_brand.py`: exact reported prompts, entity boundaries,
  time expressions, known location, price specificity, supported greetings and
  full endpoint sequence.
- `tests/test_project_service.py`: current brand expectation.
- `tests/ui_journeys.mjs`: visible brand and map-city hints checked without
  requesting geolocation before explicit consent.
- `README.md`: current product name and limitations.
- This validation report.

## Validation

```bash
uv run --frozen --extra speech ruff check .
uv run --frozen --extra speech black --check .
uv run --frozen --extra speech pytest tests/test_duty_price_brand.py tests/test_assistant_answers.py tests/test_nearby_request_regressions.py -q
uv run --frozen --extra speech pytest -q
node --check web/assets/assistant.js
npm test --prefix web
```

- Focused suite: `33 passed, 1 warning in 16.13s`.
- Full suite: `573 passed, 1 warning in 57.27s`.
- Existing warning: Starlette/AnyIO BlockingPortal deprecation.
- Ruff, Black, JavaScript syntax and consumer DOM journeys: passed.
- No model-performance or recorded-audio accuracy metric is claimed.

## Acceptance checklist

- ✅ The exact on-duty request no longer searches for a pharmacy called `li fih`.
- ✅ `had lila` remains a complete `TIME_REF` span.
- ✅ Duty replies explicitly preserve unverified status, including with location.
- ✅ Price replies avoid repetitive generic clarification and fabricated amounts.
- ✅ Missing product-detail hints are omitted when details are already supplied.
- ✅ Next-step map/location actions are available and city hints are allowlisted.
- ✅ Pharma-AI replaces the former assistant name in consumer markup, translations,
  message labels and greetings.
- ✅ Existing structured API contracts, safety boundaries and robot asset retained.
- ⚠️ Verified Moroccan prices and current duty schedules remain unavailable.
- ⚠️ Real-browser pixel-layout and native Windows microphone QA remain pending.

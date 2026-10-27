# Nearby-request routing and supplied image — Validation Report

## Reported failure and corrected behavior

The supplied screenshot shows `3tini a9rab pharmacy lya` receiving the medical
refusal. Two deterministic routing defects caused this: the location lexicon
missed the Arabizi proximity expression, and the answer presenter treated every
unrecognized request as a request for medical advice. This was a wrong-intent
response, rather than evidence of an LLM inventing pharmacy facts.

The fix adds configurable pharmacy/proximity vocabularies and requires both
signals for these new proximity variants. Thus `a9rab pharmacy` routes to
`pharmacy_info_location`, while `a9rab restaurant` is not silently interpreted as
a pharmacy query. Darija language hints include the reported spelling variants.
A shared clinical-phrase detector distinguishes actual advice requests from
unrecognized text: the latter now receives a domain clarification. Actual
medical requests remain refused, including the medical part of mixed requests.

For the reported request, the actual application returned:

```text
3tini lmdina wla smit pharmacie. Ila bghiti li 9ribin lik,
khtar blassa f la carte lte7t wla sta3mel position dyalek.
```

It also returns two consumer actions: **Chouf pharmacies** and
**Partager position dyali**. The UI opens the map or requests location only
following a user click. Unknown action types are ignored. No IP-based location,
GPS coordinates, pharmacy name, phone, stock, hours or duty status is invented.

With explicitly supplied coordinates and no named pharmacy/city, answers use up
to five saved directory records within 10 km, ordered by straight-line distance.
Calculated distances are shown; missing fields remain unknown. Without a
position, it asks for one instead of claiming to know which pharmacy is nearest.
The map retains its configurable radius. Directory coverage remains incomplete,
so these are nearby mapped entries, not a guarantee of every operating pharmacy.
New conversation clears the position used for chat answers.

## User-supplied image

The right companion panel now uses the owner's supplied pharmacy-robot image
(`image(8).png`), not the earlier generated portrait. Runtime asset:
`web/assets/pharmacy-robot.webp` (1200 × 672; 150,396 bytes).
The image was resized/re-encoded for delivery; its scene and visible watermark
were retained. No content regeneration, watermark removal or stock-site download
was performed. The original upload remains unchanged. The crop positions the
robot within the narrow panel, with a separate mobile crop. The obsolete
`web/assets/companion.webp` runtime asset was removed.

## Files changed in this correction

- `configs/baseline.yaml`: contextual pharmacy/proximity vocabularies.
- `src/pharma_assistant/nlp/intent.py`: contextual nearby routing and shared
  medical-phrase detection.
- `src/pharma_assistant/nlp/langid.py`: additional Darija spelling signals.
- `src/pharma_assistant/api/answers.py`: unknown-request clarification, consumer
  location actions, bounded source-backed nearby records and distances.
- `web/index.html`, `web/assets/assistant.css`: owner-provided image and crop.
- `web/assets/pharmacy-robot.webp`: supplied image optimized for delivery.
- `web/assets/assistant.js`: safe location-action rendering, consent flow and
  clearing shared chat location on reset.
- `tests/test_nearby_request_regressions.py`: exact reported sequence, seven
  spelling variants, restaurant negative case, medical boundary, no-position
  behavior and known-coordinate fixture distances.
- `tests/test_consumer_ui.py`: current runtime-image expectation.
- `tests/ui_journeys.mjs`: location actions require clicks; unknown actions are
  ignored and shared position is passed to map queries.
- `README.md`: current behavior and image provenance.
- This report. Earlier consumer/voice reports describe the preceding checks.

## Validation

```bash
uv run --frozen --extra speech ruff check .
uv run --frozen --extra speech black --check .
uv run --frozen --extra speech pytest -q
node --check web/assets/assistant.js
npm test --prefix web
```

- Full Python suite: `562 passed, 1 warning in 52.23s`.
- Focused routing/answer/baseline suite: `60 passed, 1 warning in 15.09s`.
- Existing warning: Starlette/AnyIO BlockingPortal deprecation.
- Ruff, Black and JavaScript syntax: passed.
- DOM journeys: passed, including map/location/consent and safe rendering.
- Actual application endpoint with the production baseline/catalogue:
  HTTP 200, intent `pharmacy_info_location`, variety `darija_latn`, no pharmacy
  records returned without a position, and both location actions offered.
- The optimized owner image was inspected directly; the visible watermark remains.

## Acceptance and limits

- ✅ Exact reported Darija request no longer receives the medical refusal.
- ✅ Unknown requests get clarification; medical advice is still refused.
- ✅ No nearest-location claim is made without user-provided coordinates.
- ✅ Returned nearby records and distances are grounded in saved data.
- ✅ Location actions require explicit user interaction; unknown actions ignored.
- ✅ Owner's supplied robot image replaces the generated portrait.
- ✅ Full suite, regression checks and UI interaction checks passed.
- ⚠️ This addresses the reported classification error, not every possible Darija
  phrasing. Routing remains heuristic and catalogue/directory coverage limited.
- ⚠️ No new general model-accuracy score or human-audio WER/CER is claimed.
- ⚠️ Real-browser pixel layout and native Windows microphone QA remain pending.
- ⚠️ User-supplied image provenance is recorded, without asserting a stock licence.

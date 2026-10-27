# Pharmacy map — Validation Report

## Feature

The existing demo now includes a Plotly Express/OpenStreetMap map, city anchors,
manual coordinates, optional browser geolocation, and a 0.1–100 km radius control.
A geodesic perimeter and center marker surround the saved pharmacy markers.
A text list shows names, straight-line distances, recorded phones and recorded
hours. Missing data remains unknown; no live stock or duty status is inferred.

`GET /v1/pharmacies/map?lat=34.0209&lon=-6.8416&radius_km=5` returns
all matching saved records, sorted by distance, plus a Plotly figure and source
attribution. There is no nearest-k truncation. Invalid/nonfinite coordinates,
invalid radii, missing databases and configured API keys are handled.
The pinned Plotly JavaScript bundle is served locally; no Google Maps API key
or external JavaScript CDN is required.

## Files changed

- `web/index.html`: controls, interactive map and safely constructed contact list.
- `src/pharma_assistant/data/pharmacies.py`: complete inclusive radius query.
- `src/pharma_assistant/api/pharmacy_map.py`: Plotly Express figure, spherical ring,
  escaped hover content and inspectable JSON coordinates.
- `src/pharma_assistant/api/service.py`: radius-map endpoint and provenance.
- `src/pharma_assistant/api/app.py`: public local Plotly bundle route.
- `pyproject.toml`, `uv.lock`: pinned Plotly 6.3.1 and pandas 2.3.3.
- `tests/test_pharmacy_map.py`: 15 checks covering completeness, boundary inclusion,
  empty results, perimeter accuracy, marker/record alignment, validation, API key,
  local bundle and missing-directory response.
- `.github/workflows/task5-dataset.yml`: map and bundle container smoke checks.
- `README.md`: operation, API example and limitations.
- `docs/pharmacy_map_validation.md`: this report.

## Reproduce

```bash
uv sync --frozen --python 3.11
uv run --frozen ruff check .
uv run --frozen black --check .
uv run --frozen pytest tests/test_pharmacy_map.py -q
uv run --frozen pytest -q
uv run --frozen python scripts/start_service.py
```

Open `http://localhost:8000/` **on the machine running the service**, choose a
center and radius, and click **Afficher les pharmacies**. Restart the service
after updating. For an API-key-protected service, enter the key in the existing
UI key field.

## Actual results

- Ruff and Black: passed.
- JavaScript: inline UI script passed `node --check`.
- Workflow YAML parsed successfully; container smoke now checks the map endpoint.
- Focused pytest: `15 passed, 1 warning in 0.82s`.
- Full pytest: `534 passed, 1 warning in 43.02s`.
- The warning is the existing Starlette/AnyIO BlockingPortal deprecation.
- Real Uvicorn HTTP smoke with the saved source snapshot:

| Request | HTTP | Saved records within 5 km | Farthest distance |
| --- | --- | --- | --- |
| Rabat, 34.0209 / -6.8416 | 200 | 130 | 4.9835 km |
| Casablanca, 33.5731 / -7.5898 | 200 | 274 | 4.9753 km |
| Marrakech, 31.6295 / -7.9811 | 200 | 223 | 4.9829 km |
| Demo HTML | 200 | — | — |
| Local Plotly JavaScript | 200 | — | — |

HTTP smoke assertions checked every returned distance and the one-to-one
alignment between map markers and records. These are snapshot search counts,
not counts of all operating pharmacies or administrative city totals.

## Acceptance checklist and limits

- ✅ Map powered by Plotly Express with OpenStreetMap attribution.
- ✅ Selectable center and radius; all matching saved records returned.
- ✅ Center, perimeter, markers and contact list.
- ✅ Explicit empty/error states; list remains usable if map rendering fails.
- ✅ Radius/API tests, lint, JavaScript syntax and real HTTP smoke.
- ⚠️ Visual browser QA and geolocation permission interaction were not performed:
  this workspace exposes no supported device-facing Python preview URL.
- ⚠️ OpenStreetMap tiles require Internet and map rendering requires browser WebGL.
- ⚠️ City presets are approximate search anchors, not boundary-based region filters.
- ⚠️ Directory coverage is incomplete. Unknown phones/hours remain unknown.
- ⚠️ No live stock, on-duty guarantee, route calculation or medical advice.
- CI container checks are committed; local HTTP checks do not claim a local
  Docker build or a completed remote CI run.

Selected coordinates are sent to this API and the browser requests geographic
tiles from OpenStreetMap. This feature does not persist user locations.
Plotly reference: https://plotly.com/python/tile-map-layers/ .

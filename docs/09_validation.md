# Validation Report — TASK 09: API service

The user authorized self-validation and completion without per-task approval pauses.

## Files created/changed

- `src/pharma_assistant/api/app.py; api/service.py`
- `src/pharma_assistant/__init__.py`
- `tests/test_project_service.py; tests/test_health.py`
- `docs/http_smoke.json`

## Commands

```bash
make demo
uv run --frozen pytest tests/test_project_service.py tests/test_health.py -q
```

## Results and limitations

Mandatory health/version/text/voice/search/nearby routes implemented. Auth, rate limit, invalid input, original evidence, voice conversion and request IDs are tested. A real uvicorn HTTP run returned 200 for health, text, medication search, nearby directory, demo and actual Whisper synthetic-voice analysis. No stub ASR was used in that HTTP smoke. No optional chat endpoint is claimed. Coordinate hints are validated; nearby lookup uses its explicit lat/lon route. Rate limits are process-local.

Shared project checks: Ruff and Black passed. The complete suite passed with **519 tests and one existing Starlette/AnyIO deprecation warning**. Detailed aggregate evidence and unresolved external-input validations are in [the final report](11_validation.md).

- ✅ Required implementation paths and reproducible commands provided.
- ✅ Relevant automated and actual execution evidence recorded.
- ✅ Provenance and observed failures retained; no fabricated metrics.
- ❌ Any unavailable scientific validation described above remains unclaimed.

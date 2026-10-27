# Windows UTF-8 startup fix — Validation Report

## Problem and fix

On Windows with a cp1252 default encoding, first-start pharmacy rebuilding failed
when writing Arabic coverage metrics. The SQLite database had already been built,
but the exception prevented Uvicorn from starting.

Explicit UTF-8 encoding is now used for generated metrics and saved manifest
reads/writes in these startup data tools:

- `src/pharma_assistant/data_tools/clean_pharmacies.py`
- `src/pharma_assistant/data_tools/fetch_pharmacies.py`
- `src/pharma_assistant/data_tools/ingest_medications.py`

The declared encodings of original BDPM source files are unchanged.
`tests/test_windows_encoding.py` simulates a cp1252 default for text file opens,
then rebuilds a small explicitly synthetic Arabic pharmacy fixture. It checks
UTF-8 JSON/CSV output and the SQLite name round-trip. No synthetic fixture is
added to the production directory.

## Validation

```bash
uv run --frozen pytest tests/test_windows_encoding.py -q
uv run --frozen ruff check .
uv run --frozen black --check .
uv run --frozen pytest -q
```

- Regression test: `1 passed in 0.03s`.
- Ruff and Black: passed.
- Full suite: `535 passed, 1 warning in 40.23s` (existing Starlette/AnyIO deprecation).
- ✅ Arabic metrics and manifest file I/O uses explicit UTF-8.
- ✅ Regression simulates the failing platform default without relying on UTF8 mode.
- ✅ Original source file encodings are preserved.
- Limitation: verification ran on Linux with a simulated cp1252 text-file default,
  not on an actual Windows host.

## Immediate workaround for the existing checkout

Run in PowerShell before starting the service:

```powershell
$env:PYTHONUTF8 = "1"
uv run --frozen python scripts/start_service.py
```

This applies to the current terminal and its child processes. Keep the terminal
open and visit `http://localhost:8000/` after Uvicorn reports that it is running.

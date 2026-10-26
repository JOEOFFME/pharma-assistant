# TASK 0 - Validation Report

Date: 2026-10-26. Scope: scaffolding and tooling only.

## Built and files created

Created the complete repository layout requested in AGENTS.md, a typed FastAPI
application factory, the GET /health route, pinned direct dependencies plus a
hash-bearing transitive uv.lock, Make targets, pre-commit hooks, environment
example, setup documentation and three pytest contract tests.

All files below are new. Package directories reserved for later tasks contain
only __init__.py; data and other reserved directories contain .gitkeep.
No source attachment was modified.

```text
pharma-assistant/
├── .env.example
├── .gitignore
├── .pre-commit-config.yaml
├── .python-version
├── AGENTS.md
├── Makefile
├── README.md
├── configs/
│   └── .gitkeep
├── data/
│   ├── audio/
│   │   └── .gitkeep
│   ├── medications/
│   │   └── .gitkeep
│   ├── nlu/
│   │   └── .gitkeep
│   ├── pharmacies/
│   │   └── .gitkeep
│   ├── processed/
│   │   └── .gitkeep
│   └── raw/
│       └── .gitkeep
├── docker/
│   └── .gitkeep
├── docs/
│   ├── .gitkeep
│   └── 00_validation.md
├── notebooks/
│   └── .gitkeep
├── pyproject.toml
├── src/
│   └── pharma_assistant/
│       ├── __init__.py
│       ├── api/
│       │   ├── __init__.py
│       │   ├── app.py
│       │   └── health.py
│       ├── asr/
│       │   └── __init__.py
│       ├── data_tools/
│       │   └── __init__.py
│       ├── eval/
│       │   └── __init__.py
│       ├── matching/
│       │   └── __init__.py
│       ├── nlp/
│       │   └── __init__.py
│       └── pipeline/
│           └── __init__.py
├── tests/
│   └── test_health.py
└── uv.lock
```

## Exact commands to reproduce

Prerequisites: Git, GNU Make, uv and Python 3.11. Tested with uv 0.13.4,
CPython 3.11.17 on Linux. On Windows use WSL2/Ubuntu.

```bash
cd pharma-assistant
uv python install 3.11   # only if Python 3.11 is absent
make install
make lint
make test
make run
```

In a second terminal:

```bash
curl --fail http://127.0.0.1:8000/health
curl --fail http://127.0.0.1:8000/docs
```

Expected: health body {"status":"ok"}, HTTP 200; docs returns HTML, HTTP 200.
Stop the foreground server with Ctrl+C.

Optional hook installation and verification:

```bash
make hooks
uv run --frozen pre-commit run --all-files
```

## Commands actually executed and outcomes

- uv python install 3.11: installed CPython 3.11.17.
- uv lock: generated lockfile, resolved 34 packages (including the local project).
- make install: created an isolated environment and installed the frozen lockfile.
- make lint: Ruff passed; Black reported 11 files unchanged.
- make test: 3 tests passed; one upstream deprecation warning (see limitations).
- uv run --frozen pre-commit run --all-files: Ruff Passed, Black Passed.
- git commit -m 'feat(task0): scaffold FastAPI service and reproducible tooling':
  one logical TASK 0 commit (report included by amendment).
- git clone --no-hardlinks . ../tmp/task0-clean-clone: independent fresh checkout.
- make -C ../tmp/task0-clean-clone install: passed, fresh virtual environment.
- make -C ../tmp/task0-clean-clone lint: passed.
- make -C ../tmp/task0-clean-clone test: passed (output excerpt below).
- make run in the fresh clone, followed by real HTTP requests using Python's
  urllib: /health returned HTTP 200 and exactly {"status":"ok"}; /docs returned
  HTTP 200. The temporary server was stopped after the check.

```text
platform linux -- Python 3.11.17, pytest-8.3.4
collected 3 items
tests/test_health.py ... [100%]
3 passed, 1 warning in 0.51s

ruff........................................................Passed
black.......................................................Passed
GET /health -> HTTP 200 {"status":"ok"}
GET /docs -> HTTP 200
```

Tests cover the exact health body and disclaimer header, the typed response in
OpenAPI, and HTTP 404 for an analysis endpoint not implemented in this task.
No NLU, speech, medical matching or model evaluation numbers are claimed.

## Acceptance checklist

- ✅ Repository layout matches the requested TASK 0 structure.
- ✅ Pinned dependency management and frozen transitive lockfile.
- ✅ Make install, lint, test and run targets work.
- ✅ Fresh Git clone installs, passes tests and serves the health route.
- ✅ GET /health returns exactly {"status":"ok"}.
- ✅ README contains prerequisites, setup, execution and expected output.
- ✅ Pre-commit configuration passes on all tracked Python files.
- ✅ Python 3.11, type hints and Pydantic v2 health response.
- ✅ One logical feat(task0) commit.
- ✅ No fabricated data, secrets or machine-specific paths in source/config.

## Known limitations and decisions

- This is TASK 0 only. No NLU, ASR, data ingestion, models or demo UI yet.
- Health is liveness, not database/model readiness. To preserve its exact required
  JSON body, the medical disclaimer is exposed as X-Medical-Disclaimer; future
  analysis responses must use the specified JSON disclaimer field.
- Pytest emits one upstream Starlette/AnyIO DeprecationWarning about
  anyio.abc.BlockingPortal. It does not fail the tests and is not suppressed.
- Fresh dependency/interpreter downloads require Internet access. This is not
  an offline bundle; it does not include a virtual environment or dependencies.
- The seed is configurable as PYTHONHASHSEED=42; no stochastic processing exists
  in this task. Future model training will require additional library seeds.
- The Makefile workflow was tested on Linux, not native Windows/macOS.

## Validation boundary

TASK 1 has not started. Next required user message: VALIDATED TASK 0.

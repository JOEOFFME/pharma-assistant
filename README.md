# Pharma Assistant - Challenge 1

Arabic, Moroccan Darija (Arabic/Latin script), French, and code-mixed
patient-pharmacy assistance prototype.

## Current scope: TASK 0

Repository scaffolding and an operational FastAPI health endpoint. NLU, speech,
medication data, pharmacy data and evaluation are later tasks and are not implemented.
No medical diagnosis, dosage recommendations or substitution advice is provided.

## Prerequisites

- Python 3.11 (the project excludes other minor versions).
- `uv` package manager, GNU Make and Git on PATH.
- Internet access for the first interpreter/dependency installation.
- On Windows, use WSL2 (Ubuntu) for the Make commands below.

The tested uv version is recorded in `docs/00_validation.md`. `uv.lock` pins
transitive dependencies as well as the exact direct versions in `pyproject.toml`.
If Python 3.11 is missing, `uv python install 3.11` can provision it.

## Setup and run

```bash
cd pharma-assistant
make install
make lint
make test
make run
```

`make install` creates `.venv`, installs the frozen lockfile and creates `.env`
from `.env.example` if absent. Activation is unnecessary. Edit `.env` to change
HOST, PORT or LOG_LEVEL. These are Make-compatible environment assignments, not
shell commands. The server runs in the foreground; stop it with Ctrl+C.

In a second terminal:

```bash
curl --fail http://127.0.0.1:8000/health
```

Expected body: `{"status":"ok"}` (HTTP 200). Interactive API docs:
<http://127.0.0.1:8000/docs>.

The health response preserves the exact acceptance contract. Its medical
disclaimer is in the `X-Medical-Disclaimer` header; future analysis responses
will carry the required JSON `disclaimer` field. Health means process liveness,
not readiness of a database, model or external service.

## Developer checks

```bash
make format                 # apply formatting and safe lint fixes
make lint                   # Ruff + Black, read-only
make test                   # pytest
make hooks                  # opt-in installation of local pre-commit hooks
uv run --frozen pre-commit run --all-files
```

Hooks use the same locked tools as Make. No dependencies or model weights are
downloaded during app import. The reproducibility seed is `PYTHONHASHSEED=42`
in `.env.example`; no stochastic model is used in TASK 0.

## Structure

- `configs/`: model and pipeline YAML configuration in later tasks.
- `data/{raw,processed,medications,pharmacies,nlu,audio}/`: empty data directories.
- `src/pharma_assistant/api/`: application factory and health route.
- `src/pharma_assistant/{asr,nlp,matching,pipeline,data_tools,eval}/`: package skeletons.
- `tests/`: HTTP and OpenAPI contract tests.
- `docs/`: validation reports and, later, study/architecture/evaluation.
- `notebooks/`, `docker/`: reserved for later tasks.

Data directories are intentionally empty. Do not commit personal health data,
credentials, local datasets, generated reports, models or `.env` files.
Follow `AGENTS.md`: execute tasks in order, with user validation between them.

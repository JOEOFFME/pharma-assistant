# Pharma Assistant - Challenge 1

Arabic, Moroccan Darija (Arabic/Latin script), French, and code-mixed
patient-pharmacy assistance prototype.

## Current scope: TASK 0-5 preparation

Repository scaffolding and an operational FastAPI health endpoint, plus the
[TASK 1 problem study](docs/01_problem_study.md) and
[TASK 1 validation report](docs/01_validation.md), the
[TASK 2 NLU specification](docs/02_nlu_spec.md), typed response models and
[200 annotation examples](docs/examples/nlu_annotation_examples.md).
The examples are authored and unreviewed, not a gold dataset. TASK 3 adds a real
[OSM pharmacy directory](data/pharmacies/README.md), SQLite queries and a generated
[coverage report](docs/data_pharmacies.md). TASK 4 adds a
[French BDPM reference fallback](data/medications/README.md), medication matching
and a 50-query review mini-set. NLU inference, speech and learned-model
evaluation are later tasks and are not implemented.
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

Versioned public source snapshots and annotated development data are included.
Do not commit personal health data, credentials, models or `.env` files.
Follow `AGENTS.md`: execute tasks in order, with user validation between them.

## NLU response contract (TASK 2)

```bash
make schema
uv run --frozen pytest tests/test_schemas.py -v
```

The JSON Schema is generated from `AnalysisResponse` in
`src/pharma_assistant/api/schemas.py`. Pydantic also enforces cross-field rules
that JSON Schema alone does not express. See
[the specification](docs/02_nlu_spec.md) and
[TASK 2 validation report](docs/02_validation.md). These define output contracts;
analysis endpoints are not implemented yet.

## Pharmacy directory (TASK 3)

```bash
make pharmacies             # build CSV, SQLite, report from committed OSM bytes
```

The directory is a snapshot from OpenStreetMap, not a live stock or garde feed.
© OpenStreetMap contributors; source and derived data are under
[ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/). See
[data instructions](data/pharmacies/README.md),
[coverage](docs/data_pharmacies.md) and
[TASK 3 validation report](docs/03_validation.md).

## Medication reference (TASK 4)

```bash
make medications            # offline catalogue build and 50-query evaluation
```

France BDPM is used as an explicitly labelled open fallback because the Moroccan
portal could not be downloaded. It provides no Moroccan availability or PPV.
Generated Arabic/typo aliases and the query mini-set require review. See
[the reference report](docs/data_medications.md) and
[TASK 4 validation](docs/04_validation.md).

## NLU dataset preparation (TASK 5)

```bash
make dataset
```

Inputs include 200 assistant-authored build seeds and 100 development-only
assistant seeds. Augmentation is synthetic and training-only; related template
families stay together. No development seed is eligible for final evaluation.
`data/nlu/gold_human.jsonl` is an empty template for separately collected human
annotations. The previous candidate-to-gold promotion mechanism is removed.
See [dataset instructions](data/nlu/README.md),
[human annotation guide](docs/gold_annotation_howto.md), and
[TASK 5 correction validation](docs/05_validation.md).

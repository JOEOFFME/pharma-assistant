UV ?= uv
-include .env
export
HOST ?= 127.0.0.1
PORT ?= 8000
LOG_LEVEL ?= info
PYTHONHASHSEED ?= 42

.PHONY: install lint test run format hooks schema
install:
	$(UV) sync --frozen --python 3.11
	@test -f .env || cp .env.example .env

lint:
	$(UV) run --frozen ruff check .
	$(UV) run --frozen black --check .

test:
	$(UV) run --frozen pytest

run:
	$(UV) run --frozen uvicorn pharma_assistant.api.app:app --host $(HOST) --port $(PORT) --log-level $(LOG_LEVEL)

format:
	$(UV) run --frozen ruff check --fix .
	$(UV) run --frozen black .

hooks:
	$(UV) run --frozen pre-commit install

schema:
	$(UV) run --frozen python scripts/export_schema.py

.PHONY: pharmacies fetch-pharmacies
pharmacies:
	$(UV) run --frozen python -m pharma_assistant.data_tools.clean_pharmacies

fetch-pharmacies:
	$(UV) run --frozen python -m pharma_assistant.data_tools.fetch_pharmacies

.PHONY: medications fetch-medications
medications:
	$(UV) run --frozen python -m pharma_assistant.data_tools.ingest_medications
	$(UV) run --frozen python -m pharma_assistant.eval.medication_resolution

fetch-medications:
	$(UV) run --frozen python -m pharma_assistant.data_tools.ingest_medications --fetch

.PHONY: dataset gold-lock
dataset:
	$(UV) run --frozen python scripts/dataset_stats.py

gold-lock:
	$(UV) run --frozen python scripts/lock_gold.py

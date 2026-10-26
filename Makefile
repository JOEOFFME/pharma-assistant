UV ?= uv
-include .env
export
HOST ?= 127.0.0.1
PORT ?= 8000
LOG_LEVEL ?= info
PYTHONHASHSEED ?= 42

.PHONY: install lint test run format hooks
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

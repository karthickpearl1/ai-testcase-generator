PYTHON ?= python3
VENV   ?= .venv
BIN     = $(VENV)/bin

.PHONY: install lint format test generate run gate demo-noisy demo-api sample typecheck clean

install:  ## create a virtualenv and install with dev tools
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -e ".[dev]"

lint:
	$(BIN)/ruff check .
	$(BIN)/ruff format --check .

format:
	$(BIN)/ruff format .
	$(BIN)/ruff check --fix .

test:
	$(BIN)/pytest

generate:  ## generate test cases, code and exports only (no execution)
	$(BIN)/testgen generate -o out/latest

run:  ## generate, execute against the demo API and report
	$(BIN)/testgen run -o out/latest

gate:  ## as run, and fail if the quality gate fails
	$(BIN)/testgen run --gate -o out/latest

demo-noisy:  ## show the gate rejecting a noisy model with weak assertions
	-$(BIN)/testgen run -c configs/noisy-model.yaml -o out/noisy-model --gate

demo-api:  ## start the bundled Bookshop API on http://127.0.0.1:8000
	$(BIN)/testgen demo-api --port 8000

sample:  ## regenerate the committed sample-output/ (review the diff before committing)
	rm -rf sample-output
	$(BIN)/testgen generate -o sample-output

typecheck:  ## type-check the generated Playwright skeletons (needs Node 20+)
	cd typecheck && npm ci && npm run typecheck

clean:
	rm -rf out out-* .pytest_cache .ruff_cache .coverage coverage.xml htmlcov

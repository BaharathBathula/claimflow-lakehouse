.PHONY: install demo generate ingest transform test lint api dashboard clean kafka-up kafka-down

PYTHON ?= python
DBT = $(PYTHON) scripts/run_dbt_cli.py

install:
	$(PYTHON) -m pip install -e ".[dev]"

demo:
	$(PYTHON) -m claimflow.demo --events 5000

generate:
	claimflow generate --events 5000 --output data/inbox/events.ndjson

ingest:
	claimflow ingest-file data/inbox/events.ndjson

transform:
	$(DBT) run --project-dir transform --profiles-dir transform
	$(DBT) test --project-dir transform --profiles-dir transform

test:
	$(PYTHON) -m pytest --cov=claimflow --cov-report=term-missing

lint:
	$(PYTHON) -m ruff check src tests

api:
	$(PYTHON) -m uvicorn claimflow.api:app --host 0.0.0.0 --port 8000 --reload

dashboard:
	$(PYTHON) -m streamlit run src/claimflow/dashboard.py --server.address 0.0.0.0

kafka-up:
	docker compose up -d redpanda console

kafka-down:
	docker compose down

clean:
	claimflow reset --yes

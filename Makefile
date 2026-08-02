.PHONY: install install-backend install-frontend init-db ingest-m2 ingest-all ingest-watchlist backfill-composite scheduler scheduler-once dev-api dev-web

VENV ?= /home/murali/sandbox/envs/tideenv
PY   := $(VENV)/bin/python
PORT ?= 8765

install: install-backend install-frontend

install-backend:
	$(VENV)/bin/pip install -e backend

install-frontend:
	cd frontend && npm install

init-db:
	cd backend && $(PY) -m tide.db init

ingest-m2:
	cd backend && $(PY) -m tide.ingest.cli run --metric m2

ingest-all:
	cd backend && $(PY) -m tide.ingest.cli run --all

ingest-watchlist:
	cd backend && $(PY) -m tide.ingest.cli watchlist

backfill-composite:
	cd backend && $(PY) -m tide.ingest.cli backfill-composite

scheduler:
	cd backend && $(PY) -m tide.ingest.cli scheduler

scheduler-once:
	cd backend && $(PY) -m tide.ingest.cli scheduler --fire-once

dev-api:
	cd backend && $(VENV)/bin/uvicorn tide.api.app:app --reload --port $(PORT)

dev-web:
	cd frontend && npm run dev

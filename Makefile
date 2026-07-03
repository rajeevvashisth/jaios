.PHONY: up down logs backend-shell migrate revision test lint fmt typecheck backend-dev frontend-dev

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f

backend-shell:
	docker compose exec backend bash

migrate:
	docker compose exec backend alembic upgrade head

revision:
	docker compose exec backend alembic revision --autogenerate -m "$(m)"

# --- Run outside Docker, against a locally running Postgres ---

backend-dev:
	cd backend && .venv/bin/uvicorn app.main:app --reload

frontend-dev:
	cd frontend && npm run dev

test:
	cd backend && .venv/bin/python -m pytest

lint:
	cd backend && .venv/bin/python -m ruff check app tests

fmt:
	cd backend && .venv/bin/python -m black app tests && .venv/bin/python -m ruff check --fix app tests

typecheck:
	cd backend && .venv/bin/python -m mypy app

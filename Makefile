# SamConsultingFirm Ticketing – common commands
COMPOSE = docker compose -f deploy/docker-compose.yml

.PHONY: up down test lint migrate logs build

up:
	$(COMPOSE) up --build -d

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f

test:
	python -m pytest -v

lint:
	ruff check backend/
	ruff format --check backend/

format:
	ruff check --fix backend/
	ruff format backend/

migrate:
	cd backend && alembic upgrade head

migrate-new:
	cd backend && alembic revision --autogenerate -m "$(msg)"

frontend-check:
	cd frontend && npx svelte-check --threshold warning

build:
	$(COMPOSE) build

.PHONY: help dev build stop clean test lint typecheck migrate seed evaluation-gate

# Default target
help:
	@echo "AgentGuard Development Commands"
	@echo "================================"
	@echo "make dev          - Start all services in development mode"
	@echo "make build        - Build all Docker images"
	@echo "make stop         - Stop all services"
	@echo "make clean        - Stop services and remove volumes"
	@echo "make test         - Run all tests"
	@echo "make lint         - Run linters"
	@echo "make typecheck    - Run type checking"
	@echo "make migrate      - Run database migrations"
	@echo "make seed         - Seed database with demo data"
	@echo "make backend-shell - Open shell in backend container"
	@echo "make frontend-shell - Open shell in frontend container"
	@echo "make logs         - Show logs from all services"
	@echo "make test-backend - Run backend tests"
	@echo "make test-frontend - Run frontend tests"
	@echo "make evaluation-gate BASELINE=... CURRENT=... - Fail on reliability regression"

# Development
dev:
	docker-compose up -d
	@echo "Services starting..."
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:3000"
	@echo "API Docs: http://localhost:8000/docs"

build:
	docker-compose build

stop:
	docker-compose down

clean:
	docker-compose down -v
	@echo "Cleaned up containers and volumes"

# Testing
test: test-backend test-frontend

test-backend:
	cd Backend && pytest

test-frontend:
	cd Frontend && npm test

test-integration:
	cd Backend && pytest tests/integration

test-contract:
	cd Backend && pytest tests/contract

test-coverage:
	cd Backend && pytest --cov=core --cov=modules --cov=shared --cov-report=html

# Reliability release gate
evaluation-gate:
	@test -n "$(BASELINE)" -a -n "$(CURRENT)" || (echo "Usage: make evaluation-gate BASELINE=baseline.json CURRENT=current.json" && exit 2)
	cd Backend && python scripts/evaluation_gate.py --baseline "../$(BASELINE)" --current "../$(CURRENT)"

# Code Quality
lint: lint-backend lint-frontend

lint-backend:
	cd Backend && ruff check . && black --check .

lint-frontend:
	cd Frontend && npm run lint

typecheck: typecheck-backend typecheck-frontend

typecheck-backend:
	cd Backend && mypy core modules shared

typecheck-frontend:
	cd Frontend && npm run type-check

format:
	cd Backend && black . && ruff check --fix .
	cd Frontend && npm run lint -- --fix

# Database
migrate:
	docker-compose exec backend alembic upgrade head

migrate-create:
	@read -p "Enter migration message: " msg; \
	docker-compose exec backend alembic revision --autogenerate -m "$$msg"

migrate-down:
	docker-compose exec backend alembic downgrade -1

seed:
	docker-compose exec backend python scripts/seed_data.py

# Shells
backend-shell:
	docker-compose exec backend /bin/bash

frontend-shell:
	docker-compose exec frontend /bin/sh

db-shell:
	docker-compose exec postgres psql -U agentguard -d agentguard

# Logs
logs:
	docker-compose logs -f

logs-backend:
	docker-compose logs -f backend

logs-frontend:
	docker-compose logs -f frontend

# Installation
install-backend:
	cd Backend && pip install -r requirements-dev.txt

install-frontend:
	cd Frontend && npm install

install: install-backend install-frontend

# CI/CD
ci: lint typecheck test build
	@echo "CI checks passed!"

# Reset
reset: clean
	@echo "Removing node_modules and Python cache..."
	rm -rf Frontend/node_modules
	rm -rf Backend/__pycache__
	rm -rf Backend/.pytest_cache
	rm -rf Backend/.mypy_cache
	find Backend -type d -name __pycache__ -exec rm -rf {} +
	@echo "Reset complete. Run 'make install' to reinstall dependencies."

.PHONY: help install install-dev update sync clean
.PHONY: serve dev api chat
.PHONY: test test-unit test-integration test-cov test-watch
.PHONY: lint lint-fix format format-check type-check
.PHONY: security bandit
.PHONY: db-migrate db-upgrade db-downgrade db-revision
.PHONY: list-skills validate-skill promote-skill

# Default target
.DEFAULT_GOAL := help

# Variables
PYTHON := uv run python
PYTEST := uv run pytest
RUFF := uv run ruff
BANDIT := uv run bandit
ALEMBIC := uv run alembic
SKILL_FLEET := uv run skill-fleet

# Help target - lists all available commands
help:
	@echo "Skill Fleet - Available Commands:"
	@echo ""
	@echo "Setup:"
	@echo "  make install      Install production dependencies"
	@echo "  make install-dev  Install with dev dependencies"
	@echo "  make update       Update all dependencies"
	@echo "  make sync         Sync dependencies with lock file"
	@echo "  make clean        Clean cache and temp files"
	@echo ""
	@echo "Development:"
	@echo "  make serve        Start production API server"
	@echo "  make dev          Start API server with auto-reload"
	@echo "  make api          Start uvicorn directly (alias)"
	@echo "  make chat         Start interactive skill creation chat"
	@echo ""
	@echo "Testing:"
	@echo "  make test         Run all tests"
	@echo "  make test-unit    Run unit tests only"
	@echo "  make test-integration  Run integration tests only"
	@echo "  make test-cov     Run tests with coverage report"
	@echo "  make test-watch   Run tests in watch mode"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint         Run linter (ruff check)"
	@echo "  make lint-fix     Run linter with auto-fix"
	@echo "  make format       Format code (ruff format)"
	@echo "  make format-check Check formatting without changes"
	@echo "  make type-check   Run type checker (ty)"
	@echo "  make security     Run security checks (bandit)"
	@echo ""
	@echo "Database:"
	@echo "  make db-migrate   Run pending migrations"
	@echo "  make db-revision  Create new migration (use NAME=...)"
	@echo ""
	@echo "CLI Shortcuts:"
	@echo "  make list-skills  List all skills"
	@echo "  make validate-skill FILE=path/to/skill.yaml"
	@echo "  make promote-skill ID=skill-id"

# Setup targets
install:
	uv sync

install-dev:
	uv sync --group dev

update:
	uv lock --upgrade

sync:
	uv sync --locked

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name .ruff_cache -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .coverage htmlcov/

# Development targets
serve:
	$(SKILL_FLEET) serve

dev:
	uvicorn skill_fleet.api.main:app --reload

api:
	$(SKILL_FLEET) serve

chat:
	$(SKILL_FLEET) chat

# Testing targets
test:
	$(PYTEST)

test-unit:
	$(PYTEST) tests/unit/

test-integration:
	$(PYTEST) tests/integration/

test-cov:
	$(PYTEST) --cov=skill_fleet --cov-report=term-missing --cov-report=html

test-watch:
	$(PYTEST) -f

# Code quality targets
lint:
	$(RUFF) check .

lint-fix:
	$(RUFF) check --fix .

format:
	$(RUFF) format .

format-check:
	$(RUFF) format --check .

type-check:
	uv run ty check

security:
	$(BANDIT) -c pyproject.toml -r src/

# Database targets
db-migrate:
	$(ALEMBIC) upgrade head

db-upgrade:
	$(ALEMBIC) upgrade +1

db-downgrade:
	$(ALEMBIC) downgrade -1

db-revision:
	@test -n "$(NAME)" || (echo "Usage: make db-revision NAME=description" && exit 1)
	$(ALEMBIC) revision --autogenerate -m "$(NAME)"

# CLI shortcuts
list-skills:
	$(SKILL_FLEET) list

validate-skill:
	@test -n "$(FILE)" || (echo "Usage: make validate-skill FILE=path/to/skill.yaml" && exit 1)
	$(SKILL_FLEET) validate $(FILE)

promote-skill:
	@test -n "$(ID)" || (echo "Usage: make promote-skill ID=skill-id" && exit 1)
	$(SKILL_FLEET) promote $(ID)

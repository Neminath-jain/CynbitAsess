# BitElevate PR Review Copilot - Command Automation
.PHONY: test lint run-api run-web audit help

VENV_BIN := $(shell if [ -d ".venv/bin" ]; then echo ".venv/bin/"; elif [ -d ".venv/Scripts" ]; then echo ".venv/Scripts/"; else echo ""; fi)
PYTHON ?= $(VENV_BIN)python
PYTEST ?= $(VENV_BIN)pytest
RUFF ?= $(VENV_BIN)ruff
MYPY ?= $(VENV_BIN)mypy
BANDIT ?= $(VENV_BIN)bandit
PIPAUDIT ?= $(VENV_BIN)pip-audit
UVICORN ?= $(VENV_BIN)uvicorn

help:
	@echo "Available commands:"
	@echo "  make test      - Run all backend unit & integration tests"
	@echo "  make lint      - Run ruff linter and mypy type checks"
	@echo "  make run-api   - Launch FastAPI backend server with hot-reload"
	@echo "  make run-web   - Launch React frontend dev server (UI HOLD)"
	@echo "  make audit     - Run bandit security scan and dependency vulnerability audit"

test:
	cd backend && $(PYTEST) tests/ -v

lint:
	cd backend && $(RUFF) check app/
	cd backend && $(MYPY) app/

run-api:
	cd backend && $(UVICORN) app.main:app --host 0.0.0.0 --port 8000 --reload

run-web:
	@echo "[UI HOLD] Frontend development is currently on hold pending UI design direction."
	@echo "Target stack: React 18 + Vite + TypeScript + TanStack Query."

audit:
	cd backend && $(BANDIT) -r app/ -ll
	cd backend && $(PIPAUDIT)

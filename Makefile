# BitElevate PR Review Copilot - Command Automation
.PHONY: test lint run-api run-web audit help

PYTHON ?= python

help:
	@echo "Available commands:"
	@echo "  make test      - Run all backend unit & integration tests"
	@echo "  make lint      - Run ruff linter and mypy type checks"
	@echo "  make run-api   - Launch FastAPI backend server with hot-reload"
	@echo "  make run-web   - Launch React frontend dev server (UI HOLD)"
	@echo "  make audit     - Run bandit security scan and dependency vulnerability audit"

test:
	cd backend && $(PYTHON) -m pytest tests/ -v

lint:
	cd backend && $(PYTHON) -m ruff check app/
	cd backend && $(PYTHON) -m mypy app/

run-api:
	cd backend && $(PYTHON) -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

run-web:
	@echo "[UI HOLD] Frontend development is currently on hold pending UI design direction."
	@echo "Target stack: React 18 + Vite + TypeScript + TanStack Query."

audit:
	cd backend && $(PYTHON) -m bandit -r app/ -ll
	cd backend && $(PYTHON) -m pip_audit

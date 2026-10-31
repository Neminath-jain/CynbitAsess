# PowerShell script equivalent for make targets on Windows
param (
    [Parameter(Mandatory=$true, Position=0)]
    [ValidateSet("test", "lint", "run-api", "run-web", "audit", "help")]
    [string]$Target
)

$ErrorActionPreference = "Stop"

switch ($Target) {
    "test" {
        Write-Host "Running backend test suite..." -ForegroundColor Cyan
        Push-Location backend
        try {
            python -m pytest tests/ -v
        } finally {
            Pop-Location
        }
    }
    "lint" {
        Write-Host "Running ruff check and mypy type checks..." -ForegroundColor Cyan
        Push-Location backend
        try {
            python -m ruff check app/
            python -m mypy app/
        } finally {
            Pop-Location
        }
    }
    "run-api" {
        Write-Host "Starting FastAPI server on http://localhost:8000..." -ForegroundColor Cyan
        Push-Location backend
        try {
            python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
        } finally {
            Pop-Location
        }
    }
    "run-web" {
        Write-Host "[UI HOLD] Frontend development is on hold pending UI design direction." -ForegroundColor Yellow
        Write-Host "Target stack: React 18 + Vite + TypeScript + TanStack Query." -ForegroundColor Yellow
    }
    "audit" {
        Write-Host "Running bandit security scan and pip-audit..." -ForegroundColor Cyan
        Push-Location backend
        try {
            python -m bandit -r app/ -ll
            python -m pip_audit
        } finally {
            Pop-Location
        }
    }
    "help" {
        Write-Host "Available targets: test, lint, run-api, run-web, audit" -ForegroundColor Cyan
    }
}

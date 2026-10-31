# PowerShell script equivalent for make targets on Windows
param (
    [Parameter(Mandatory=$true, Position=0)]
    [ValidateSet("test", "lint", "run-api", "run-web", "audit", "help")]
    [string]$Target
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"

if (Test-Path $VenvPython) {
    $PythonCmd = $VenvPython
    $PytestCmd = Join-Path $Root ".venv\Scripts\pytest.exe"
    $RuffCmd = Join-Path $Root ".venv\Scripts\ruff.exe"
    $MypyCmd = Join-Path $Root ".venv\Scripts\mypy.exe"
    $BanditCmd = Join-Path $Root ".venv\Scripts\bandit.exe"
    $PipAuditCmd = Join-Path $Root ".venv\Scripts\pip-audit.exe"
    $UvicornCmd = Join-Path $Root ".venv\Scripts\uvicorn.exe"
} else {
    $PythonCmd = "python"
    $PytestCmd = "pytest"
    $RuffCmd = "ruff"
    $MypyCmd = "mypy"
    $BanditCmd = "bandit"
    $PipAuditCmd = "pip-audit"
    $UvicornCmd = "uvicorn"
}

switch ($Target) {
    "test" {
        Write-Host "Running backend test suite..." -ForegroundColor Cyan
        Push-Location "$Root\backend"
        try {
            & $PytestCmd tests/ -v
        } finally {
            Pop-Location
        }
    }
    "lint" {
        Write-Host "Running ruff check and mypy type checks..." -ForegroundColor Cyan
        Push-Location "$Root\backend"
        try {
            Write-Host "--> Running ruff check app/..." -ForegroundColor Yellow
            & $RuffCmd check app/
            Write-Host "--> Running mypy app/..." -ForegroundColor Yellow
            & $MypyCmd app/
        } finally {
            Pop-Location
        }
    }
    "run-api" {
        Write-Host "Starting FastAPI server on http://localhost:8000..." -ForegroundColor Cyan
        Push-Location "$Root\backend"
        try {
            & $UvicornCmd app.main:app --host 0.0.0.0 --port 8000 --reload
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
        Push-Location "$Root\backend"
        try {
            Write-Host "--> Running bandit -r app/ -ll..." -ForegroundColor Yellow
            & $BanditCmd -r app/ -ll
            Write-Host "--> Running pip-audit..." -ForegroundColor Yellow
            & $PipAuditCmd
        } finally {
            Pop-Location
        }
    }
    "help" {
        Write-Host "Available targets: test, lint, run-api, run-web, audit" -ForegroundColor Cyan
    }
}

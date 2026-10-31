# Master Implementation Plan (PLAN.md)
## BitElevate PR Review Copilot

**Organization**: Cynbit Technologies  
**Approach**: Small, test-driven steps in Conventional Commits; Phase-based execution with stopping gates.  
**Fixed Stack**: Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2, SQLite, httpx, pytest, ruff, mypy, bandit, pip-audit, uv; React 18, Vite, TS (UI HOLD).  

---

## Phase Overview & Status

| Phase | Description | Status | Gate Condition |
|---|---|---|---|
| **Phase A** | Planning & Foundation | **COMPLETED** | Layout scaffolded, docs aligned, make commands working, Phase A report generated |
| **Phase B** | Backend Core | **UP NEXT** | Sanitizer, LLM client, AI analysis service, DB repository, all tests passing |
| **Phase C** | Backend Completion | PENDING | Mentor workflow, GitHub dispatcher, FastAPI JSON routes, safe error handlers |
| **Phase D** | Frontend | **BLOCKED (UI HOLD)** | Blocked until user sends UI design direction; backend built headlessly |
| **Phase E** | Quality & Hardening | PENDING | Prompt injection benchmarks in `evals/`, bandit, pip-audit, strict mypy, ruff |
| **Phase F** | Deliverables | PENDING | Walkthrough, final reports, docker-compose deployment verification |

---

## Detailed Phase Breakdown

### Phase A: Planning & Foundation (COMPLETED)
- **Task A.1**: Realign documentation (`docs/PRD.md`, `docs/SRS.md`, `docs/architecture.md`, `docs/PLAN.md`).
- **Task A.2**: Scaffold repository layout (`backend/`, `frontend/`, `evals/`, `docs/reports/`, `.github/workflows/`, `docker-compose.yml`, `Makefile`, `run.ps1`).
- **Task A.3**: Reorganize existing domain models, diff parser, and tests into `backend/`.
- **Task A.4**: Verify backend tests pass (15/15 tests passing).
- **Task A.5**: Compile Phase A Report (`docs/reports/phase_a_report.md`) and STOP for user review.

---

### Phase B: Backend Core
- **Task B.1**: Untrusted input sanitizer & prompt injection defense service (`backend/app/services/sanitizer.py`).
  - Delimiter neutralization, XML envelope formatting, instruction boundary guards.
  - Tests in `backend/tests/test_sanitizer.py`.
  - Proposed Commit: `feat(security): implement untrusted input sanitizer and prompt injection containment`
- **Task B.2**: LLM client adapter and structured schemas (`backend/app/schemas/llm.py`, `backend/app/adapters/llm_client.py`).
  - OpenAI-compatible and mock LLM clients, JSON schema enforcement, automatic retry on invalid JSON.
  - Tests in `backend/tests/test_llm_client.py`.
  - Proposed Commit: `feat(llm): implement structured LLM client adapter and response schemas`
- **Task B.3**: First-pass AI analysis service (`backend/app/services/analysis_service.py`).
  - Orchestration of diff parsing, sanitization, LLM review prompt construction, and pedagogical comment generation.
  - Tests in `backend/tests/test_analysis_service.py`.
  - Proposed Commit: `feat(analysis): implement first-pass AI review analysis service`
- **Task B.4**: Database persistence layer with SQLAlchemy 2 & SQLite (`backend/app/adapters/db_repository.py`).
  - Repository interface and SQLite implementation for reviews, comments, and audit timestamps.
  - Tests in `backend/tests/test_db_repository.py`.
  - Proposed Commit: `feat(db): implement SQLite persistence repository with SQLAlchemy 2`
- **Milestone B**: Run all backend tests, generate `docs/reports/phase_b_report.md`, STOP for approval.

---

### Phase C: Backend Completion
- **Task C.1**: Mentor review workflow service (`backend/app/services/mentor_service.py`).
  - Comment approval, editing, rejection, batch operations, review lifecycle state machine.
  - Tests in `backend/tests/test_mentor_service.py`.
  - Proposed Commit: `feat(mentor): implement mentor review triage and approval state machine`
- **Task C.2**: GitHub API client & review dispatcher (`backend/app/adapters/github_client.py`, `backend/app/services/dispatch_service.py`).
  - Strict enforcement of mentor approval gate: only `APPROVED` comments are dispatched to GitHub.
  - Tests with mock httpx transport in `backend/tests/test_dispatch_service.py`.
  - Proposed Commit: `feat(dispatch): implement GitHub PR review dispatcher with mentor approval gate`
- **Task C.3**: FastAPI REST API endpoints & centralized safe error handling (`backend/app/web/`).
  - Review endpoints (`/api/v1/reviews`), webhook endpoint (`/api/v1/webhooks/github`), health check (`/health`).
  - Safe error handler returning UUID `error_id` with internal trace logging.
  - Tests in `backend/tests/test_api_reviews.py` and `backend/tests/test_error_handling.py`.
  - Proposed Commit: `feat(api): implement REST API endpoints and centralized safe error handling`
- **Milestone C**: Run all backend tests, generate `docs/reports/phase_c_report.md`, STOP for approval.

---

### Phase D: Frontend (BLOCKED - UI HOLD)
> **HOLD STATUS**: Per Rule 13, all frontend tasks below remain blocked until the user sends explicit UI direction.
- **Task D.1 [BLOCKED]**: Vite + React 18 + TypeScript project setup.
- **Task D.2 [BLOCKED]**: TanStack Query client & API connector.
- **Task D.3 [BLOCKED]**: Review queue & diff viewer UI.
- **Task D.4 [BLOCKED]**: Comment triage card (Approve, Edit, Reject).
- **Task D.5 [BLOCKED]**: Vitest & React Testing Library test suite.

---

### Phase E: Quality and Hardening
- **Task E.1**: Prompt injection adversarial test harness in `evals/`.
  - Test suite with adversarial payloads verifying 100% containment.
  - Proposed Commit: `test(evals): add prompt injection adversarial evaluation suite`
- **Task E.2**: Security and vulnerability audit (`bandit` and `pip-audit`).
  - Run static analysis and dependency audit; resolve any findings.
  - Proposed Commit: `chore(security): run bandit scan and pip-audit dependency validation`
- **Task E.3**: Strict typing and linting (`mypy --strict`, `ruff`).
  - Enforce zero type errors across `backend/app`.
  - Proposed Commit: `chore(quality): enforce strict mypy typing and ruff linting`
- **Milestone E**: Compile `docs/reports/phase_e_report.md`, STOP for approval.

---

### Phase F: Deliverables
- **Task F.1**: End-to-end walkthrough demonstrating review ingestion, AI drafting, mentor triage, and GitHub publishing.
- **Task F.2**: Comprehensive `README.md` and Docker Compose deployment instructions.
- **Task F.3**: Final Deliverables Report (`docs/reports/phase_f_report.md`).

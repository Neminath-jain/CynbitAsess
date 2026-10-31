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

### Phase BC: Backend Core & Completion (IN PROGRESS - Combined Phase)
- **Task BC.1 [COMPLETED]**: Untrusted input sanitizer, XML boundary containment, and evidence verification (`backend/app/services/sanitizer.py`).
  - Neutralizes `</untrusted_pr_diff>` closing tags; drops findings without matching evidence in diff.
  - Tests in `backend/tests/test_sanitizer.py`.
  - Commit: `feat(security): implement untrusted input sanitizer with evidence check and injection containment`
- **Task BC.2 [COMPLETED]**: Structured Finding schema & LLM client adapter (`backend/app/schemas/finding.py`, `backend/app/schemas/llm.py`, `backend/app/adapters/llm_client.py`).
  - Finding schema: rule_id, severity, file, line_start, line_end, evidence_quote, explanation, suggested_fix, confidence.
  - MockLLMClient quotes real diff lines covering: missing foreign key index, hardcoded secret, unverified JWT, missing tests.
  - OpenAI-compatible client enabled via LLM_PROVIDER="openai" with mock default.
  - Tests in `backend/tests/test_llm_client.py`.
  - Commit: `feat(llm): implement structured finding models and mock/openai llm client adapters`
- **Task BC.3 [COMPLETED]**: Minimal GitHub PR Ingestion (`backend/app/schemas/github.py`, `backend/app/adapters/github_client.py`, `backend/app/services/ingestion.py`).
  - Strict https://github.com/{owner}/{repo}/pull/{number} URL validation.
  - Diff character size caps and truncation markers.
  - Offline recorded fixtures in `backend/tests/fixtures/recorded_github_pr.py` (0 network calls).
  - Tests in `backend/tests/test_ingestion.py`.
  - Commit: `feat(ingestion): implement github pull request ingestion with url validation and size caps`
- **Task BC.4 [COMPLETED]**: Database persistence layer with SQLAlchemy 2 & SQLite (`backend/app/adapters/db/`).
  - Synchronous SQLite sessions, foreign keys enabled (`PRAGMA foreign_keys=ON;`).
  - `ReviewRecord` with telemetry (provider, model, latency_ms, tokens, est_cost).
  - `FindingRecord` with index on `review_id`.
  - `DecisionRecord` with unique `finding_id` storing original text alongside edited text.
  - Commit: `feat(db): implement sqlite persistence with sqlalchemy 2 for review, finding, and decision`
- **Task BC.5 [COMPLETED]**: First-pass AI analysis & review orchestration service (`backend/app/services/review_service.py`).
  - Pipeline: Ingest -> Sanitize -> Rule Checks -> LLM Analysis -> Schema Validation -> Verify Evidence -> SQLite Persistence.
  - Commit: `feat(review): implement review orchestration pipeline connecting ingestion, sanitizer, llm, and persistence`
- **Task BC.6 [COMPLETED]**: FastAPI REST API endpoints & mentor authorization (`backend/app/web/`).
  - `POST /api/v1/reviews`, `GET /api/v1/reviews`, `GET /api/v1/reviews/{id}`.
  - `POST /api/v1/findings/{id}/decision` (approve, edit, reject) with constant-time mentor token validation.
  - `GET /api/v1/reviews/{id}/export` (markdown containing approved comments only).
  - Request correlation with `X-Request-ID` middleware; central safe exception handler with `error_id`.
  - Commit: `feat(api): implement fastapi review endpoints, mentor auth, and markdown export`
- **Task BC.7 [NEXT]**: Evaluation harness and benchmark runner in `evals/`.
- **Milestone BC**: Run all tests, lint, audit, generate `docs/reports/PHASE_BC_REPORT.md` (id BC), STOP for approval.

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

# Implementation Plan
## BitElevate PR Review Copilot

**Organization**: Cynbit Technologies  
**Approach**: Small, test-driven, reviewable steps adhering to Conventional Commits.  

---

### Phase 1: Foundation & Project Setup
- **Task 1.1**: Author specifications suite (`docs/PRD.md`, `docs/SRS.md`, `docs/architecture.md`, `docs/plan.md`).
  *Proposed Commit*: `docs: define PRD, SRS, architecture, and implementation plan for BitElevate PR Review Copilot`
- **Task 1.2**: Project scaffolding: `.gitignore`, `.env.example`, `pyproject.toml` (or `requirements.txt`), project directory structure (`app/domain`, `app/schemas`, `app/services`, `app/adapters`, `app/web`, `tests`).
  *Proposed Commit*: `chore: scaffold project structure, dependencies, and configuration templates`
- **Task 1.3**: Configuration management module (`app/config.py`) using `pydantic-settings` with tests.
  *Proposed Commit*: `feat(config): implement environment-based settings with pydantic-settings`

---

### Phase 2: Domain Models, Schemas & Diff Parser
- **Task 2.1**: Domain entities and enums (`ReviewStatus`, `CommentCategory`, `CommentSeverity`, `CommentStatus`, `PRReview`, `ReviewComment`).
  *Proposed Commit*: `feat(domain): define core review entities, status enums, and domain exceptions`
- **Task 2.2**: Unified Git diff parser (`app/services/diff_parser.py`) converting raw diff text into structured file hunks and line mappings with thorough tests.
  *Proposed Commit*: `feat(diff): implement unified git diff parser with line mapping`
- **Task 2.3**: Untrusted input sanitizer & prompt injection defense service (`app/services/sanitizer.py`) with test suite covering injection attempts.
  *Proposed Commit*: `feat(security): implement untrusted input sanitizer and prompt injection defenses`

---

### Phase 3: Schema-Enforced LLM Analysis Engine
- **Task 3.1**: LLM review request/response Pydantic boundary schemas (`app/schemas/llm.py`).
  *Proposed Commit*: `feat(schemas): define strict pydantic schemas for LLM structured output`
- **Task 3.2**: LLM client adapter (`app/adapters/llm_client.py`) supporting OpenAI/Gemini-compatible structured completion and mock test client.
  *Proposed Commit*: `feat(llm): implement structured LLM client adapter with mock support`
- **Task 3.3**: First-pass AI analysis service (`app/services/analysis_service.py`) orchestrating prompt generation, pedagogical guidelines, schema validation, and safe fallback.
  *Proposed Commit*: `feat(analysis): implement first-pass AI review analysis service with schema enforcement`

---

### Phase 4: Persistence Layer & Mentor Workflow Service
- **Task 4.1**: SQLite / SQLAlchemy database models and repository interface (`app/adapters/repository.py`).
  *Proposed Commit*: `feat(db): implement SQLite repository and database models for reviews and comments`
- **Task 4.2**: Mentor review workflow service (`app/services/mentor_service.py`) governing comment approval, editing, rejection, and state transitions.
  *Proposed Commit*: `feat(mentor): implement mentor triage, approval, and state machine transitions`

---

### Phase 5: GitHub Integration & Dispatcher
- **Task 5.1**: GitHub REST API client adapter (`app/adapters/github_client.py`) with mock transport tests.
  *Proposed Commit*: `feat(github): implement GitHub REST client for fetching diffs and posting reviews`
- **Task 5.2**: Dispatch service (`app/services/dispatch_service.py`) strictly enforcing that only `APPROVED` comments are published to GitHub.
  *Proposed Commit*: `feat(dispatch): implement review dispatcher enforcing mentor approval gate`

---

### Phase 6: Web API, Safe Error Handling & Mentor Dashboard
- **Task 6.1**: FastAPI application setup with global safe error handler, health check, and CORS configuration.
  *Proposed Commit*: `feat(web): configure FastAPI app with centralized safe error handler`
- **Task 6.2**: REST API routes (`app/web/routes/reviews.py`, `app/web/routes/webhooks.py`) delegating to services.
  *Proposed Commit*: `feat(api): implement review management and webhook ingestion endpoints`
- **Task 6.3**: Mentor Review Web Dashboard UI (`app/templates/dashboard.html`, `app/templates/review_detail.html`) allowing mentors to inspect diffs, edit comments, and approve/reject with one click.
  *Proposed Commit*: `feat(ui): implement responsive mentor review dashboard and comment triage interface`

---

### Phase 7: End-to-End Testing, Hardening & Verification
- **Task 7.1**: Comprehensive end-to-end integration test suite simulating full flow: PR ingestion -> AI draft -> mentor triage -> approval -> GitHub dispatch.
  *Proposed Commit*: `test(e2e): add end-to-end review lifecycle integration tests`
- **Task 7.2**: Developer guide, README.md, and production deployment notes.
  *Proposed Commit*: `docs: add comprehensive README, developer instructions, and deployment guide`

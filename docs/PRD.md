# Product Requirements Document (PRD)
## BitElevate PR Review Copilot

**Organization**: Cynbit Technologies  
**Programme**: BitElevate (Internship Engineering Programme)  
**Status**: Draft / Approved for MVP  
**Version**: 1.0.0  

---

### 1. Executive Summary & Objective

In Cynbit Technologies' BitElevate programme, interns submit daily pull requests (PRs) across diverse engineering stacks. Timely, high-quality, and constructive code reviews are critical for intern skill development. However, senior engineers and mentors face review fatigue from repetitive first-pass feedback (style inconsistencies, common anti-patterns, edge case oversights, security oversights).

**BitElevate PR Review Copilot** is an AI-assisted first-pass review engine designed to inspect intern pull requests and generate educational, constructive review comments. 

**Core Human-in-the-Loop Principle**:
> **A human mentor must explicitly approve, edit, or reject every comment before any intern ever sees it.** Under no circumstances does the system autonomously publish comments to GitHub pull requests without mentor authorization.

---

### 2. User Personas

| Persona | Role | Key Needs & Expectations |
|---|---|---|
| **BitElevate Intern** | Engineering Intern | Needs clear, constructive, pedagogical feedback explaining *why* a pattern is problematic and *how* to improve it, without intimidating or harsh criticism. |
| **Mentor / Senior Engineer** | Cynbit Technical Mentor | Needs an intuitive queue of AI-drafted review comments, organized by file and diff line, with one-click approve/edit/reject actions to minimize review overhead while maintaining high pedagogical and code standards. |
| **Programme Admin / Lead** | Engineering Leadership | Needs visibility into review latency, approval rates, mentor override rates, and assurance that no prompt injection from intern PR code compromises the review engine. |

---

### 3. Key Assumptions & Constraints

1. **Company Facts & Context**: Cynbit Technologies runs the BitElevate internship programme (source: workspace specification). Any broader company background outside the provided workspace context is treated as unverified assumption.
2. **Untrusted Inputs**: All PR code, diff contents, commit messages, PR titles, and descriptions are treated as **untrusted input** prone to accidental or deliberate indirect prompt injection.
3. **Strict Mentor Approval Gate**: The system state machine guarantees comments remain in `DRAFT` or `PENDING_APPROVAL` status until a verified mentor action transitions them to `APPROVED` or `REJECTED`. Only `APPROVED` comments are published to the target VCS (GitHub).
4. **Tone & Pedagogy**: Feedback must balance technical precision with educational warmth, teaching best practices (PEP 8, idiomatic patterns, security basics, type safety).
5. **Technology Stack**: Python 3.11+, Pydantic v2 for data boundaries, FastAPI for REST API, SQLite (file-based) for MVP persistence, standard boring libraries for VCS and LLM interoperability.

---

### 4. Scope & Feature Requirements

#### In-Scope (MVP)

1. **Pull Request Ingestion**:
   - Ingest PR metadata (repository, PR number, author, base/head commits, title, description).
   - Ingest unified git diffs per file, parsing modified lines, additions, deletions, and line numbers.

2. **Security & Input Sanitization**:
   - Defensive prompt engineering: Content wrapping and XML-delimited envelopes to mitigate indirect prompt injection.
   - Enforced diff size and token budgets with intelligent chunking to prevent denial-of-service or token exhaustion.

3. **Schema-Enforced LLM First-Pass Review**:
   - Generation of structured review comments conforming to strict Pydantic schemas.
   - Categorization: `BUG`, `SECURITY`, `PERFORMANCE`, `STYLE`, `PEDAGOGY`.
   - Pedagogical explanation (`issue`, `why_it_matters`, `suggested_fix`, `learning_resource`).

4. **Mentor Review Dashboard / Staging Workflow**:
   - Interface for mentors to view PRs, line-by-line diffs, and proposed AI comments.
   - Per-comment actions: `Approve`, `Edit & Approve`, `Reject`.
   - Bulk action: `Approve All Selected`, `Publish Review to GitHub`.

5. **GitHub Dispatch Integration**:
   - Publish approved comments back to GitHub as PR line comments or review summaries using the GitHub REST API.
   - Error handling with exponential backoff on GitHub API rate limits.

6. **Auditability & Observability**:
   - Full audit trail logging raw LLM responses, mentor edits, and publishing timestamps.
   - Safe error handling: internal structured logging with tracebacks, user-facing safe error messages.

#### Out-of-Scope (Non-Goals for MVP)
- Direct autonomous posting of comments without mentor intervention.
- Automated merging or closing of PRs.
- Autonomous git commits or push of code fixes back to intern branches.
- Self-hosted LLM fine-tuning pipelines.

---

### 5. Success Metrics

1. **Mentor Time Saved**: >= 50% reduction in time spent by mentors writing repetitive first-pass review comments.
2. **Review Turnaround**: First-pass review drafts generated within 30 seconds of PR ingestion.
3. **Safety Guarantee**: 0 unapproved comments posted to intern pull requests.
4. **Schema Compliance**: 100% of LLM outputs validated against strict Pydantic models before storage or presentation.

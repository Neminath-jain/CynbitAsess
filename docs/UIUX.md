# UI/UX Design Specification (UIUX.md)
## BitElevate PR Review Copilot

**System**: BitElevate PR Review Copilot  
**Organization**: Cynbit Technologies  
**Target Users**: Cynbit Technical Mentors & Senior Engineers reviewing intern pull requests  
**Framework**: React 18 + TypeScript + Vite + React Router v6 + TanStack Query v5  
**Styling**: Pure Modern CSS (Tokens, CSS Modules / scoped CSS, flex/grid layouts, dark theme)

---

## 1. Design Philosophy & Aesthetic System

BitElevate PR Review Copilot is a precision developer tool designed for high-throughput, low-fatigue code review triage. It balances speed, density, and cognitive clarity.

### 1.1 Visual Tokens & Color Palette
- **Backgrounds**:
  - Base: `#0B0F19` (Deep slate night)
  - Surface Elevated: `#131B2E` (Card background)
  - Surface Higher: `#1E293B` (Dropdowns, modals, hover states)
  - Border Subdued: `#334155` (Dividers, borders)
  - Border Highlight: `#6366F1` (Focus rings, active selection)
- **Accents & Brand**:
  - Indigo Accent: `#6366F1` (Primary CTA, links)
  - Violet Glow: `#8B5CF6` (Badges, subtle gradients)
- **Semantic Severity**:
  - `CRITICAL`: `#EF4444` (Rose / Red)
  - `WARNING`: `#F59E0B` (Amber / Yellow)
  - `SUGGESTION`: `#3B82F6` (Sky Blue)
  - `NOTE` / `STYLE`: `#10B981` (Emerald Green)
- **Triage Actions**:
  - Approve: `#10B981` (Emerald)
  - Edit: `#3B82F6` (Indigo/Blue)
  - Reject: `#64748B` (Muted Slate / Red accent on hover)
- **Typography**:
  - Interface: `Inter`, system-ui, sans-serif
  - Code / Diffs: `JetBrains Mono`, `Fira Code`, monospace
  - Scale: Consistent 4px baseline, 12px captions, 14px body, 16px headers, 20px subheadings, 24px page headers.

---

## 2. Core User Flows & Information Architecture

```
+---------------------------------------------------------------------------------------+
|                                    NAVIGATION HEADER                                  |
| [BitElevate Review Copilot]       Status: Online    Mentor: Token Active    Help [?]  |
+---------------------------------------------------------------------------------------+
|  [Queue / Dashboard]                                      [New Review URL Input: ->]  |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
| SCREEN 1: REVIEW QUEUE DASHBOARD (`/`)                                                |
| - Ingestion Trigger: [ https://github.com/owner/repo/pull/123 ] [ Analyze PR ]        |
| - Filter Tabs: [ All (12) ] [ Pending (4) ] [ Approved (8) ]                          |
| - Review Table / Cards: Repo, PR#, Author, Status, Findings Count, Date, Action       |
+---------------------------------------------------------------------------------------+
                                           |
                                           v (Click Review)
+---------------------------------------------------------------------------------------+
| SCREEN 2: SPLIT-PANE REVIEW DETAIL & MENTOR TRIAGE (`/reviews/:id`)                   |
| +---------------------------------------------------+-------------------------------+ |
| | HEADER: org/repo#42 - "Add Auth Middleware"       | [Export Approved Markdown]   | |
| | Author: @intern_dev  | Status: PENDING_APPROVAL   | Latency: 420ms | Cost: $0.00 | |
| +---------------------------------------------------+-------------------------------+ |
| | LEFT PANE: Findings & Triage (45% Width)          | RIGHT PANE: Workspace (55%)   | |
| | - Rule Badge: `SEC_JWT_UNVERIFIED`                | [Diff Viewer] [Rubric] [Export| |
| | - Severity: CRITICAL | Lines 45-52                |                               | |
| | - Evidence Quote:                                 | --- Diff View ---             | |
| |   `jwt.decode(token, verify=False)`               | @@ -40,12 +40,15 @@           | |
| | - Explanation: Pedagogical rationale              |   import jwt                  | |
| | - Suggested Fix: Minimal diff replacement         | - data = jwt.decode(token)    | |
| |                                                   | + data = jwt.decode(token,    | |
| | [Approve (A)] [Edit (E)] [Reject (R)]             | +     key=SECRET, alg="HS256")| |
| |                                                   |                               | |
| | (Card 2: `PERF_MISSING_FK_INDEX`)                 | --- Tab: Rubric Summary ---   | |
| | (Card 3: `TEST_MISSING_UNIT_TESTS`)               | Security: 1 | Perf: 1         | |
| +---------------------------------------------------+-------------------------------+ |
+---------------------------------------------------------------------------------------+
```

---

## 3. Detailed Screen Specifications

### 3.1 Screen 1: Review Queue Dashboard (`/` or `/reviews`)
1. **Header**:
   - Branding: "BitElevate PR Review Copilot - Mentor Console".
   - System status badge (`API: Connected`, `Mock/OpenAI Engine`).
   - Mentor Token indicator with option to configure or view token header.
2. **PR Ingestion Bar**:
   - Input: Text field with placeholder `https://github.com/owner/repo/pull/123`.
   - Real-time client validation: strict regex matching GitHub PR URLs.
   - Action: "Trigger Review" button with spinner loading state.
3. **Queue List**:
   - Columns: Repository & PR #, Title, Author, Status badge (`DRAFT`, `PENDING_APPROVAL`, `APPROVED`), Findings Count, Approved Count, Created At, Action ("Open Triage").
   - Filter bar: All, Pending, Approved.
   - States:
     - **Loading**: Skeletons for table rows.
     - **Empty**: "No pull request reviews found. Enter a GitHub PR URL above to trigger your first first-pass review."
     - **Error**: Banner showing safe error message with retry button.

### 3.2 Screen 2: Review Detail & Triage Console (`/reviews/:id`)
1. **Metadata Header Bar**:
   - Back button to queue (`<- All Reviews`).
   - Repository name, PR number, PR title, author username.
   - Status badge and provider/model telemetry tag.
   - Quick Action: "Export Markdown" button (instant preview modal or download).
2. **Split Pane Layout**:
   - **Left Column: Findings Stream**:
     - Filter/counter tabs: "All (N)", "Pending (N)", "Approved (N)", "Rejected (N)".
     - Finding Card:
       - Header: Rule ID chip (`SEC_HARDCODED_SECRET`), Severity chip (`CRITICAL`), File name (`app/auth.py`), Line span (`L24-L26`).
       - Evidence block: Monospace quote with quote border.
       - Explanation block: Why this matters for the intern's learning.
       - Suggested Fix block: Code snippet with diff styling.
       - Decision Action Buttons:
         - **Approve**: One-click accept.
         - **Edit**: Opens inline edit form to modify quote, explanation, suggested fix, or severity, and add mentor notes.
         - **Reject**: One-click reject.
       - Current Decision state badge: `[APPROVED]`, `[EDITED]`, `[REJECTED]`, or `[AWAITING MENTOR]`.
   - **Right Column: Multi-tab Inspector**:
     - **Tab 1: Unified Diff Viewer**:
       - Displays PR changes with line numbers, syntax highlighting, additions (`+`), deletions (`-`).
       - Clicking a finding auto-scrolls to the matching lines in the diff.
     - **Tab 2: Rubric & Telemetry Summary**:
       - Summary of rules triggered across the PR.
       - Token counts, latency in ms, cost estimate, truncation status (`None` or `Truncated`).
     - **Tab 3: Approved Comments Export**:
       - Live rendered Markdown of exclusively approved comments.
       - "Copy to Clipboard" button.
       - Note: Confirms zero unapproved comments are included in export.

---

## 4. Interaction & Accessibility (a11y) Standards

1. **Keyboard Shortcuts**:
   - `J` / `K` or `Down` / `Up`: Navigate to Next / Previous Finding.
   - `A`: Approve active finding.
   - `E`: Open Edit mode for active finding.
   - `R`: Reject active finding.
   - `Escape`: Cancel edit mode or close modals.
2. **Accessible Attributes**:
   - All interactive controls have unique IDs, `aria-label` or `aria-labelledby`.
   - Forms have explicit `<label>` bindings.
   - Buttons maintain visible focus rings (`outline: 2px solid #6366F1; outline-offset: 2px`).
   - Color is never the sole indicator of status (always paired with text labels and icons).

---

## 5. Architecture & State Management

1. **API Client & Type Generation**:
   - Generated TypeScript definitions from backend `/openapi.json` using `openapi-typescript` or OpenAPI schema generation script.
   - Strictly typed API client using `fetch` with base URL configured and Vite dev proxy (`/api` -> `http://localhost:8000`).
2. **Server State (TanStack Query v5)**:
   - `useReviews()`: Fetch review list with caching and status filtering.
   - `useReview(id)`: Fetch single review and findings.
   - `useCreateReview()`: Mutation for PR ingestion.
   - `useRecordDecision()`: Mutation for approve/edit/reject actions, optimistically updating local cache or invalidating review query.
   - `useExportMarkdown(id)`: Fetch Markdown export string.
3. **Component Separation**:
   - **Pages**: `ReviewListPage.tsx`, `ReviewDetailPage.tsx`, `NotFoundPage.tsx`.
   - **Components**:
     - `Header.tsx`: Navigation and global telemetry.
     - `IngestBar.tsx`: PR URL submission and validation.
     - `ReviewTable.tsx`: Review queue table and cards.
     - `FindingCard.tsx`: Finding presentation and triage controls.
     - `FindingEditModal.tsx`: Edit form for mentor overrides.
     - `DiffViewer.tsx`: Syntax-colored diff view with line highlighting.
     - `RubricSummary.tsx`: Telemetry and rule statistics.
     - `ExportPreview.tsx`: Rendered Markdown preview and copy utility.
   - **Zero Business Logic in Components**: Extracted into hooks (`useReviewTriage`, `useKeyboardNav`).

---

## 6. Testing & Quality Strategy

1. **Unit & Component Testing**:
   - `Vitest` and `@testing-library/react`.
   - Tests verify:
     - Finding triage flow (Approve, Edit, Reject buttons update status).
     - Empty, loading, and error states render correctly.
     - Keyboard accessibility and aria attributes.
     - Form validation on PR ingestion input.
2. **End-to-End Browser Validation**:
   - Verified in headless / live browser using browser subagent.
   - Capture screenshots of:
     - Review Dashboard with ingestion bar.
     - Split-pane review detail with findings and diff.
     - Edit decision dialog and approved export preview.

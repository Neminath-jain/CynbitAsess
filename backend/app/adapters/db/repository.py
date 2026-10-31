"""Repository for Review, Finding, and Decision persistence operations."""
import logging

from sqlalchemy import desc, select
from sqlalchemy.orm import Session, joinedload

from app.adapters.db.models import DecisionRecord, FindingRecord, ReviewRecord
from app.domain.exceptions import EntityNotFoundError, InvalidStateTransitionError
from app.schemas.finding import Finding

logger = logging.getLogger(__name__)


class ReviewRepository:
    """Repository managing ReviewRecord, FindingRecord, and DecisionRecord transactions."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create_review(
        self,
        repo_full_name: str,
        pr_number: int,
        pr_title: str,
        pr_description: str,
        author_username: str,
        base_commit_sha: str,
        head_commit_sha: str,
        raw_diff: str,
        summary: str,
        findings: list[Finding],
        is_truncated: bool = False,
        provider: str = "mock",
        model: str = "mock-rules",
        latency_ms: int = 0,
        tokens: int = 0,
        est_cost: float = 0.0,
    ) -> ReviewRecord:
        """Create and persist a new ReviewRecord with its initial findings."""
        review = ReviewRecord(
            repo_full_name=repo_full_name,
            pr_number=pr_number,
            pr_title=pr_title,
            pr_description=pr_description,
            author_username=author_username,
            base_commit_sha=base_commit_sha,
            head_commit_sha=head_commit_sha,
            raw_diff=raw_diff,
            summary=summary,
            status="PENDING_APPROVAL",
            is_truncated=is_truncated,
            provider=provider,
            model=model,
            latency_ms=latency_ms,
            tokens=tokens,
            est_cost=est_cost,
        )
        self.session.add(review)
        self.session.flush()

        for f in findings:
            record = FindingRecord(
                review_id=review.id,
                rule_id=f.rule_id,
                severity=f.severity.value,
                file=f.file,
                line_start=f.line_start,
                line_end=f.line_end,
                evidence_quote=f.evidence_quote,
                explanation=f.explanation,
                suggested_fix=f.suggested_fix,
                confidence=f.confidence,
            )
            self.session.add(record)

        self.session.flush()
        return review

    def get_review(self, review_id: str) -> ReviewRecord | None:
        """Retrieve a review by ID including findings and their decisions."""
        stmt = (
            select(ReviewRecord)
            .options(
                joinedload(ReviewRecord.findings).joinedload(FindingRecord.decision)
            )
            .where(ReviewRecord.id == review_id)
        )
        return self.session.scalars(stmt).first()

    def list_reviews(
        self,
        skip: int = 0,
        limit: int = 50,
        status: str | None = None,
    ) -> list[ReviewRecord]:
        """List reviews with pagination and optional status filter."""
        stmt = (
            select(ReviewRecord)
            .options(joinedload(ReviewRecord.findings))
            .order_by(desc(ReviewRecord.created_at))
            .offset(skip)
            .limit(limit)
        )
        if status:
            stmt = stmt.where(ReviewRecord.status == status.upper())
        return list(self.session.scalars(stmt).unique())

    def get_finding(self, finding_id: str) -> FindingRecord | None:
        """Retrieve a finding with its review and decision."""
        stmt = (
            select(FindingRecord)
            .options(
                joinedload(FindingRecord.review),
                joinedload(FindingRecord.decision),
            )
            .where(FindingRecord.id == finding_id)
        )
        return self.session.scalars(stmt).first()

    def record_decision(
        self,
        finding_id: str,
        action: str,
        mentor_id: str | None = None,
        mentor_notes: str | None = None,
        edited_quote: str | None = None,
        edited_explanation: str | None = None,
        edited_suggested_fix: str | None = None,
        edited_severity: str | None = None,
    ) -> DecisionRecord:
        """Record a human mentor triage decision on a finding and update review state."""
        action_upper = action.upper()
        if action_upper not in ("APPROVE", "EDIT", "REJECT"):
            raise InvalidStateTransitionError(
                f"Invalid decision action: '{action}'. Must be one of APPROVE, EDIT, REJECT."
            )

        finding = self.get_finding(finding_id)
        if not finding:
            raise EntityNotFoundError(f"Finding with id '{finding_id}' not found.")

        # Check existing decision: if already exists, update it; otherwise create new
        decision = finding.decision
        if decision is None:
            decision = DecisionRecord(
                finding_id=finding.id,
                action=action_upper,
                original_quote=finding.evidence_quote,
                original_explanation=finding.explanation,
                original_suggested_fix=finding.suggested_fix,
                original_severity=finding.severity,
                edited_quote=edited_quote,
                edited_explanation=edited_explanation,
                edited_suggested_fix=edited_suggested_fix,
                edited_severity=edited_severity,
                mentor_notes=mentor_notes,
                mentor_id=mentor_id,
            )
            self.session.add(decision)
            finding.decision = decision
            decision.finding = finding
        else:
            decision.action = action_upper
            decision.edited_quote = edited_quote
            decision.edited_explanation = edited_explanation
            decision.edited_suggested_fix = edited_suggested_fix
            decision.edited_severity = edited_severity
            decision.mentor_notes = mentor_notes
            decision.mentor_id = mentor_id

        self.session.flush()

        # Sync review status
        self._sync_review_status(finding.review_id)
        return decision

    def _sync_review_status(self, review_id: str) -> None:
        """Recalculate review status based on mentor decisions across all its findings."""
        review = self.get_review(review_id)
        if not review or not review.findings:
            return

        finding_ids = [f.id for f in review.findings]
        stmt = select(DecisionRecord).where(DecisionRecord.finding_id.in_(finding_ids))
        decisions = list(self.session.scalars(stmt))
        actions = [d.action for d in decisions]

        if not actions:
            review.status = "PENDING_APPROVAL"
        elif len(actions) < len(review.findings):
            review.status = "IN_REVIEW"
        else:
            # All findings have decisions
            if all(a in ("APPROVE", "EDIT") for a in actions):
                review.status = "APPROVED"
            elif all(a == "REJECT" for a in actions):
                review.status = "REJECTED"
            else:
                # Mixed approvals and rejections
                review.status = "APPROVED"

        self.session.flush()

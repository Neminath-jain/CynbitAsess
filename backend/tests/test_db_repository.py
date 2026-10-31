"""Unit tests for SQLite persistence with SQLAlchemy 2 (Review, Finding, Decision)."""
import pytest
from sqlalchemy.orm import Session
from app.adapters.db.repository import ReviewRepository
from app.adapters.db.session import DatabaseManager
from app.config import Settings
from app.domain.exceptions import EntityNotFoundError, InvalidStateTransitionError
from app.domain.models import CommentSeverity
from app.schemas.finding import Finding


@pytest.fixture
def db_session() -> Session:
    """Provide an isolated in-memory SQLite database session for testing."""
    test_settings = Settings(DATABASE_URL="sqlite:///:memory:")
    manager = DatabaseManager(test_settings)
    manager.create_tables()
    session = manager.session_factory()
    try:
        yield session
    finally:
        session.close()
        manager.drop_tables()


def create_sample_finding(rule_id: str = "SEC_01", line: int = 10) -> Finding:
    """Helper to instantiate a valid Finding."""
    return Finding(
        rule_id=rule_id,
        severity=CommentSeverity.CRITICAL,
        file="app/auth.py",
        line_start=line,
        line_end=line,
        evidence_quote='api_key = "secret_value_123"',
        explanation="Hardcoded secret credential.",
        suggested_fix="Use environment variable.",
        confidence=0.99,
    )


def test_create_review_with_telemetry_and_findings(db_session: Session) -> None:
    """Verify creating review persists PR metadata, telemetry fields, and child findings."""
    repo = ReviewRepository(db_session)
    finding = create_sample_finding()

    review = repo.create_review(
        repo_full_name="cynbit/bitelevate-sample",
        pr_number=10,
        pr_title="Authentication Module",
        pr_description="Added API token auth",
        author_username="intern_bob",
        base_commit_sha="aaa111",
        head_commit_sha="bbb222",
        raw_diff="+ api_key = 'secret_value_123'",
        summary="Review completed with 1 finding.",
        findings=[finding],
        provider="mock",
        model="mock-rules",
        latency_ms=120,
        tokens=450,
        est_cost=0.002,
    )
    db_session.commit()

    # Retrieve and verify
    fetched = repo.get_review(review.id)
    assert fetched is not None
    assert fetched.repo_full_name == "cynbit/bitelevate-sample"
    assert fetched.pr_number == 10
    assert fetched.provider == "mock"
    assert fetched.model == "mock-rules"
    assert fetched.latency_ms == 120
    assert fetched.tokens == 450
    assert fetched.est_cost == 0.002
    assert fetched.status == "PENDING_APPROVAL"

    assert len(fetched.findings) == 1
    f_rec = fetched.findings[0]
    assert f_rec.rule_id == "SEC_01"
    assert f_rec.severity == "CRITICAL"
    assert f_rec.line_start == 10
    assert f_rec.evidence_quote == 'api_key = "secret_value_123"'


def test_record_decision_keeps_original_and_edited_text(db_session: Session) -> None:
    """Verify decision records store both original finding text and mentor edits."""
    repo = ReviewRepository(db_session)
    finding = create_sample_finding()

    review = repo.create_review(
        repo_full_name="cynbit/bitelevate-sample",
        pr_number=11,
        pr_title="PR 11",
        pr_description="",
        author_username="intern",
        base_commit_sha="a",
        head_commit_sha="b",
        raw_diff="+ code",
        summary="summary",
        findings=[finding],
    )
    db_session.commit()

    f_id = review.findings[0].id
    decision = repo.record_decision(
        finding_id=f_id,
        action="EDIT",
        mentor_id="mentor_alice",
        mentor_notes="Clarified severity and explanation for intern learning.",
        edited_explanation="Edited: This credential must not be committed to Git.",
        edited_severity="WARNING",
    )
    db_session.commit()

    assert decision.action == "EDIT"
    # Original text preserved
    assert decision.original_explanation == "Hardcoded secret credential."
    assert decision.original_severity == "CRITICAL"
    # Edited text stored
    assert decision.edited_explanation == "Edited: This credential must not be committed to Git."
    assert decision.edited_severity == "WARNING"
    assert decision.mentor_notes == "Clarified severity and explanation for intern learning."

    # Review status should now be APPROVED (single finding was edited & approved)
    updated_review = repo.get_review(review.id)
    assert updated_review is not None
    assert updated_review.status == "APPROVED"


def test_record_decision_reject_updates_status(db_session: Session) -> None:
    """Verify rejecting all findings sets review status to REJECTED."""
    repo = ReviewRepository(db_session)
    f1 = create_sample_finding(rule_id="R1", line=5)
    review = repo.create_review(
        repo_full_name="cynbit/bitelevate",
        pr_number=12,
        pr_title="PR 12",
        pr_description="",
        author_username="intern",
        base_commit_sha="a",
        head_commit_sha="b",
        raw_diff="+ code",
        summary="summary",
        findings=[f1],
    )
    db_session.commit()

    repo.record_decision(finding_id=review.findings[0].id, action="REJECT", mentor_notes="False positive.")
    db_session.commit()

    updated = repo.get_review(review.id)
    assert updated is not None
    assert updated.status == "REJECTED"


def test_invalid_decision_action_raises_error(db_session: Session) -> None:
    """Verify invalid action raises InvalidStateTransitionError."""
    repo = ReviewRepository(db_session)
    review = repo.create_review(
        repo_full_name="cynbit/bitelevate",
        pr_number=13,
        pr_title="PR 13",
        pr_description="",
        author_username="intern",
        base_commit_sha="a",
        head_commit_sha="b",
        raw_diff="+ code",
        summary="summary",
        findings=[create_sample_finding()],
    )
    db_session.commit()

    with pytest.raises(InvalidStateTransitionError):
        repo.record_decision(finding_id=review.findings[0].id, action="INVALID_ACTION")


def test_record_decision_nonexistent_finding(db_session: Session) -> None:
    """Verify non-existent finding raises EntityNotFoundError."""
    repo = ReviewRepository(db_session)
    with pytest.raises(EntityNotFoundError):
        repo.record_decision(finding_id="non-existent-uuid", action="APPROVE")

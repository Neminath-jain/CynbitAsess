"""Unit tests for domain models and state transitions."""
import pytest
from app.domain.models import (
    PRReview,
    ReviewComment,
    ReviewStatus,
    CommentStatus,
    CommentCategory,
    CommentSeverity,
)
from app.domain.exceptions import InvalidStateTransitionError


def create_dummy_comment(review_id: str = "rev-1", line: int = 10) -> ReviewComment:
    """Helper to instantiate a dummy comment."""
    return ReviewComment(
        review_id=review_id,
        file_path="app/main.py",
        line_number=line,
        diff_hunk="@@ -1,5 +1,5 @@",
        category=CommentCategory.BUG,
        severity=CommentSeverity.WARNING,
        title="Potential Null Pointer",
        issue="Variable might be None when accessed.",
        why_it_matters="Accessing attributes on None causes AttributeError at runtime.",
        suggested_fix="if var is not None:\n    var.process()",
        learning_resource="https://docs.python.org/3/tutorial/errors.html",
    )


def test_comment_lifecycle_approve() -> None:
    """Test standard approval of a draft comment."""
    comment = create_dummy_comment()
    assert comment.status == CommentStatus.PENDING
    assert comment.is_mentor_edited is False

    comment.approve(mentor_notes="Looks good, valid issue")
    assert comment.status == CommentStatus.APPROVED
    assert comment.mentor_notes == "Looks good, valid issue"


def test_comment_lifecycle_reject() -> None:
    """Test rejecting a draft comment."""
    comment = create_dummy_comment()
    comment.reject(mentor_notes="False positive")
    assert comment.status == CommentStatus.REJECTED


def test_comment_lifecycle_edit() -> None:
    """Test editing comment fields by mentor."""
    comment = create_dummy_comment()
    comment.edit(
        title="Clarified Error Handling",
        severity=CommentSeverity.CRITICAL,
        mentor_notes="Clarified explanation for intern",
    )
    assert comment.title == "Clarified Error Handling"
    assert comment.severity == CommentSeverity.CRITICAL
    assert comment.is_mentor_edited is True


def test_invalid_publish_unapproved_comment() -> None:
    """Verify publishing a PENDING comment raises InvalidStateTransitionError."""
    comment = create_dummy_comment()
    with pytest.raises(InvalidStateTransitionError):
        comment.mark_published()


def test_cannot_modify_published_comment() -> None:
    """Verify published comment cannot be edited or re-approved."""
    comment = create_dummy_comment()
    comment.approve()
    comment.mark_published()
    assert comment.status == CommentStatus.PUBLISHED

    with pytest.raises(InvalidStateTransitionError):
        comment.approve()

    with pytest.raises(InvalidStateTransitionError):
        comment.edit(title="New Title")

    with pytest.raises(InvalidStateTransitionError):
        comment.reject()


def test_comment_markdown_formatting() -> None:
    """Verify formatted GitHub markdown output includes badges and sections."""
    comment = create_dummy_comment()
    md = comment.format_github_markdown()
    assert "[BUG]" in md
    assert "[WARNING]" in md
    assert "Potential Null Pointer" in md
    assert "**Why this matters:**" in md
    assert "BitElevate technical mentor" in md


def test_review_aggregate_transitions() -> None:
    """Verify PRReview aggregate handles comments, batch approvals, and publishing."""
    c1 = create_dummy_comment(review_id="rev-1", line=12)
    c2 = create_dummy_comment(review_id="rev-1", line=25)
    review = PRReview(
        id="rev-1",
        repo_full_name="cynbit/bitelevate-core",
        pr_number=42,
        pr_title="Add feature X",
        author_username="intern_alice",
        base_commit_sha="abc111",
        head_commit_sha="def222",
        comments=[c1, c2],
    )

    # Initial state
    assert review.can_publish() is False
    assert len(review.get_approved_comments()) == 0

    # Approve single comment
    review.approve_comment(c1.id, mentor_notes="Approved c1")
    assert review.can_publish() is True
    assert len(review.get_approved_comments()) == 1
    assert review.status == ReviewStatus.IN_REVIEW

    # Approve all
    review.approve_all(mentor_id="mentor_bob")
    assert review.status == ReviewStatus.APPROVED
    assert len(review.get_approved_comments()) == 2

    # Publish
    review.mark_published()
    assert review.status == ReviewStatus.PUBLISHED
    assert c1.status == CommentStatus.PUBLISHED
    assert c2.status == CommentStatus.PUBLISHED
    assert review.published_at is not None

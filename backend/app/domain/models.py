"""Core domain models, status enums, and business logic methods.

All entities are immutable-by-default or controlled via explicit domain transition methods.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List
import uuid
from pydantic import BaseModel, Field, ConfigDict
from app.domain.exceptions import InvalidStateTransitionError


class ReviewStatus(str, Enum):
    """Lifecycle statuses for a Pull Request review."""
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"


class CommentStatus(str, Enum):
    """Lifecycle statuses for an individual review comment."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PUBLISHED = "PUBLISHED"


class CommentCategory(str, Enum):
    """Pedagogical and technical categories for review comments."""
    BUG = "BUG"
    SECURITY = "SECURITY"
    PERFORMANCE = "PERFORMANCE"
    STYLE = "STYLE"
    PEDAGOGY = "PEDAGOGY"


class CommentSeverity(str, Enum):
    """Severity levels for review comments."""
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    SUGGESTION = "SUGGESTION"
    NOTE = "NOTE"


def get_current_utc_time() -> datetime:
    """Return timezone-aware current UTC datetime."""
    return datetime.now(timezone.utc)


class ReviewComment(BaseModel):
    """An individual line-level or file-level review comment."""

    model_config = ConfigDict(validate_assignment=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    review_id: str
    file_path: str
    line_number: int = Field(ge=1)
    diff_hunk: Optional[str] = None
    category: CommentCategory
    severity: CommentSeverity
    title: str = Field(min_length=3, max_length=120)
    issue: str = Field(min_length=5)
    why_it_matters: str = Field(min_length=5)
    suggested_fix: str = Field(min_length=1)
    learning_resource: Optional[str] = None
    status: CommentStatus = CommentStatus.PENDING
    mentor_notes: Optional[str] = None
    is_mentor_edited: bool = False
    created_at: datetime = Field(default_factory=get_current_utc_time)
    updated_at: datetime = Field(default_factory=get_current_utc_time)

    def approve(self, mentor_notes: Optional[str] = None) -> None:
        """Approve the comment for publication to the intern."""
        if self.status == CommentStatus.PUBLISHED:
            raise InvalidStateTransitionError("Cannot approve an already published comment.")
        self.status = CommentStatus.APPROVED
        if mentor_notes:
            self.mentor_notes = mentor_notes
        self.updated_at = get_current_utc_time()

    def reject(self, mentor_notes: Optional[str] = None) -> None:
        """Reject the comment so it is never published."""
        if self.status == CommentStatus.PUBLISHED:
            raise InvalidStateTransitionError("Cannot reject an already published comment.")
        self.status = CommentStatus.REJECTED
        if mentor_notes:
            self.mentor_notes = mentor_notes
        self.updated_at = get_current_utc_time()

    def edit(
        self,
        title: Optional[str] = None,
        issue: Optional[str] = None,
        why_it_matters: Optional[str] = None,
        suggested_fix: Optional[str] = None,
        severity: Optional[CommentSeverity] = None,
        category: Optional[CommentCategory] = None,
        mentor_notes: Optional[str] = None,
    ) -> None:
        """Apply mentor edits to the comment content before approval."""
        if self.status == CommentStatus.PUBLISHED:
            raise InvalidStateTransitionError("Cannot edit an already published comment.")
        if title:
            self.title = title
        if issue:
            self.issue = issue
        if why_it_matters:
            self.why_it_matters = why_it_matters
        if suggested_fix:
            self.suggested_fix = suggested_fix
        if severity:
            self.severity = severity
        if category:
            self.category = category
        if mentor_notes:
            self.mentor_notes = mentor_notes
        self.is_mentor_edited = True
        self.updated_at = get_current_utc_time()

    def mark_published(self) -> None:
        """Mark comment as dispatched to GitHub."""
        if self.status != CommentStatus.APPROVED:
            raise InvalidStateTransitionError(
                f"Cannot publish comment in status {self.status.value}; only APPROVED comments can be published."
            )
        self.status = CommentStatus.PUBLISHED
        self.updated_at = get_current_utc_time()

    def format_github_markdown(self) -> str:
        """Format the pedagogical comment cleanly for the intern in GitHub markdown."""
        badge = f"**[{self.category.value}] [{self.severity.value}]** {self.title}"
        body_parts = [
            f"### {badge}",
            f"\n**Observation:**\n{self.issue}",
            f"\n**Why this matters:**\n{self.why_it_matters}",
            f"\n**Recommended Action / Fix:**\n{self.suggested_fix}",
        ]
        if self.learning_resource:
            body_parts.append(f"\n📚 **Learn More:** [{self.learning_resource}]({self.learning_resource})")
        if self.is_mentor_edited:
            body_parts.append("\n\n*Note: This comment was curated and approved by a BitElevate technical mentor.*")
        else:
            body_parts.append("\n\n*Note: Reviewed and approved by a BitElevate technical mentor.*")
        return "\n".join(body_parts)


class PRReview(BaseModel):
    """Aggregate root representing a pull request review session."""

    model_config = ConfigDict(validate_assignment=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    repo_full_name: str
    pr_number: int = Field(ge=1)
    pr_title: str
    pr_description: str = ""
    author_username: str
    base_commit_sha: str
    head_commit_sha: str
    status: ReviewStatus = ReviewStatus.PENDING_APPROVAL
    summary: str = ""
    comments: List[ReviewComment] = Field(default_factory=list)
    total_files_analyzed: int = 0
    raw_llm_response: Optional[str] = None
    mentor_id: Optional[str] = None
    created_at: datetime = Field(default_factory=get_current_utc_time)
    updated_at: datetime = Field(default_factory=get_current_utc_time)
    published_at: Optional[datetime] = None

    def approve_comment(self, comment_id: str, mentor_notes: Optional[str] = None) -> None:
        """Approve an individual comment by ID."""
        comment = self.get_comment(comment_id)
        comment.approve(mentor_notes)
        self._sync_review_status()

    def reject_comment(self, comment_id: str, mentor_notes: Optional[str] = None) -> None:
        """Reject an individual comment by ID."""
        comment = self.get_comment(comment_id)
        comment.reject(mentor_notes)
        self._sync_review_status()

    def approve_all(self, mentor_id: Optional[str] = None) -> None:
        """Batch approve all pending comments in the review."""
        if mentor_id:
            self.mentor_id = mentor_id
        for comment in self.comments:
            if comment.status == CommentStatus.PENDING:
                comment.approve()
        self._sync_review_status()

    def reject_all(self, mentor_id: Optional[str] = None) -> None:
        """Batch reject all pending comments in the review."""
        if mentor_id:
            self.mentor_id = mentor_id
        for comment in self.comments:
            if comment.status == CommentStatus.PENDING:
                comment.reject()
        self._sync_review_status()

    def get_comment(self, comment_id: str) -> ReviewComment:
        """Retrieve a specific comment from the review."""
        for c in self.comments:
            if c.id == comment_id:
                return c
        raise InvalidStateTransitionError(f"Comment with id '{comment_id}' not found in review '{self.id}'.")

    def get_approved_comments(self) -> List[ReviewComment]:
        """Return list of comments approved for publishing."""
        return [c for c in self.comments if c.status == CommentStatus.APPROVED]

    def can_publish(self) -> bool:
        """Strict gate: Only reviews in APPROVED or IN_REVIEW state with at least one APPROVED comment can be published."""
        approved = self.get_approved_comments()
        return len(approved) > 0 and self.status in (ReviewStatus.APPROVED, ReviewStatus.IN_REVIEW, ReviewStatus.PENDING_APPROVAL)

    def mark_published(self) -> None:
        """Mark the review as published after successfully dispatching approved comments."""
        if not self.can_publish():
            raise InvalidStateTransitionError(
                "Cannot publish review: no approved comments available or review in invalid state."
            )
        for comment in self.get_approved_comments():
            comment.mark_published()
        self.status = ReviewStatus.PUBLISHED
        self.published_at = get_current_utc_time()
        self.updated_at = get_current_utc_time()

    def _sync_review_status(self) -> None:
        """Recalculate review level status based on comment states."""
        self.updated_at = get_current_utc_time()
        if not self.comments:
            return
        statuses = {c.status for c in self.comments}
        if statuses == {CommentStatus.APPROVED}:
            self.status = ReviewStatus.APPROVED
        elif statuses == {CommentStatus.REJECTED}:
            self.status = ReviewStatus.REJECTED
        elif CommentStatus.APPROVED in statuses:
            self.status = ReviewStatus.IN_REVIEW

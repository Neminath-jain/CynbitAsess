"""SQLAlchemy 2 declarative database models for reviews, findings, and mentor decisions."""
import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def generate_uuid() -> str:
    """Return a new random UUID string."""
    return str(uuid.uuid4())


def get_utc_now() -> datetime:
    """Return current UTC timestamp."""
    return datetime.now(UTC)


class Base(DeclarativeBase):
    """Base declarative class for all SQLAlchemy 2 models."""
    pass


class ReviewRecord(Base):
    """Database record for a Pull Request review session."""

    __tablename__ = "reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    repo_full_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    pr_number: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    pr_title: Mapped[str] = mapped_column(String(500), nullable=False)
    pr_description: Mapped[str] = mapped_column(Text, default="")
    author_username: Mapped[str] = mapped_column(String(100), nullable=False)
    base_commit_sha: Mapped[str] = mapped_column(String(40), nullable=False)
    head_commit_sha: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(50), index=True, default="PENDING_APPROVAL")
    summary: Mapped[str] = mapped_column(Text, default="")
    raw_diff: Mapped[str] = mapped_column(Text, default="")
    is_truncated: Mapped[bool] = mapped_column(Boolean, default=False)

    # Telemetry and LLM attribution fields
    provider: Mapped[str] = mapped_column(String(50), default="mock")
    model: Mapped[str] = mapped_column(String(100), default="mock-rules")
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    tokens: Mapped[int] = mapped_column(Integer, default=0)
    est_cost: Mapped[float] = mapped_column(Float, default=0.0)

    created_at: Mapped[datetime] = mapped_column(default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(default=get_utc_now, onupdate=get_utc_now)

    findings: Mapped[list["FindingRecord"]] = relationship(
        "FindingRecord",
        back_populates="review",
        cascade="all, delete-orphan",
        order_by="FindingRecord.line_start",
    )


class FindingRecord(Base):
    """Database record representing an individual code finding."""

    __tablename__ = "findings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    review_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("reviews.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    rule_id: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    file: Mapped[str] = mapped_column(String(500), nullable=False)
    line_start: Mapped[int] = mapped_column(Integer, nullable=False)
    line_end: Mapped[int] = mapped_column(Integer, nullable=False)
    evidence_quote: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    suggested_fix: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    created_at: Mapped[datetime] = mapped_column(default=get_utc_now)

    review: Mapped[ReviewRecord] = relationship("ReviewRecord", back_populates="findings")
    decision: Mapped["DecisionRecord | None"] = relationship(
        "DecisionRecord",
        back_populates="finding",
        uselist=False,
        cascade="all, delete-orphan",
    )


class DecisionRecord(Base):
    """Database record capturing mentor triage action on a finding."""

    __tablename__ = "decisions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    finding_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("findings.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    action: Mapped[str] = mapped_column(String(20), nullable=False)  # APPROVE, EDIT, REJECT

    # Keeps original text next to any edited text
    original_quote: Mapped[str] = mapped_column(Text, nullable=False)
    original_explanation: Mapped[str] = mapped_column(Text, nullable=False)
    original_suggested_fix: Mapped[str] = mapped_column(Text, nullable=False)
    original_severity: Mapped[str] = mapped_column(String(20), nullable=False)

    # Optional mentor edits
    edited_quote: Mapped[str | None] = mapped_column(Text, nullable=True)
    edited_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    edited_suggested_fix: Mapped[str | None] = mapped_column(Text, nullable=True)
    edited_severity: Mapped[str | None] = mapped_column(String(20), nullable=True)

    mentor_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    mentor_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    decided_at: Mapped[datetime] = mapped_column(default=get_utc_now)

    finding: Mapped[FindingRecord] = relationship("FindingRecord", back_populates="decision")

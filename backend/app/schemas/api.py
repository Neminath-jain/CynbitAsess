"""Pydantic v2 schemas for API requests and responses."""
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ReviewCreateRequest(BaseModel):
    """Payload for initiating a new pull request review."""

    model_config = ConfigDict(extra="forbid")

    pr_url: str = Field(
        ...,
        description="Public GitHub pull request URL (e.g. https://github.com/owner/repo/pull/123)",
        examples=["https://github.com/cynbit/bitelevate-sample/pull/42"],
    )


class DecisionRequest(BaseModel):
    """Payload submitted by a human mentor to triage a review finding."""

    model_config = ConfigDict(extra="forbid")

    action: Literal["APPROVE", "EDIT", "REJECT"] = Field(
        ...,
        description="Mentor decision: APPROVE (keep finding), EDIT (modify finding text/severity), or REJECT (discard finding)",
    )
    mentor_notes: str | None = Field(
        default=None,
        description="Optional pedagogical context or coaching notes from the mentor",
    )
    edited_quote: str | None = Field(
        default=None,
        description="Replacement evidence quote if edited",
    )
    edited_explanation: str | None = Field(
        default=None,
        description="Replacement explanation text if edited",
    )
    edited_suggested_fix: str | None = Field(
        default=None,
        description="Replacement suggested remediation code if edited",
    )
    edited_severity: str | None = Field(
        default=None,
        description="Modified severity level (blocker, major, minor, nit) if edited",
    )


class DecisionResponse(BaseModel):
    """Response model representing a recorded mentor triage decision."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    finding_id: str
    action: str
    original_quote: str
    original_explanation: str
    original_suggested_fix: str
    original_severity: str
    edited_quote: str | None = None
    edited_explanation: str | None = None
    edited_suggested_fix: str | None = None
    edited_severity: str | None = None
    mentor_notes: str | None = None
    mentor_id: str | None = None
    decided_at: datetime


class FindingResponse(BaseModel):
    """Response model representing an individual code finding."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    review_id: str
    rule_id: str
    severity: str
    file: str
    line_start: int
    line_end: int
    evidence_quote: str
    explanation: str
    suggested_fix: str
    confidence: float
    created_at: datetime
    decision: DecisionResponse | None = None


class ReviewResponse(BaseModel):
    """Detailed response model for a pull request review session."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    repo_full_name: str
    pr_number: int
    pr_title: str
    pr_description: str
    author_username: str
    base_commit_sha: str
    head_commit_sha: str
    status: str
    summary: str
    is_truncated: bool
    provider: str
    model: str
    latency_ms: int
    tokens: int
    est_cost: float
    created_at: datetime
    updated_at: datetime
    findings: list[FindingResponse] = Field(default_factory=list)


class ReviewListItemResponse(BaseModel):
    """Summary model for review catalog listing."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    repo_full_name: str
    pr_number: int
    pr_title: str
    author_username: str
    status: str
    provider: str
    model: str
    findings_count: int
    approved_count: int
    created_at: datetime


class ErrorResponse(BaseModel):
    """Standardized safe error payload. Never contains stack traces or internal paths."""

    error_id: str = Field(description="Unique UUID for tracing and logging error occurrences")
    message: str = Field(description="Safe, sanitized error description suitable for end clients")
    detail: Any | None = Field(default=None, description="Optional structured field details (e.g. validation issues)")

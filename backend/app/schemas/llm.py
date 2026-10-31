"""LLM review response schemas enforcing structured output."""
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.finding import Finding


class LLMReviewResponse(BaseModel):
    """Structured response output produced by LLM analysis."""

    model_config = ConfigDict(validate_assignment=True)

    summary: str = Field(min_length=5, description="High-level pedagogical summary of the PR review")
    general_feedback: str = Field(default="", description="General educational feedback for the intern")
    findings: list[Finding] = Field(default_factory=list, description="List of specific code findings")

"""Finding schema representing a code review finding from analysis."""
from pydantic import BaseModel, ConfigDict, Field

from app.domain.models import CommentSeverity


class Finding(BaseModel):
    """An individual structured code review finding."""

    model_config = ConfigDict(validate_assignment=True)

    rule_id: str = Field(min_length=2, max_length=64, description="Unique identifier for the review rule")
    severity: CommentSeverity = Field(description="Severity tier of the finding")
    file: str = Field(min_length=1, description="Path to the file matching the diff")
    line_start: int = Field(ge=1, description="Starting line number in the new file")
    line_end: int = Field(ge=1, description="Ending line number in the new file")
    evidence_quote: str = Field(min_length=1, description="Exact code quote from the diff supporting the finding")
    explanation: str = Field(min_length=5, description="Clear, pedagogical explanation of the issue and why it matters")
    suggested_fix: str = Field(min_length=1, description="Actionable code change or remediation advice")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")

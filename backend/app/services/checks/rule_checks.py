"""Deterministic rule checks module.

Performs static regex pattern inspections directly on diff lines to identify:
1. Missing foreign key index
2. Hardcoded secrets
3. Unverified JWT decoding
4. Missing unit test additions
"""
import re

from pydantic import BaseModel, ConfigDict, Field

from app.domain.models import CommentSeverity
from app.schemas.finding import Finding


class CheckResult(BaseModel):
    """Result of an individual deterministic rule check."""

    model_config = ConfigDict(validate_assignment=True)

    rule_id: str = Field(min_length=2, max_length=64)
    severity: CommentSeverity
    file: str
    line_start: int = Field(ge=1)
    line_end: int = Field(ge=1)
    evidence_quote: str
    explanation: str
    suggested_fix: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)

    def to_finding(self) -> Finding:
        """Convert CheckResult to standard Finding schema."""
        return Finding(
            rule_id=self.rule_id,
            severity=self.severity,
            file=self.file,
            line_start=self.line_start,
            line_end=self.line_end,
            evidence_quote=self.evidence_quote,
            explanation=self.explanation,
            suggested_fix=self.suggested_fix,
            confidence=self.confidence,
        )


SECRET_PATTERNS = ["api_key", "secret", "secret_key", "password", "token", "private_key"]
SECRET_VALUE_REGEX = re.compile(r"['\"][A-Za-z0-9_\-]{8,}['\"]")


def run_rule_checks(raw_diff: str) -> list[CheckResult]:
    """Inspect raw diff lines and return typed CheckResult models with verbatim line evidence."""
    results: list[CheckResult] = []
    if not raw_diff or not raw_diff.strip():
        return results

    lines = raw_diff.splitlines()
    current_file = "unknown_file.py"
    has_tests = False
    first_code_line: str | None = None
    first_code_file: str = "app/main.py"
    first_code_line_num: int = 1

    line_num = 0
    for line in lines:
        if line.startswith("+++ b/"):
            current_file = line[6:].strip()
            if "test" in current_file.lower():
                has_tests = True
            line_num = 0
            continue
        elif line.startswith("@@"):
            m = re.search(r"\+(\d+)", line)
            if m:
                line_num = int(m.group(1))
            continue

        if line.startswith("+") and not line.startswith("+++"):
            line_num += 1
            content = line[1:].strip()

            if not first_code_line and content and not content.startswith("#"):
                first_code_line = line[1:]
                first_code_file = current_file
                first_code_line_num = line_num

            # 1. Missing Foreign Key Index
            if ("ForeignKey(" in content or "foreign_key" in content.lower()) and "index=True" not in content:
                results.append(
                    CheckResult(
                        rule_id="PERF_MISSING_FK_INDEX",
                        severity=CommentSeverity.WARNING,
                        file=current_file,
                        line_start=line_num,
                        line_end=line_num,
                        evidence_quote=line[1:],
                        explanation=(
                            "Foreign key defined without an explicit database index. "
                            "In relational databases, unindexed foreign keys lead to full table scans during JOINs "
                            "and cascading operations, resulting in severe performance degradation as rows grow."
                        ),
                        suggested_fix="Add index=True to the ForeignKey column declaration.",
                        confidence=1.0,
                    )
                )

            # 2. Hardcoded Secret
            if any(p in content.lower() for p in SECRET_PATTERNS) and SECRET_VALUE_REGEX.search(content):
                results.append(
                    CheckResult(
                        rule_id="SEC_HARDCODED_SECRET",
                        severity=CommentSeverity.CRITICAL,
                        file=current_file,
                        line_start=line_num,
                        line_end=line_num,
                        evidence_quote=line[1:],
                        explanation=(
                            "Potential hardcoded secret or credential detected in source code. "
                            "Committing credentials to version control exposes infrastructure to unauthorized access and credential leakage."
                        ),
                        suggested_fix="Extract secret into an environment variable and load it via pydantic-settings.",
                        confidence=1.0,
                    )
                )

            # 3. JWT Decode without verification
            if "jwt.decode(" in content and ("verify=False" in content or "verify_signature': False" in content or 'verify_signature": False' in content):
                results.append(
                    CheckResult(
                        rule_id="SEC_JWT_UNVERIFIED",
                        severity=CommentSeverity.CRITICAL,
                        file=current_file,
                        line_start=line_num,
                        line_end=line_num,
                        evidence_quote=line[1:],
                        explanation=(
                            "JWT token decoded with verification disabled. "
                            "Skipping cryptographic signature validation allows malicious actors to forge token claims and impersonate users."
                        ),
                        suggested_fix="Enforce signature validation: jwt.decode(token, secret_key, algorithms=['HS256']).",
                        confidence=1.0,
                    )
                )

    # 4. No tests
    if not has_tests and first_code_line:
        results.append(
            CheckResult(
                rule_id="TEST_MISSING_UNIT_TESTS",
                severity=CommentSeverity.WARNING,
                file=first_code_file,
                line_start=first_code_line_num,
                line_end=first_code_line_num,
                evidence_quote=first_code_line,
                explanation=(
                    "New code added without accompanying unit tests in the pull request. "
                    "Shipping features without automated test coverage increases regression risks."
                ),
                suggested_fix="Add unit tests in tests/ covering both expected behavior and error edge cases.",
                confidence=0.90,
            )
        )

    return results

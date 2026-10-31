"""Untrusted input sanitizer and prompt injection containment service.

Guarantees that untrusted PR diffs and metadata cannot break prompt instruction boundaries
and verifies that all LLM findings cite real evidence present in the original diff.
"""
import logging
import re

from app.config import get_settings
from app.schemas.finding import Finding

logger = logging.getLogger(__name__)

CLOSING_TAG_PATTERN = re.compile(r"<\s*/\s*untrusted_pr_diff\s*>", re.IGNORECASE)
OPENING_TAG_PATTERN = re.compile(r"<\s*untrusted_pr_diff\s*>", re.IGNORECASE)


class InputSanitizerService:
    """Service to contain untrusted pull request data and verify evidence quotes."""

    def __init__(self, max_chars: int | None = None) -> None:
        settings = get_settings()
        self.max_chars = max_chars or settings.MAX_DIFF_CHARACTERS

    def sanitize_untrusted_text(self, text: str) -> str:
        """Neutralize tag injection vectors inside untrusted input."""
        if not text:
            return ""

        # Neutralize any attempt to break out using the boundary tags
        sanitized = CLOSING_TAG_PATTERN.sub("&lt;/untrusted_pr_diff&gt;", text)
        sanitized = OPENING_TAG_PATTERN.sub("&lt;untrusted_pr_diff&gt;", sanitized)

        # Budget cap guardrail
        if len(sanitized) > self.max_chars:
            logger.warning("Untrusted text length (%d) exceeded max budget (%d). Truncating.", len(sanitized), self.max_chars)
            sanitized = sanitized[: self.max_chars] + "\n[TRUNCATED: Exceeded max allowed diff size]"

        return sanitized

    def wrap_in_envelope(self, pr_title: str, pr_body: str, raw_diff: str) -> str:
        """Wrap untrusted PR components in strict XML boundary tags."""
        clean_title = self.sanitize_untrusted_text(pr_title)
        clean_body = self.sanitize_untrusted_text(pr_body)
        clean_diff = self.sanitize_untrusted_text(raw_diff)

        return (
            "<untrusted_pr_diff>\n"
            f"<metadata>\n"
            f"<title>{clean_title}</title>\n"
            f"<description>{clean_body}</description>\n"
            f"</metadata>\n"
            f"<diff_content>\n{clean_diff}\n</diff_content>\n"
            "</untrusted_pr_diff>"
        )

    @staticmethod
    def verify_evidence(findings: list[Finding], raw_diff: str) -> list[Finding]:
        """Drop any finding whose evidence_quote does not appear in the raw diff.

        Normalizes whitespace on both sides to allow resilient matching while strictly
        preventing hallucinated code lines from ever reaching the mentor or intern.
        """
        if not raw_diff:
            return []

        def normalize_ws(s: str) -> str:
            return " ".join(s.split())

        normalized_diff = normalize_ws(raw_diff)
        diff_lines_normalized = [normalize_ws(line) for line in raw_diff.splitlines() if line.strip()]

        verified: list[Finding] = []
        for finding in findings:
            quote = finding.evidence_quote
            normalized_quote = normalize_ws(quote)

            if not normalized_quote:
                continue

            # Exact match, normalized full-diff substring, or normalized line substring match
            is_valid = (
                quote in raw_diff
                or normalized_quote in normalized_diff
                or any(normalized_quote in line for line in diff_lines_normalized)
            )

            if is_valid:
                verified.append(finding)
            else:
                logger.warning(
                    "Dropping finding '%s' on %s: evidence quote %r not found in diff.",
                    finding.rule_id,
                    finding.file,
                    quote,
                )
        return verified

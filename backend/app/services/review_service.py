"""Review Service orchestrating the complete code review pipeline:

Ingest -> Sanitize -> Rule Checks -> LLM Analysis -> Schema Validation -> Verify Evidence -> SQLite Persistence.
"""
import logging
import time

from sqlalchemy.orm import Session

from app.adapters.db.models import ReviewRecord
from app.adapters.db.repository import ReviewRepository
from app.adapters.llm_client import BaseLLMClient, get_llm_client
from app.config import Settings, get_settings
from app.schemas.llm import LLMReviewResponse
from app.services.ingestion import IngestionService
from app.services.sanitizer import InputSanitizerService

logger = logging.getLogger(__name__)


class ReviewService:
    """Orchestrates pull request ingestion, defensive containment, AI analysis, and persistence."""

    def __init__(
        self,
        settings: Settings | None = None,
        ingestion_service: IngestionService | None = None,
        sanitizer_service: InputSanitizerService | None = None,
        llm_client: BaseLLMClient | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.ingestion_service = ingestion_service or IngestionService()
        self.sanitizer_service = sanitizer_service or InputSanitizerService()
        self.llm_client = llm_client or get_llm_client(self.settings)

    async def review_pull_request(
        self,
        pr_url: str,
        session: Session,
    ) -> ReviewRecord:
        """Execute end-to-end review lifecycle and store results."""
        # 1. Ingest PR metadata and diff (validates URL, enforces size caps)
        logger.info("Ingesting pull request from URL: %s", pr_url)
        payload = await self.ingestion_service.ingest_from_url(pr_url)

        # 2. Sanitize & wrap in strict XML containment envelope
        sanitized_envelope = self.sanitizer_service.wrap_in_envelope(
            pr_title=payload.title,
            pr_body=payload.body,
            raw_diff=payload.raw_diff,
        )

        # 3. LLM Analysis (includes rule check facts, schema validation, and repair retry)
        start_time = time.perf_counter()
        provider_name = self.settings.LLM_PROVIDER
        model_name = getattr(self.llm_client, "model", "mock-rules")

        logger.info("Invoking LLM analysis via provider '%s' (model: '%s')", provider_name, model_name)
        llm_response: LLMReviewResponse = await self.llm_client.analyze(
            sanitized_envelope=sanitized_envelope,
            raw_diff=payload.raw_diff,
        )
        latency_ms = max(1, int((time.perf_counter() - start_time) * 1000))

        # 4. Verify evidence: Drop any finding without genuine diff quote
        verified_findings = self.sanitizer_service.verify_evidence(
            findings=llm_response.findings,
            raw_diff=payload.raw_diff,
        )

        # 5. Calculate rough telemetry estimates
        # ~4 chars per token heuristic for input + output
        estimated_tokens = max(50, (len(sanitized_envelope) + len(str(llm_response))) // 4)
        # Pricing heuristic: $0.15 per 1M input tokens for mini models, $0 for mock
        cost_per_token = 0.0000003 if provider_name == "openai" else 0.0
        est_cost = round(estimated_tokens * cost_per_token, 6)

        # 6. Persist to SQLite using ReviewRepository
        repo = ReviewRepository(session)
        review_record = repo.create_review(
            repo_full_name=f"{payload.pr_identifier.owner}/{payload.pr_identifier.repo}",
            pr_number=payload.pr_identifier.pull_number,
            pr_title=payload.title,
            pr_description=payload.body,
            author_username=payload.author,
            base_commit_sha=payload.base_sha,
            head_commit_sha=payload.head_sha,
            raw_diff=payload.raw_diff,
            summary=llm_response.summary,
            findings=verified_findings,
            is_truncated=payload.is_truncated,
            provider=provider_name,
            model=model_name,
            latency_ms=latency_ms,
            tokens=estimated_tokens,
            est_cost=est_cost,
        )

        session.commit()
        logger.info(
            "Review #%s created successfully with %d verified finding(s). Status: %s",
            review_record.id,
            len(verified_findings),
            review_record.status,
        )
        return review_record

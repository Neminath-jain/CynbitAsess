import json

import httpx
import pytest
from sqlalchemy.orm import Session

from app.adapters.db.repository import ReviewRepository
from app.adapters.db.session import DatabaseManager
from app.adapters.github_client import GitHubClient
from app.adapters.llm_client import MockLLMClient
from app.config import Settings
from app.domain.exceptions import AppError
from app.services.ingestion import IngestionService
from app.services.review_service import ReviewService
from app.services.sanitizer import InputSanitizerService
from tests.fixtures.recorded_github_pr import RECORDED_DIFF_42, RECORDED_METADATA_42


@pytest.fixture
def isolated_db_session() -> Session:
    """Provide clean in-memory SQLite session."""
    test_settings = Settings(DATABASE_URL="sqlite:///:memory:")
    manager = DatabaseManager(test_settings)
    manager.create_tables()
    session = manager.session_factory()
    try:
        yield session
    finally:
        session.close()
        manager.drop_tables()


@pytest.mark.asyncio
async def test_review_service_end_to_end_orchestration(isolated_db_session: Session) -> None:
    """Verify ReviewService orchestrates ingestion, sanitization, LLM, evidence check, and persistence."""
    def mock_github_handler(request: httpx.Request) -> httpx.Response:
        url_str = str(request.url)
        if url_str.endswith("/pulls/42"):
            if "application/vnd.github.v3.diff" in request.headers.get("Accept", ""):
                return httpx.Response(200, text=RECORDED_DIFF_42)
            return httpx.Response(200, text=json.dumps(RECORDED_METADATA_42))
        return httpx.Response(404, text=json.dumps({"message": "Not Found"}))

    transport = httpx.MockTransport(mock_github_handler)
    async with httpx.AsyncClient(transport=transport) as mock_client:
        gh_client = GitHubClient(http_client=mock_client)
        ingestion_service = IngestionService(github_client=gh_client)
        sanitizer_service = InputSanitizerService()
        llm_client = MockLLMClient()

        review_service = ReviewService(
            ingestion_service=ingestion_service,
            sanitizer_service=sanitizer_service,
            llm_client=llm_client,
        )

        review = await review_service.review_pull_request(
            pr_url="https://github.com/cynbit/bitelevate-sample/pull/42",
            session=isolated_db_session,
        )

        # Assertions on returned review
        assert review.id is not None
        assert review.repo_full_name == "cynbit/bitelevate-sample"
        assert review.pr_number == 42
        assert review.status == "PENDING_APPROVAL"
        assert review.provider == "mock"
        assert review.model == "mock-rules"
        assert review.latency_ms >= 1
        assert review.tokens >= 50

        # Verify findings persisted and verified
        assert len(review.findings) > 0
        for f in review.findings:
            assert f.evidence_quote in RECORDED_DIFF_42

        # Verify persistent in database
        repo = ReviewRepository(isolated_db_session)
        stored_review = repo.get_review(review.id)
        assert stored_review is not None
        assert len(stored_review.findings) == len(review.findings)


@pytest.mark.asyncio
async def test_review_service_rejects_invalid_url(isolated_db_session: Session) -> None:
    """Verify invalid URL fails fast before hitting LLM or DB."""
    review_service = ReviewService()
    with pytest.raises(AppError):
        await review_service.review_pull_request(
            pr_url="https://gitlab.com/cynbit/repo/pull/1",
            session=isolated_db_session,
        )

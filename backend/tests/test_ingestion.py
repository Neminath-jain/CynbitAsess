"""Unit tests for GitHub PR URL parsing, ingestion, and size cap enforcement."""
import json
import httpx
import pytest
from app.adapters.github_client import GitHubClient
from app.domain.exceptions import AppError, EntityNotFoundError
from app.schemas.github import PRIdentifier
from app.services.ingestion import IngestionService
from tests.fixtures.recorded_github_pr import RECORDED_DIFF_42, RECORDED_METADATA_42


def test_pr_identifier_valid_urls() -> None:
    """Verify strict parsing of valid GitHub pull request URLs."""
    valid_url = "https://github.com/cynbit/bitelevate-sample/pull/42"
    ident = PRIdentifier.from_url(valid_url)
    assert ident.owner == "cynbit"
    assert ident.repo == "bitelevate-sample"
    assert ident.pull_number == 42
    assert ident.raw_url == valid_url

    # Trailing slash support
    ident_slash = PRIdentifier.from_url("https://github.com/cynbit/repo.core/pull/101/")
    assert ident_slash.owner == "cynbit"
    assert ident_slash.repo == "repo.core"
    assert ident_slash.pull_number == 101


@pytest.mark.parametrize(
    "invalid_url",
    [
        "http://github.com/cynbit/repo/pull/1",  # Insecure http
        "https://gitlab.com/cynbit/repo/pull/1",  # Non-github host
        "https://github.com/cynbit/repo/issues/1",  # Issues instead of pull
        "https://github.com/cynbit/repo",  # Missing pull path
        "https://github.com/cynbit/repo/pull/0",  # Zero pull number
        "https://github.com/cynbit/repo/pull/notanumber",  # Non-numeric pull
        "",  # Empty
    ],
)
def test_pr_identifier_invalid_urls_rejected(invalid_url: str) -> None:
    """Verify that malformed or unsupported URLs are rejected with AppError."""
    with pytest.raises(AppError):
        PRIdentifier.from_url(invalid_url)


@pytest.mark.asyncio
async def test_ingest_from_url_with_recorded_fixture() -> None:
    """Verify ingestion service fetches metadata and diff using recorded mock transport."""
    def mock_handler(request: httpx.Request) -> httpx.Response:
        url_str = str(request.url)
        if url_str.endswith("/pulls/42"):
            if "application/vnd.github.v3.diff" in request.headers.get("Accept", ""):
                return httpx.Response(200, text=RECORDED_DIFF_42)
            return httpx.Response(200, text=json.dumps(RECORDED_METADATA_42))
        return httpx.Response(404, text=json.dumps({"message": "Not Found"}))

    transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=transport) as mock_client:
        github_client = GitHubClient(http_client=mock_client)
        ingestion_service = IngestionService(github_client=github_client)

        payload = await ingestion_service.ingest_from_url(
            "https://github.com/cynbit/bitelevate-sample/pull/42"
        )

        assert payload.title == "Add order processing endpoint and models"
        assert payload.author == "intern_dev"
        assert payload.pr_identifier.pull_number == 42
        assert payload.base_sha.startswith("a1b2c3d4")
        assert payload.head_sha.startswith("f9e8d7c6")
        assert "class OrderItem:" in payload.raw_diff
        assert payload.is_truncated is False
        assert payload.files_count == 2


@pytest.mark.asyncio
async def test_ingestion_size_cap_truncation() -> None:
    """Verify that diffs exceeding the size cap are cleanly truncated and marked."""
    large_diff = "diff --git a/test.py b/test.py\n" + ("+ line of added code\n" * 50)

    def mock_handler(request: httpx.Request) -> httpx.Response:
        url_str = str(request.url)
        if url_str.endswith("/pulls/1"):
            if "diff" in request.headers.get("Accept", ""):
                return httpx.Response(200, text=large_diff)
            return httpx.Response(200, text=json.dumps({"title": "Large PR", "user": {"login": "dev"}}))
        return httpx.Response(404)

    transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=transport) as mock_client:
        github_client = GitHubClient(http_client=mock_client)
        # Cap at 100 characters
        service = IngestionService(github_client=github_client, max_diff_chars=100)

        payload = await service.ingest_from_url("https://github.com/cynbit/bitelevate/pull/1")

        assert payload.is_truncated is True
        assert "[TRUNCATED: Exceeded pull request diff character limit]" in payload.raw_diff
        assert len(payload.raw_diff) < 200


@pytest.mark.asyncio
async def test_ingestion_pr_not_found_raises_entity_not_found() -> None:
    """Verify 404 response raises EntityNotFoundError."""
    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text=json.dumps({"message": "Not Found"}))

    transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=transport) as mock_client:
        github_client = GitHubClient(http_client=mock_client)
        service = IngestionService(github_client=github_client)

        with pytest.raises(EntityNotFoundError):
            await service.ingest_from_url("https://github.com/cynbit/missing-repo/pull/999")

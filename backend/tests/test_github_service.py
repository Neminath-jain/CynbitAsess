"""Comprehensive unit tests for GitHub PR ingestion service using recorded JSON fixtures."""
import json
from typing import Any

import httpx
import pytest

from app.domain.exceptions import (
    AppError,
    EntityNotFoundError,
    GitHubIntegrationError,
    SecurityViolationError,
)
from app.services.github import GitHubService, parse_github_pr_url


def test_parse_github_pr_url_strictness() -> None:
    """Verify strict parsing: accepts only https://github.com/{owner}/{repo}/pull/{number}."""
    # Valid URLs
    owner, repo, num = parse_github_pr_url("https://github.com/cynbit/bitelevate/pull/42")
    assert (owner, repo, num) == ("cynbit", "bitelevate", 42)

    owner2, repo2, num2 = parse_github_pr_url("https://www.github.com/org-name/repo.name/pull/999/")
    assert (owner2, repo2, num2) == ("org-name", "repo.name", 999)

    # Hostile URLs & invalid hosts
    with pytest.raises(AppError, match="Invalid host"):
        parse_github_pr_url("https://evil.com/cynbit/bitelevate/pull/42")

    with pytest.raises(AppError, match="Invalid host"):
        parse_github_pr_url("https://github.com.attacker.com/cynbit/bitelevate/pull/42")

    # Insecure scheme
    with pytest.raises(AppError, match="Invalid URL protocol"):
        parse_github_pr_url("http://github.com/cynbit/bitelevate/pull/42")

    # Hostile paths / non-PR paths
    with pytest.raises(AppError, match="Invalid GitHub PR path"):
        parse_github_pr_url("https://github.com/cynbit/bitelevate/issues/42")

    with pytest.raises(AppError, match="Invalid GitHub PR path"):
        parse_github_pr_url("https://github.com/cynbit/bitelevate/pull/0")

    with pytest.raises(AppError, match="Invalid GitHub PR path"):
        parse_github_pr_url("https://github.com/cynbit/bitelevate/pull/notanumber")

    with pytest.raises(AppError, match="non-empty string"):
        parse_github_pr_url("")


@pytest.mark.asyncio
async def test_empty_pr_ingestion() -> None:
    """Verify empty PR (0 changed files, 0 commits) returns empty files and commit lists."""
    metadata_fixture = {
        "title": "Empty Initial PR",
        "body": "Branch initialization with no changes yet.",
        "base": {"ref": "main", "sha": "base1234"},
        "head": {"ref": "feature", "sha": "head5678", "repo": {"full_name": "cynbit/bitelevate"}},
    }

    def mock_handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "/commits" in url or "/files" in url:
            return httpx.Response(200, json=[])
        if url.endswith("/pulls/10"):
            return httpx.Response(200, json=metadata_fixture)
        return httpx.Response(404)

    transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        service = GitHubService(http_client=client)
        ctx = await service.fetch_pr_context("https://github.com/cynbit/bitelevate/pull/10")

        assert ctx.title == "Empty Initial PR"
        assert ctx.body == "Branch initialization with no changes yet."
        assert ctx.base == "main"
        assert ctx.head == "feature"
        assert ctx.files == []
        assert ctx.commit_messages == []
        assert ctx.is_fork is False
        assert ctx.is_truncated is False


@pytest.mark.asyncio
async def test_fork_pr_ingestion() -> None:
    """Verify fork PR detection when head repo differs from base repo."""
    fork_metadata_fixture = {
        "title": "Intern Contribution from Fork",
        "body": "Fixing issue from fork repository.",
        "base": {"ref": "main", "sha": "base1111", "repo": {"full_name": "cynbit/bitelevate"}},
        "head": {"ref": "fix-typo", "sha": "head2222", "repo": {"full_name": "intern-dev/bitelevate"}},
    }
    commits_fixture = [
        {"commit": {"message": "Fix typo in docstring"}},
    ]
    files_fixture = [
        {
            "filename": "app/main.py",
            "status": "modified",
            "patch": "@@ -1,2 +1,2 @@\n-old code\n+new code\n",
            "additions": 1,
            "deletions": 1,
        }
    ]

    def mock_handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "/pulls/15/commits" in url:
            return httpx.Response(200, json=commits_fixture)
        if "/pulls/15/files" in url:
            return httpx.Response(200, json=files_fixture)
        if url.endswith("/pulls/15"):
            return httpx.Response(200, json=fork_metadata_fixture)
        return httpx.Response(404)

    transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        service = GitHubService(http_client=client)
        ctx = await service.fetch_pr_context("https://github.com/cynbit/bitelevate/pull/15")

        assert ctx.is_fork is True
        assert len(ctx.files) == 1
        assert ctx.files[0].filename == "app/main.py"
        assert ctx.commit_messages == ["Fix typo in docstring"]


@pytest.mark.asyncio
async def test_skips_binary_files_and_lockfiles() -> None:
    """Verify binary files (.png, .so, status=binary) and lockfiles (package-lock.json) are skipped."""
    metadata = {
        "title": "Assets and Dependencies",
        "base": {"ref": "main"},
        "head": {"ref": "assets"},
    }
    files_fixture = [
        # Binary extension
        {"filename": "docs/logo.png", "status": "added", "patch": "Binary file differs"},
        # Status=binary
        {"filename": "lib/native.so", "status": "binary", "patch": None},
        # Lockfile
        {"filename": "package-lock.json", "status": "modified", "patch": "@@ -1 +1 @@\n-v1\n+v2"},
        {"filename": "poetry.lock", "status": "modified", "patch": "@@ -1 +1 @@\n-v1\n+v2"},
        # Legitimate source file
        {"filename": "app/routes.py", "status": "modified", "patch": "@@ -1 +1 @@\n-pass\n+return True"},
    ]

    def mock_handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "/files" in url:
            return httpx.Response(200, json=files_fixture)
        if "/commits" in url:
            return httpx.Response(200, json=[])
        return httpx.Response(200, json=metadata)

    transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        service = GitHubService(http_client=client)
        ctx = await service.fetch_pr_context("https://github.com/cynbit/bitelevate/pull/20")

        assert len(ctx.files) == 1
        assert ctx.files[0].filename == "app/routes.py"


@pytest.mark.asyncio
async def test_oversized_diff_capping() -> None:
    """Verify cumulative diff exceeding max_diff_chars is capped with is_truncated=True."""
    metadata = {"title": "Large Diff PR", "base": {"ref": "main"}, "head": {"ref": "big"}}
    large_patch = "+" + "A" * 600 + "\n"
    files_fixture = [
        {"filename": "app/file1.py", "status": "added", "patch": large_patch},
        {"filename": "app/file2.py", "status": "added", "patch": large_patch},
    ]

    def mock_handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "/files" in url:
            return httpx.Response(200, json=files_fixture)
        if "/commits" in url:
            return httpx.Response(200, json=[])
        return httpx.Response(200, json=metadata)

    transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        # Cap at 500 characters
        service = GitHubService(http_client=client, max_diff_chars=500)
        ctx = await service.fetch_pr_context("https://github.com/cynbit/bitelevate/pull/30")

        assert ctx.is_truncated is True
        assert ctx.total_diff_size <= 600


@pytest.mark.asyncio
async def test_404_not_found_handling() -> None:
    """Verify 404 response raises EntityNotFoundError."""
    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"message": "Not Found"})

    transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        service = GitHubService(http_client=client)
        with pytest.raises(EntityNotFoundError):
            await service.fetch_pr_context("https://github.com/cynbit/bitelevate/pull/404")


@pytest.mark.asyncio
async def test_403_rate_limit_handling() -> None:
    """Verify 403 rate limit response raises GitHubIntegrationError."""
    def mock_handler(request: httpx.Request) -> httpx.Response:
        headers = {
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": "1730000000",
            "Retry-After": "10",
        }
        return httpx.Response(403, headers=headers, json={"message": "API rate limit exceeded"})

    transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        service = GitHubService(http_client=client)
        with pytest.raises(GitHubIntegrationError, match="rate limit exceeded"):
            await service.fetch_pr_context("https://github.com/cynbit/bitelevate/pull/42")


@pytest.mark.asyncio
async def test_cross_host_redirect_rejection() -> None:
    """Verify redirects pointing to external/untrusted hosts are aborted with SecurityViolationError."""
    def mock_handler(request: httpx.Request) -> httpx.Response:
        # Redirect to malicious external endpoint
        return httpx.Response(
            302,
            headers={"Location": "https://attacker-credential-stealer.com/harvest"},
        )

    transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        service = GitHubService(http_client=client)
        with pytest.raises(SecurityViolationError, match="Refusing to follow redirect to external/untrusted host"):
            await service.fetch_pr_context("https://github.com/cynbit/bitelevate/pull/50")

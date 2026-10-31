"""GitHub PR Ingestion Service.

Strictly validates github.com PR URLs, fetches PR metadata, commits, and changed file
patches via the GitHub REST API using httpx with pagination, rate-limit backoff,
lockfile/binary filtering, size capping, and cross-host redirect protection.
"""
import asyncio
import logging
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx

from app.config import Settings, get_settings
from app.domain.exceptions import (
    AppError,
    EntityNotFoundError,
    GitHubIntegrationError,
    SecurityViolationError,
)
from app.schemas.github import FilePatch, PullRequestContext

logger = logging.getLogger(__name__)

# Standard lockfile filenames to exclude from code review diffs
LOCKFILES: set[str] = {
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
    "pipfile.lock",
    "uv.lock",
    "cargo.lock",
    "composer.lock",
    "gemfile.lock",
    "go.sum",
    "flake.lock",
}

# Standard binary file extensions to exclude from code review diffs
BINARY_EXTENSIONS: set[str] = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".webp", ".bmp", ".tiff",
    ".pdf", ".zip", ".tar", ".gz", ".bz2", ".xz", ".7z", ".rar",
    ".exe", ".dll", ".so", ".dylib", ".bin", ".iso", ".dat",
    ".pyc", ".pyo", ".class", ".jar", ".war",
    ".woff", ".woff2", ".ttf", ".eot", ".otf",
    ".mp3", ".mp4", ".wav", ".avi", ".mov", ".mkv",
}

GITHUB_PR_URL_REGEX = re.compile(
    r"^/([a-zA-Z0-9_\-\.]+)/([a-zA-Z0-9_\-\.]+)/pull/([1-9]\d*)/?$"
)


def parse_github_pr_url(url: str) -> tuple[str, str, int]:
    """Strictly parse a GitHub pull request URL.

    Requirements:
    - Protocol must be https.
    - Host must be strictly 'github.com' or 'www.github.com'.
    - Path must match /owner/repo/pull/number.
    Rejects any non-GitHub hosts, subdomains, hostile URLs, or invalid paths.
    """
    if not url or not isinstance(url, str):
        raise AppError("PR URL must be a non-empty string.")

    cleaned_url = url.strip()
    parsed = urlparse(cleaned_url)

    if parsed.scheme.lower() != "https":
        raise AppError(f"Invalid URL protocol: '{parsed.scheme}'. Only 'https' is permitted.")

    # Strict host validation - prevent attacker.com or github.com.evil.com
    hostname = (parsed.hostname or "").lower()
    if hostname not in ("github.com", "www.github.com"):
        raise AppError(f"Invalid host: '{hostname}'. Only 'github.com' is supported.")

    match = GITHUB_PR_URL_REGEX.match(parsed.path)
    if not match:
        raise AppError(
            f"Invalid GitHub PR path: '{parsed.path}'. Expected '/{{owner}}/{{repo}}/pull/{{number}}'."
        )

    owner, repo, num_str = match.groups()
    return owner, repo, int(num_str)


class GitHubService:
    """Service fetching and processing pull request data from GitHub REST API."""

    def __init__(
        self,
        settings: Settings | None = None,
        http_client: httpx.AsyncClient | None = None,
        max_diff_chars: int | None = None,
        token: str | None = None,
        max_retries: int = 2,
    ) -> None:
        self.settings = settings or get_settings()
        self._custom_client = http_client
        self.max_diff_chars = max_diff_chars or self.settings.MAX_DIFF_CHARACTERS
        self.token = token or self.settings.GITHUB_TOKEN
        self.max_retries = max_retries
        self.base_url = "https://api.github.com"

    def _get_headers(self, accept: str = "application/vnd.github.v3+json") -> dict[str, str]:
        headers = {
            "Accept": accept,
            "User-Agent": "BitElevate-PR-Review-Copilot/1.0",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _check_redirect_safety(self, response: httpx.Response) -> None:
        """Verify redirect location does not point to an untrusted external host."""
        if response.status_code in (301, 302, 303, 307, 308):
            location = response.headers.get("Location")
            if location:
                parsed_loc = urlparse(location)
                loc_host = (parsed_loc.hostname or "").lower()
                if loc_host and loc_host not in ("api.github.com", "github.com", "www.github.com"):
                    raise SecurityViolationError(
                        f"Refusing to follow redirect to external/untrusted host: '{location}'."
                    )

    async def _request(
        self,
        client: httpx.AsyncClient,
        url: str,
        params: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """Perform HTTP GET with rate-limit header inspection and redirect safety checks."""
        headers = self._get_headers()
        retry_count = 0

        while True:
            response = await client.get(
                url,
                headers=headers,
                params=params,
                follow_redirects=False,
            )

            # Security check on redirects
            self._check_redirect_safety(response)

            # Handle Rate Limiting (403 with X-RateLimit-Remaining == 0)
            if response.status_code == 403:
                remaining = response.headers.get("X-RateLimit-Remaining")
                retry_after = response.headers.get("Retry-After")
                reset_time = response.headers.get("X-RateLimit-Reset")

                is_rate_limited = remaining == "0" or "rate limit" in response.text.lower()
                if is_rate_limited:
                    wait_seconds = int(retry_after) if retry_after and retry_after.isdigit() else 1
                    if retry_count < self.max_retries and wait_seconds <= 2:
                        retry_count += 1
                        logger.warning("GitHub rate limit hit. Backing off for %ds...", wait_seconds)
                        await asyncio.sleep(wait_seconds)
                        continue

                    raise GitHubIntegrationError(
                        f"GitHub API rate limit exceeded. Reset at {reset_time or 'unknown'}. "
                        "Please configure a valid GITHUB_TOKEN."
                    )

            if response.status_code == 404:
                raise EntityNotFoundError("Requested GitHub resource was not found (404).")

            if response.status_code >= 400:
                raise GitHubIntegrationError(
                    f"GitHub API error: HTTP {response.status_code} - {response.text[:200]}"
                )

            return response

    async def fetch_pr_context(self, pr_url: str) -> PullRequestContext:
        """Parse URL strictly, fetch PR metadata, commits, and file patches, and apply filters."""
        owner, repo, pull_number = parse_github_pr_url(pr_url)

        if self._custom_client:
            return await self._fetch_context_with_client(self._custom_client, owner, repo, pull_number)
        else:
            async with httpx.AsyncClient(timeout=30.0) as client:
                return await self._fetch_context_with_client(client, owner, repo, pull_number)

    async def _fetch_context_with_client(
        self,
        client: httpx.AsyncClient,
        owner: str,
        repo: str,
        pull_number: int,
    ) -> PullRequestContext:
        # 1. Fetch Pull Request Metadata
        pr_url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pull_number}"
        meta_resp = await self._request(client, pr_url)
        metadata: dict[str, Any] = meta_resp.json()

        title = metadata.get("title") or "Untitled Pull Request"
        body = metadata.get("body") or ""

        base_ref = metadata.get("base", {}).get("ref") or metadata.get("base", {}).get("sha", "")
        head_ref = metadata.get("head", {}).get("ref") or metadata.get("head", {}).get("sha", "")

        # Check if fork PR
        head_repo = metadata.get("head", {}).get("repo")
        base_repo = metadata.get("base", {}).get("repo")
        is_fork = False
        if head_repo and base_repo:
            is_fork = head_repo.get("full_name") != base_repo.get("full_name")

        # 2. Fetch Commit Messages
        commits_url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pull_number}/commits"
        try:
            commits_resp = await self._request(client, commits_url, params={"per_page": 50})
            commits_data: list[dict[str, Any]] = commits_resp.json()
            commit_messages = [
                c.get("commit", {}).get("message", "").strip()
                for c in commits_data
                if c.get("commit", {}).get("message")
            ]
        except Exception as e:
            logger.warning("Failed to retrieve commit messages for PR #%d: %s", pull_number, e)
            commit_messages = []

        # 3. Fetch Changed Files & Patches with Pagination
        files_url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pull_number}/files"
        file_patches: list[FilePatch] = []
        page = 1
        per_page = 100
        total_diff_size = 0
        is_truncated = False

        while True:
            files_resp = await self._request(client, files_url, params={"page": page, "per_page": per_page})
            files_data: list[dict[str, Any]] = files_resp.json()

            if not files_data:
                break

            for f in files_data:
                filename = f.get("filename", "")
                raw_patch = f.get("patch")
                status = f.get("status", "modified")
                additions = f.get("additions", 0)
                deletions = f.get("deletions", 0)

                # Skip binary files
                if f.get("status") == "binary" or raw_patch is None:
                    continue

                path_obj = Path(filename)
                if path_obj.suffix.lower() in BINARY_EXTENSIONS:
                    continue

                # Skip lockfiles
                if path_obj.name.lower() in LOCKFILES:
                    continue

                patch_len = len(raw_patch)
                if total_diff_size + patch_len > self.max_diff_chars:
                    remaining_allowed = self.max_diff_chars - total_diff_size
                    if remaining_allowed > 100:
                        trimmed_patch = raw_patch[:remaining_allowed] + "\n[TRUNCATED: File patch capped]"
                        file_patches.append(
                            FilePatch(
                                filename=filename,
                                status=status,
                                patch=trimmed_patch,
                                additions=additions,
                                deletions=deletions,
                            )
                        )
                        total_diff_size += len(trimmed_patch)
                    is_truncated = True
                    break
                else:
                    file_patches.append(
                        FilePatch(
                            filename=filename,
                            status=status,
                            patch=raw_patch,
                            additions=additions,
                            deletions=deletions,
                        )
                    )
                    total_diff_size += patch_len

            if is_truncated or len(files_data) < per_page:
                break

            page += 1

        return PullRequestContext(
            title=title,
            body=body,
            base=base_ref,
            head=head_ref,
            files=file_patches,
            commit_messages=commit_messages,
            is_fork=is_fork,
            is_truncated=is_truncated,
            total_diff_size=total_diff_size,
        )

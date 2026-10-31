"""GitHub API client adapter for fetching PR metadata and raw diffs.

Supports dependency-injected httpx.AsyncClient for zero-network testing with mock transports.
"""
import logging
from typing import Any

import httpx

from app.config import Settings, get_settings
from app.domain.exceptions import EntityNotFoundError, GitHubIntegrationError

logger = logging.getLogger(__name__)


class GitHubClient:
    """Client for GitHub REST API operations."""

    def __init__(
        self,
        settings: Settings | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self._custom_client = http_client
        self.base_url = "https://api.github.com"

    def _get_headers(self, accept: str = "application/vnd.github.v3+json") -> dict[str, str]:
        """Construct standard authorization and content negotiation headers."""
        headers = {
            "Accept": accept,
            "User-Agent": "BitElevate-PR-Review-Copilot/1.0",
        }
        if self.settings.GITHUB_TOKEN:
            headers["Authorization"] = f"Bearer {self.settings.GITHUB_TOKEN}"
        return headers

    async def fetch_pr_metadata(self, owner: str, repo: str, pull_number: int) -> dict[str, Any]:
        """Fetch pull request metadata JSON from GitHub API."""
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pull_number}"
        headers = self._get_headers("application/vnd.github.v3+json")

        if self._custom_client:
            response = await self._custom_client.get(url, headers=headers)
        else:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.get(url, headers=headers)

        if response.status_code == 404:
            raise EntityNotFoundError(f"Pull request #{pull_number} in '{owner}/{repo}' not found on GitHub.")
        if response.status_code != 200:
            logger.error("GitHub API error fetching metadata: status=%d, body=%s", response.status_code, response.text)
            raise GitHubIntegrationError(
                f"GitHub API returned error status {response.status_code} while fetching pull request metadata."
            )

        data: dict[str, Any] = response.json()
        return data

    async def fetch_pr_diff(self, owner: str, repo: str, pull_number: int) -> str:
        """Fetch unified git diff string from GitHub API."""
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pull_number}"
        headers = self._get_headers("application/vnd.github.v3.diff")

        if self._custom_client:
            response = await self._custom_client.get(url, headers=headers)
        else:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.get(url, headers=headers)

        if response.status_code == 404:
            raise EntityNotFoundError(f"Pull request #{pull_number} diff in '{owner}/{repo}' not found on GitHub.")
        if response.status_code != 200:
            logger.error("GitHub API error fetching diff: status=%d, body=%s", response.status_code, response.text)
            raise GitHubIntegrationError(
                f"GitHub API returned error status {response.status_code} while fetching pull request diff."
            )

        return response.text

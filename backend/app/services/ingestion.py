"""GitHub Pull Request ingestion service.

Performs URL validation, metadata/diff retrieval via GitHub API adapter,
and strict size cap enforcement before handover to the review pipeline.
"""
import logging

from app.adapters.github_client import GitHubClient
from app.config import get_settings
from app.schemas.github import IngestionPayload, PRIdentifier

logger = logging.getLogger(__name__)


class IngestionService:
    """Service orchestrating PR validation, ingestion, and size cap enforcement."""

    def __init__(
        self,
        github_client: GitHubClient | None = None,
        max_diff_chars: int | None = None,
    ) -> None:
        self.github_client = github_client or GitHubClient()
        settings = get_settings()
        self.max_diff_chars = max_diff_chars or settings.MAX_DIFF_CHARACTERS

    async def ingest_from_url(self, pr_url: str) -> IngestionPayload:
        """Parse github.com URL, fetch PR metadata and diff, and enforce size caps."""
        identifier = PRIdentifier.from_url(pr_url)

        metadata = await self.github_client.fetch_pr_metadata(
            owner=identifier.owner,
            repo=identifier.repo,
            pull_number=identifier.pull_number,
        )

        raw_diff = await self.github_client.fetch_pr_diff(
            owner=identifier.owner,
            repo=identifier.repo,
            pull_number=identifier.pull_number,
        )

        is_truncated = False
        effective_diff = raw_diff

        # Enforce size cap
        if len(raw_diff) > self.max_diff_chars:
            logger.warning(
                "Ingested PR diff length (%d) exceeded cap (%d). Truncating.",
                len(raw_diff),
                self.max_diff_chars,
            )
            cut_idx = raw_diff[: self.max_diff_chars].rfind("\n")
            effective_diff = (
                raw_diff[:cut_idx] if cut_idx != -1 else raw_diff[: self.max_diff_chars]
            )
            effective_diff += "\n[TRUNCATED: Exceeded pull request diff character limit]"
            is_truncated = True

        # Count affected files
        files_count = metadata.get("changed_files", 0)
        if files_count == 0:
            files_count = effective_diff.count("diff --git")

        title = metadata.get("title") or "Untitled Pull Request"
        body = metadata.get("body") or ""
        author = metadata.get("user", {}).get("login", "unknown_intern")
        base_sha = metadata.get("base", {}).get("sha", "000000000000")
        head_sha = metadata.get("head", {}).get("sha", "111111111111")

        return IngestionPayload(
            pr_identifier=identifier,
            title=title,
            body=body,
            author=author,
            base_sha=base_sha,
            head_sha=head_sha,
            raw_diff=effective_diff,
            is_truncated=is_truncated,
            files_count=files_count,
        )

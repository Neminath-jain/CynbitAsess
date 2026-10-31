"""Schemas for GitHub pull request ingestion and URL validation."""
import re
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.exceptions import AppError

GITHUB_PR_REGEX = re.compile(
    r"^/([a-zA-Z0-9_\-\.]+)/([a-zA-Z0-9_\-\.]+)/pull/([1-9]\d*)/?$"
)


class PRIdentifier(BaseModel):
    """Strongly-typed, validated GitHub Pull Request identifier."""

    model_config = ConfigDict(validate_assignment=True)

    owner: str = Field(min_length=1, max_length=100)
    repo: str = Field(min_length=1, max_length=100)
    pull_number: int = Field(ge=1)
    raw_url: str

    @classmethod
    def from_url(cls, url: str) -> "PRIdentifier":
        """Strictly parse and validate a github.com pull request URL.

        Requires https://github.com/{owner}/{repo}/pull/{pull_number}.
        Rejects non-github hosts, insecure protocols, and non-PR paths.
        """
        if not url or not isinstance(url, str):
            raise AppError("PR URL must be a non-empty string.")

        parsed = urlparse(url.strip())
        if parsed.scheme.lower() != "https":
            raise AppError(f"Invalid URL protocol: '{parsed.scheme}'. Only 'https' is permitted.")

        if parsed.netloc.lower() not in ("github.com", "www.github.com"):
            raise AppError(f"Invalid host: '{parsed.netloc}'. Only 'github.com' is supported.")

        match = GITHUB_PR_REGEX.match(parsed.path)
        if not match:
            raise AppError(
                f"Invalid GitHub PR path: '{parsed.path}'. Expected '/{{owner}}/{{repo}}/pull/{{number}}'."
            )

        owner, repo, pr_num_str = match.groups()
        return cls(
            owner=owner,
            repo=repo,
            pull_number=int(pr_num_str),
            raw_url=url.strip(),
        )


class IngestionPayload(BaseModel):
    """Normalized payload resulting from PR metadata and diff ingestion."""

    model_config = ConfigDict(validate_assignment=True)

    pr_identifier: PRIdentifier
    title: str = Field(min_length=1)
    body: str = Field(default="")
    author: str = Field(min_length=1)
    base_sha: str = Field(min_length=4)
    head_sha: str = Field(min_length=4)
    raw_diff: str
    is_truncated: bool = False
    files_count: int = 0

    @field_validator("title", mode="before")
    @classmethod
    def sanitize_empty_title(cls, v: str) -> str:
        return v if v and v.strip() else "Untitled Pull Request"


class FilePatch(BaseModel):
    """Patch information for a single modified file in a pull request."""

    model_config = ConfigDict(validate_assignment=True)

    filename: str
    status: str
    patch: str
    additions: int = 0
    deletions: int = 0


class PullRequestContext(BaseModel):
    """Typed pull request context containing metadata, patches, and commit history."""

    model_config = ConfigDict(validate_assignment=True)

    title: str
    body: str = ""
    base: str
    head: str
    files: list[FilePatch] = Field(default_factory=list)
    commit_messages: list[str] = Field(default_factory=list)
    is_fork: bool = False
    is_truncated: bool = False
    total_diff_size: int = 0


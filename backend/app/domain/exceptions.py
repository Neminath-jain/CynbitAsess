"""Domain-level exception hierarchy.

Ensures structured, safe error reporting across all layers.
"""
import uuid


class AppError(Exception):
    """Base application exception with safe public error message and tracing ID."""

    def __init__(self, message: str, error_id: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.error_id = error_id or str(uuid.uuid4())


class EntityNotFoundError(AppError):
    """Raised when a requested domain entity (review, comment, file) is not found."""
    pass


class InvalidStateTransitionError(AppError):
    """Raised when an illegal lifecycle state transition is attempted."""
    pass


class SecurityViolationError(AppError):
    """Raised when an untrusted input breaches safety constraints or prompt injection defenses."""
    pass


class DiffParsingError(AppError):
    """Raised when a git diff cannot be safely or syntactically parsed."""
    pass


class LLMServiceError(AppError):
    """Raised when LLM invocation fails or returns unrecoverable schema violations."""
    pass


class GitHubIntegrationError(AppError):
    """Raised when upstream GitHub API calls fail or return error responses."""
    pass

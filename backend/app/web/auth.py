"""Authentication and authorization dependencies for mentor operations."""
import secrets
from typing import Annotated

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer

from app.config import Settings, get_settings

mentor_api_key_header = APIKeyHeader(name="X-Mentor-Token", auto_error=False)
mentor_bearer_scheme = HTTPBearer(auto_error=False)


def get_mentor_token_from_request(
    header_token: Annotated[str | None, Security(mentor_api_key_header)] = None,
    bearer_creds: Annotated[HTTPAuthorizationCredentials | None, Security(mentor_bearer_scheme)] = None,
) -> str | None:
    """Extract mentor token from either X-Mentor-Token header or Bearer authorization."""
    if header_token:
        return header_token
    if bearer_creds and bearer_creds.credentials:
        return bearer_creds.credentials
    return None


def verify_mentor_token(
    token: Annotated[str | None, Depends(get_mentor_token_from_request)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> str:
    """Validate mentor token using constant-time comparison against configured secret."""
    expected_token = settings.MENTOR_TOKEN

    if not token or not expected_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing mentor authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Constant-time comparison to prevent timing side-channel attacks
    if not secrets.compare_digest(token.encode("utf-8"), expected_token.encode("utf-8")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid mentor authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return token

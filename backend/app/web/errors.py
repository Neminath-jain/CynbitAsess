"""Centralized safe exception handlers for FastAPI.

Never leaks stack traces, source file paths, or raw database errors to clients.
All errors produce a consistent JSON payload with an error_id and safe message.
"""
import logging
import uuid
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.domain.exceptions import (
    AppError,
    EntityNotFoundError,
    InvalidStateTransitionError,
    SecurityViolationError,
)

logger = logging.getLogger(__name__)


def _get_request_id(request: Request) -> str:
    """Retrieve correlation ID from request state or generate a fallback UUID."""
    return getattr(request.state, "request_id", str(uuid.uuid4()))


def register_exception_handlers(app: FastAPI) -> None:
    """Attach global exception handlers to the FastAPI application."""

    @app.exception_handler(EntityNotFoundError)
    async def entity_not_found_handler(request: Request, exc: EntityNotFoundError) -> JSONResponse:
        error_id = exc.error_id or _get_request_id(request)
        logger.warning("EntityNotFoundError [%s]: %s (path: %s)", error_id, exc.message, request.url.path)
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error_id": error_id, "message": exc.message, "detail": None},
        )

    @app.exception_handler(InvalidStateTransitionError)
    async def state_transition_handler(request: Request, exc: InvalidStateTransitionError) -> JSONResponse:
        error_id = exc.error_id or _get_request_id(request)
        logger.warning("InvalidStateTransitionError [%s]: %s (path: %s)", error_id, exc.message, request.url.path)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error_id": error_id, "message": exc.message, "detail": None},
        )

    @app.exception_handler(SecurityViolationError)
    async def security_violation_handler(request: Request, exc: SecurityViolationError) -> JSONResponse:
        error_id = exc.error_id or _get_request_id(request)
        logger.warning("SecurityViolationError [%s]: %s (path: %s)", error_id, exc.message, request.url.path)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error_id": error_id, "message": exc.message, "detail": None},
        )

    @app.exception_handler(AppError)
    async def generic_app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        error_id = exc.error_id or _get_request_id(request)
        logger.error("AppError [%s]: %s (path: %s)", error_id, exc.message, request.url.path)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error_id": error_id, "message": exc.message, "detail": None},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        error_id = _get_request_id(request)
        logger.info("RequestValidationError [%s]: path %s, errors: %s", error_id, request.url.path, exc.errors())
        # Clean errors of non-serializable objects
        safe_errors: list[dict[str, Any]] = []
        for err in exc.errors():
            safe_errors.append({
                "loc": [str(loc) for loc in err.get("loc", [])],
                "msg": err.get("msg", ""),
                "type": err.get("type", ""),
            })
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error_id": error_id,
                "message": "Request validation failed. Please check submitted payload fields.",
                "detail": safe_errors,
            },
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        error_id = _get_request_id(request)
        message = exc.detail if isinstance(exc.detail, str) else "HTTP error"
        detail = exc.detail if not isinstance(exc.detail, str) else None
        headers = dict(exc.headers) if exc.headers else None
        return JSONResponse(
            status_code=exc.status_code,
            content={"error_id": error_id, "message": message, "detail": detail},
            headers=headers,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        error_id = _get_request_id(request)
        # Log full traceback internally for operations/debugging, but NEVER leak to client
        logger.exception("Unhandled server exception [%s] on %s: %s", error_id, request.url.path, str(exc))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error_id": error_id,
                "message": "An internal server error occurred. Please contact support with this error ID.",
                "detail": None,
            },
        )

"""Custom HTTP middlewares for request correlation and telemetry."""
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Assigns or propagates an X-Request-ID header on every HTTP request and response."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        incoming_id = request.headers.get("X-Request-ID")
        request_id = incoming_id.strip() if incoming_id and incoming_id.strip() else str(uuid.uuid4())

        # Store in request state for downstream handlers and error formatting
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

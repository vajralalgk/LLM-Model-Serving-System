"""
Request size limiting middleware.
Prevents oversized payloads from reaching the application layer.
"""

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.observability.logging import get_logger

logger = get_logger(__name__)


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Middleware that rejects requests exceeding the configured size limit."""

    def __init__(self, app, max_size: int = 1_048_576):
        super().__init__(app)
        self.max_size = max_size

    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")

        if content_length and int(content_length) > self.max_size:
            logger.warning(
                "request_too_large",
                content_length=content_length,
                max_size=self.max_size,
            )
            return JSONResponse(
                status_code=413,
                content={
                    "error": "Request entity too large",
                    "detail": f"Maximum request size is {self.max_size} bytes",
                },
            )

        return await call_next(request)

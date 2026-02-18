"""
JWT and API Key authentication middleware.
Protects API endpoints while allowing health checks through.
"""

import time
from typing import Optional

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from jose import jwt, JWTError

from app.observability.logging import get_logger

logger = get_logger(__name__)

# Paths that don't require authentication
PUBLIC_PATHS = {"/health", "/ready", "/metrics", "/version", "/docs", "/redoc", "/openapi.json"}


class JWTAuthMiddleware(BaseHTTPMiddleware):
    """Middleware that validates JWT tokens or API keys on protected endpoints."""

    def __init__(self, app, settings):
        super().__init__(app)
        self.secret_key = settings.jwt_secret_key
        self.algorithm = settings.jwt_algorithm
        self.api_key = settings.api_key

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Skip auth for public endpoints
        if path in PUBLIC_PATHS:
            return await call_next(request)

        # Check for API key first (simpler service-to-service auth)
        api_key = request.headers.get("X-API-Key")
        if api_key and api_key == self.api_key:
            request.state.auth_method = "api_key"
            return await call_next(request)

        # Check for JWT Bearer token
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return JSONResponse(
                status_code=401,
                content={"error": "Missing authentication credentials"},
            )

        try:
            scheme, token = auth_header.split(" ", 1)
            if scheme.lower() != "bearer":
                return JSONResponse(
                    status_code=401,
                    content={"error": "Invalid authentication scheme. Use 'Bearer <token>'"},
                )

            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # Check token expiration
            exp = payload.get("exp")
            if exp and time.time() > exp:
                return JSONResponse(
                    status_code=401,
                    content={"error": "Token has expired"},
                )

            request.state.user = payload.get("sub", "unknown")
            request.state.auth_method = "jwt"

        except (ValueError, JWTError) as e:
            logger.warning("auth_failed", error=str(e), path=path)
            return JSONResponse(
                status_code=401,
                content={"error": "Invalid or expired token"},
            )

        return await call_next(request)


def create_access_token(data: dict, settings, expires_delta_minutes: Optional[int] = None) -> str:
    """Utility function to create JWT tokens for testing and service auth."""
    to_encode = data.copy()
    expire = time.time() + (expires_delta_minutes or settings.jwt_expiration_minutes) * 60
    to_encode.update({"exp": expire, "iat": time.time()})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

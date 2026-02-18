"""
Rate limiting middleware using SlowAPI.
Protects the service from abuse and ensures fair resource allocation.
"""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import FastAPI, Request

from app.observability.logging import get_logger

logger = get_logger(__name__)

limiter = Limiter(key_func=get_remote_address)


def setup_rate_limiter(app: FastAPI, settings):
    """Configure rate limiting on the FastAPI application."""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    logger.info("rate_limiter_configured", limit=settings.rate_limit)

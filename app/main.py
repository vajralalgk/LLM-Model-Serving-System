"""
Main FastAPI application entry point.
Initializes the LLM Ranking Service with all middleware, routes, and lifecycle hooks.
Author: Gopi Krishna Vajrala
"""

import signal
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from app.config import get_settings
from app.api.routes import rank, health, metrics
from app.api.middleware.auth import JWTAuthMiddleware
from app.api.middleware.rate_limiter import setup_rate_limiter
from app.api.middleware.request_validator import RequestSizeLimitMiddleware
from app.core.model_server import ModelServer
from app.core.dynamic_batcher import DynamicBatcher
from app.core.model_registry import ModelRegistry
from app.observability.metrics import PrometheusMetrics
from app.observability.logging import setup_logging, get_logger
from app.observability.tracing import setup_tracing

settings = get_settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle: startup and shutdown."""
    logger.info("starting_application", version=settings.app_version)

    # Initialize model registry and load models
    app.state.model_registry = ModelRegistry(settings)
    await app.state.model_registry.load_models()

    # Initialize model server
    app.state.model_server = ModelServer(
        registry=app.state.model_registry,
        settings=settings,
    )

    # Initialize dynamic batcher
    app.state.dynamic_batcher = DynamicBatcher(
        model_server=app.state.model_server,
        max_batch_size=settings.max_batch_size,
        timeout_ms=settings.batch_timeout_ms,
    )
    await app.state.dynamic_batcher.start()

    # Initialize metrics
    app.state.metrics = PrometheusMetrics()

    logger.info("application_ready", model_version=settings.model_version)
    yield

    # Graceful shutdown
    logger.info("shutting_down_application")
    await app.state.dynamic_batcher.stop()
    await app.state.model_server.shutdown()
    logger.info("application_shutdown_complete")


def create_app() -> FastAPI:
    """Factory function to create and configure the FastAPI application."""
    setup_logging(settings.log_level)

    app = FastAPI(
        title="LLM Ranking Service",
        description="Real-time personalization ranking system powered by LLM",
        version=settings.app_version,
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
        docs_url="/docs" if settings.app_env != "production" else None,
        redoc_url="/redoc" if settings.app_env != "production" else None,
    )

    # Middleware (order matters - outermost first)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestSizeLimitMiddleware, max_size=settings.max_request_size_bytes)
    app.add_middleware(JWTAuthMiddleware, settings=settings)

    # Rate limiting
    setup_rate_limiter(app, settings)

    # Tracing
    if settings.enable_tracing:
        setup_tracing(app, settings)

    # Routes
    app.include_router(rank.router, tags=["Ranking"])
    app.include_router(health.router, tags=["Health"])
    app.include_router(metrics.router, tags=["Metrics"])

    # Graceful shutdown on SIGTERM
    def handle_sigterm(*args):
        logger.info("received_sigterm")
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, handle_sigterm)

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        workers=settings.app_workers,
        log_level=settings.log_level.lower(),
        access_log=True,
    )

"""
Distributed tracing using OpenTelemetry.
Provides end-to-end request tracing across the service.
"""

from app.observability.logging import get_logger

logger = get_logger(__name__)


def setup_tracing(app, settings):
    """Configure OpenTelemetry tracing for the FastAPI application."""
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanExporter
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        resource = Resource.create(
            {
                "service.name": settings.app_name,
                "service.version": settings.app_version,
                "deployment.environment": settings.app_env,
            }
        )

        provider = TracerProvider(resource=resource)

        otlp_exporter = OTLPSpanExporter(endpoint=settings.otlp_endpoint)
        provider.add_span_processor(BatchSpanExporter(otlp_exporter))

        trace.set_tracer_provider(provider)

        FastAPIInstrumentor.instrument_app(app)

        logger.info(
            "tracing_configured",
            endpoint=settings.otlp_endpoint,
            service=settings.app_name,
        )

    except ImportError as e:
        logger.warning("tracing_not_available", error=str(e))
    except Exception as e:
        logger.error("tracing_setup_failed", error=str(e))

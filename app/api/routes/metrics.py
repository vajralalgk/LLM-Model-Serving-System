"""
Prometheus metrics endpoint.
Exposes application and system metrics for monitoring.
"""

from fastapi import APIRouter, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

router = APIRouter()


@router.get("/metrics", summary="Prometheus metrics endpoint")
async def prometheus_metrics():
    """Expose Prometheus-compatible metrics."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )

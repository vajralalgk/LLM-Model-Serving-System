"""
Health check endpoints for Kubernetes liveness and readiness probes.
"""

from fastapi import APIRouter, Request, Response

router = APIRouter()


@router.get("/health", summary="Liveness probe")
async def health_check():
    """Liveness probe - returns 200 if the service is running."""
    return {"status": "healthy"}


@router.get("/ready", summary="Readiness probe")
async def readiness_check(request: Request):
    """Readiness probe - returns 200 only if model is loaded and ready to serve."""
    try:
        model_server = request.app.state.model_server
        batcher = request.app.state.dynamic_batcher

        if not model_server.is_ready():
            return Response(
                content='{"status": "not_ready", "reason": "model not loaded"}',
                status_code=503,
                media_type="application/json",
            )

        if not batcher.is_running():
            return Response(
                content='{"status": "not_ready", "reason": "batcher not running"}',
                status_code=503,
                media_type="application/json",
            )

        return {
            "status": "ready",
            "model_version": model_server.current_version,
            "batcher_queue_size": batcher.queue_size,
        }

    except Exception as e:
        return Response(
            content=f'{{"status": "not_ready", "reason": "{str(e)}"}}',
            status_code=503,
            media_type="application/json",
        )


@router.get("/version", summary="Service version info")
async def version_info(request: Request):
    """Returns current service and model version information."""
    try:
        registry = request.app.state.model_registry
        return {
            "service_version": request.app.version,
            "model_version": request.app.state.model_server.current_version,
            "available_versions": registry.list_versions(),
        }
    except Exception:
        return {
            "service_version": request.app.version,
            "model_version": "unknown",
            "available_versions": [],
        }

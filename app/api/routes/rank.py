"""
Ranking API endpoint - POST /rank
Serves real-time personalized content rankings using LLM embeddings.
"""

import time
import uuid
from datetime import datetime

from fastapi import APIRouter, Request, HTTPException

from app.api.schemas.rank import RankRequest, RankResponse, RankedItem, ErrorResponse
from app.config import get_settings
from app.observability.logging import get_logger
from app.resilience.circuit_breaker import ranking_circuit_breaker
from app.resilience.timeout import with_timeout

router = APIRouter()
settings = get_settings()
logger = get_logger(__name__)


@router.post(
    "/rank",
    response_model=RankResponse,
    responses={
        400: {"model": ErrorResponse},
        429: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
    summary="Rank candidate titles for a user",
    description="Accepts a user ID, context, and candidate titles. Returns titles ranked by personalized relevance.",
)
async def rank_titles(request: Request, payload: RankRequest):
    request_id = str(uuid.uuid4())
    start_time = time.perf_counter()

    logger.info(
        "rank_request_received",
        request_id=request_id,
        user_id=payload.user_id,
        num_candidates=len(payload.candidate_titles),
        model_version=payload.model_version,
    )

    try:
        # Determine model version
        model_version = payload.model_version or settings.model_version

        # Submit to dynamic batcher with circuit breaker protection
        batcher = request.app.state.dynamic_batcher
        metrics = request.app.state.metrics

        @ranking_circuit_breaker
        async def execute_ranking():
            return await with_timeout(
                batcher.submit(
                    user_id=payload.user_id,
                    context=payload.context,
                    candidate_titles=payload.candidate_titles,
                    model_version=model_version,
                ),
                timeout_seconds=settings.request_timeout_seconds,
            )

        scores = await execute_ranking()

        # Build ranked results
        title_scores = list(zip(payload.candidate_titles, scores))
        title_scores.sort(key=lambda x: x[1], reverse=True)

        ranked_titles = [t for t, _ in title_scores]
        ranked_items = [
            RankedItem(title=title, rank=i + 1, score=round(score, 6))
            for i, (title, score) in enumerate(title_scores)
        ]

        latency_ms = (time.perf_counter() - start_time) * 1000

        # Record metrics
        metrics.record_request_latency(latency_ms)
        metrics.increment_request_count(status="success")

        logger.info(
            "rank_request_completed",
            request_id=request_id,
            user_id=payload.user_id,
            latency_ms=round(latency_ms, 2),
            model_version=model_version,
        )

        return RankResponse(
            ranked_titles=ranked_titles,
            ranked_items=ranked_items,
            model_version=model_version,
            request_id=request_id,
            latency_ms=round(latency_ms, 2),
            timestamp=datetime.utcnow(),
        )

    except TimeoutError:
        latency_ms = (time.perf_counter() - start_time) * 1000
        metrics = request.app.state.metrics
        metrics.increment_request_count(status="timeout")
        logger.error("rank_request_timeout", request_id=request_id, latency_ms=latency_ms)
        raise HTTPException(status_code=504, detail="Request timed out")

    except Exception as e:
        latency_ms = (time.perf_counter() - start_time) * 1000
        try:
            metrics = request.app.state.metrics
            metrics.increment_request_count(status="error")
        except Exception:
            pass
        logger.error(
            "rank_request_failed",
            request_id=request_id,
            error=str(e),
            latency_ms=latency_ms,
        )
        raise HTTPException(status_code=500, detail=f"Ranking failed: {str(e)}")

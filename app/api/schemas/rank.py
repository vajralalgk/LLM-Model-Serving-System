"""
Pydantic schemas for the ranking API endpoint.
Handles request validation and response serialization.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime


class RankRequest(BaseModel):
    """Input schema for POST /rank endpoint."""

    user_id: str = Field(
        ...,
        min_length=1,
        max_length=256,
        description="Unique user identifier",
        examples=["user_12345"],
    )
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="User context for personalization (location, time, preferences, etc.)",
        examples=[{"location": "US", "device": "mobile", "time_of_day": "morning"}],
    )
    candidate_titles: List[str] = Field(
        ...,
        min_length=1,
        max_length=500,
        description="List of candidate content titles to rank",
        examples=[["Breaking News: AI Advances", "Sports Update", "Weather Forecast"]],
    )
    model_version: Optional[str] = Field(
        default=None,
        description="Specific model version to use (e.g., 'v1', 'v2'). Uses latest if not specified.",
    )

    @field_validator("candidate_titles")
    @classmethod
    def validate_titles(cls, v):
        if any(len(title.strip()) == 0 for title in v):
            raise ValueError("Empty titles are not allowed")
        if any(len(title) > 1000 for title in v):
            raise ValueError("Individual title must not exceed 1000 characters")
        return v


class RankedItem(BaseModel):
    """A single ranked item with its score."""

    title: str
    rank: int
    score: float = Field(..., description="Relevance score between 0.0 and 1.0")


class RankResponse(BaseModel):
    """Output schema for POST /rank endpoint."""

    ranked_titles: List[str] = Field(
        ..., description="Titles sorted by relevance (most relevant first)"
    )
    ranked_items: List[RankedItem] = Field(
        ..., description="Detailed ranking with scores"
    )
    model_version: str = Field(..., description="Model version used for ranking")
    request_id: str = Field(..., description="Unique request identifier for tracing")
    latency_ms: float = Field(..., description="Server-side processing time in milliseconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    """Standard error response format."""

    error: str
    detail: Optional[str] = None
    request_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

"""
Response Models for PAI API

Provides Pydantic models for standardized API responses with:
- Consistent error format
- Typed response schemas
- OpenAPI documentation support
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


def _utc_now() -> datetime:
    """Get current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


class ErrorCode(str, Enum):
    """Standardized error codes."""

    VALIDATION_ERROR = "validation_error"
    EMBEDDING_FAILED = "embedding_failed"
    VECTOR_DB_ERROR = "vector_db_error"
    AI_GENERATION_ERROR = "ai_generation_error"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    INTERNAL_ERROR = "internal_error"
    NOT_FOUND = "not_found"


class ErrorDetail(BaseModel):
    """Detailed error information."""

    code: ErrorCode
    message: str
    field: str | None = None
    details: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    """Standardized error response."""

    success: bool = False
    error: ErrorDetail
    timestamp: datetime = Field(default_factory=_utc_now)
    request_id: str | None = None


# Specific Response Models
class VectorizeResponse(BaseModel):
    """Response for vectorize endpoint."""

    original_text: str
    vector_dimension: int
    vector_preview: list[float] = Field(max_length=5)


class ContextResponse(BaseModel):
    """Response for context storage endpoint."""

    status: str = "success"
    id: str
    message: str


class MatchResult(BaseModel):
    """Single search result."""

    id: str
    score: float
    text: str
    metadata: dict[str, Any] = {}


class SearchResponse(BaseModel):
    """Response for search endpoint."""

    matches: list[MatchResult]
    query: str
    total_results: int


class InsightResponse(BaseModel):
    """Response for insight generation endpoint."""

    insight: str
    context_used: list[str]
    model_used: str = "gemini-3-flash-preview"


class HealthResponse(BaseModel):
    """Response for health check endpoint."""

    status: str
    service: str
    config: dict[str, bool]
    version: str = "0.2.0"

"""PAI Models Package - Request and Response models for API validation."""

from app.models.requests import ContextInput, SearchInput, TextInput
from app.models.responses import (
    ContextResponse,
    ErrorCode,
    ErrorDetail,
    ErrorResponse,
    HealthResponse,
    InsightResponse,
    MatchResult,
    SearchResponse,
    VectorizeResponse,
)

__all__ = [
    # Requests
    "TextInput",
    "SearchInput",
    "ContextInput",
    # Responses
    "VectorizeResponse",
    "ContextResponse",
    "SearchResponse",
    "InsightResponse",
    "HealthResponse",
    "MatchResult",
    "ErrorResponse",
    "ErrorDetail",
    "ErrorCode",
]

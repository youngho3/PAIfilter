"""
Request Models for PAI API

Provides Pydantic models for input validation with:
- Text sanitization
- Length constraints
- Field-level validation
"""

from typing import Any

from pydantic import BaseModel, Field, field_validator


class TextInput(BaseModel):
    """Input model for text-based API endpoints."""

    text: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Text input for processing"
    )

    @field_validator("text")
    @classmethod
    def sanitize_text(cls, v: str) -> str:
        """Sanitize input text to prevent injection attacks."""
        # Remove null bytes
        v = v.replace("\x00", "")
        # Strip excessive whitespace
        v = " ".join(v.split())
        v = v.strip()
        # Check if text is empty after sanitization
        if not v:
            raise ValueError("Text cannot be empty or whitespace only")
        return v


class SearchInput(TextInput):
    """Extended input for search operations."""

    top_k: int = Field(
        default=3,
        ge=1,
        le=20,
        description="Number of results to return"
    )
    min_score: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score threshold"
    )


class ContextInput(TextInput):
    """Input for storing context with optional metadata."""

    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Optional metadata to store with the vector"
    )

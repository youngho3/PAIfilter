"""
News Models for PAI Signal System

Provides models for news articles and signals.
"""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field, HttpUrl


def _utc_now() -> datetime:
    """Get current UTC time."""
    return datetime.now(timezone.utc)


class NewsArticle(BaseModel):
    """Represents a news article from RSS/web sources."""

    id: str = Field(..., description="Unique identifier for the article")
    title: str = Field(..., description="Article title")
    url: str = Field(..., description="Article URL")
    source: str = Field(..., description="Source name (e.g., 'TechCrunch', 'Medium')")
    summary: str = Field(default="", description="Article summary or excerpt")
    content: str = Field(default="", description="Full article content")
    author: str | None = Field(default=None, description="Article author")
    published_at: datetime | None = Field(default=None, description="Publication date")
    fetched_at: datetime = Field(default_factory=_utc_now, description="When the article was fetched")
    tags: list[str] = Field(default_factory=list, description="Article tags/categories")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class Signal(BaseModel):
    """Represents a scored signal for the user."""

    article: NewsArticle
    score: float = Field(..., ge=0, le=10, description="Relevance score (0-10)")
    similarity: float = Field(..., ge=0, le=1, description="Raw cosine similarity")
    reason: str | None = Field(default=None, description="AI-generated reason for relevance")


class SignalResponse(BaseModel):
    """Response containing multiple signals."""

    signals: list[Signal]
    total: int
    user_context: str | None = Field(default=None, description="User context used for matching")


class FeedSource(BaseModel):
    """RSS/Atom feed source configuration."""

    name: str = Field(..., description="Source name")
    url: str = Field(..., description="Feed URL")
    category: str = Field(default="tech", description="Category of the feed")
    enabled: bool = Field(default=True, description="Whether the feed is enabled")

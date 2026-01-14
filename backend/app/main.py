"""
PAI Intelligence Engine - Main FastAPI Application

This module defines the FastAPI application and API endpoints for the
Personal AI Filter (PAI) system, which provides:
- Text vectorization using Gemini embeddings
- Context storage and retrieval via Pinecone
- AI-powered insights with RAG (Retrieval Augmented Generation)
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import Depends, FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import Settings, get_settings, settings
from app.core.exceptions import PAIException, pai_exception_handler, validation_exception_handler
from app.core.logging import get_logger, setup_logging
from app.middleware.rate_limiter import rate_limiter
from app.models.requests import SearchInput, TextInput
from app.models.responses import (
    ContextResponse,
    HealthResponse,
    InsightResponse,
    MatchResult,
    SearchResponse,
    VectorizeResponse,
)
from app.models.news import FeedSource, Signal, SignalResponse
from app.services.crawler_service import fetch_all_feeds, get_available_feeds
from app.services.gemini_service import get_gemini_response, get_text_embedding
from app.services.pinecone_service import search_similar_context, upsert_context
from app.services.signal_service import generate_signals, get_news_count, process_articles

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup/shutdown events."""
    # Startup
    setup_logging(settings.LOG_LEVEL)
    logger.info("PAI Intelligence Engine starting up...")
    logger.info(f"Environment: {settings.APP_ENV}")
    yield
    # Shutdown
    logger.info("PAI Intelligence Engine shutting down...")


app = FastAPI(
    title="PAI Intelligence Engine",
    description="Personal AI Filter - Context-aware AI assistant with memory",
    version="0.2.0",
    lifespan=lifespan,
)

# Register exception handlers
app.add_exception_handler(PAIException, pai_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=HealthResponse, tags=["Health"])
def read_root(config: Settings = Depends(get_settings)) -> HealthResponse:
    """
    Health check endpoint.

    Returns the service status and configuration state.
    """
    return HealthResponse(
        status="online",
        service="PAI Intelligence Engine",
        config={
            "gemini_configured": bool(config.GOOGLE_API_KEY),
            "pinecone_configured": bool(config.PINECONE_API_KEY),
        },
    )


@app.post(
    "/api/v1/vectorize",
    response_model=VectorizeResponse,
    tags=["Embedding"],
    dependencies=[Depends(rate_limiter)],
)
async def vectorize_text(input_data: TextInput) -> VectorizeResponse:
    """
    Convert text to a vector embedding.

    Uses Gemini text-embedding-004 model to generate a 768-dimensional
    vector representation of the input text.
    """
    vector = await get_text_embedding(input_data.text)

    if not vector:
        logger.error(f"Failed to generate embedding for text: {input_data.text[:50]}...")
        raise HTTPException(
            status_code=500,
            detail={
                "code": "embedding_failed",
                "message": "Failed to generate embedding. Please try again.",
            },
        )

    return VectorizeResponse(
        original_text=input_data.text,
        vector_dimension=len(vector),
        vector_preview=vector[:5],
    )


@app.post(
    "/api/v1/context",
    response_model=ContextResponse,
    tags=["Memory"],
    dependencies=[Depends(rate_limiter)],
)
async def store_context(input_data: TextInput) -> ContextResponse:
    """
    Store context in the vector database (Pinecone).

    Vectorizes the input text and stores it for future retrieval
    during RAG-enhanced insight generation.
    """
    vector_id = await upsert_context(input_data.text)

    if not vector_id:
        logger.error(f"Failed to store context: {input_data.text[:50]}...")
        raise HTTPException(
            status_code=500,
            detail={
                "code": "vector_db_error",
                "message": "Failed to store context in Vector DB",
            },
        )

    logger.info(f"Context stored with ID: {vector_id}")
    return ContextResponse(id=vector_id, message="Context remembered.")


@app.post(
    "/api/v1/search",
    response_model=SearchResponse,
    tags=["Memory"],
    dependencies=[Depends(rate_limiter)],
)
async def search_context(input_data: SearchInput) -> SearchResponse:
    """
    Search for similar past contexts.

    Queries Pinecone for vectors similar to the input text.
    """
    matches = await search_similar_context(input_data.text, top_k=input_data.top_k)

    return SearchResponse(
        matches=[
            MatchResult(
                id=m.get("id", ""),
                score=m.get("score", 0.0),
                text=m.get("metadata", {}).get("text", ""),
                metadata=m.get("metadata", {}),
            )
            for m in matches
        ],
        query=input_data.text,
        total_results=len(matches),
    )


@app.post(
    "/api/v1/insight",
    response_model=InsightResponse,
    tags=["AI"],
    dependencies=[Depends(rate_limiter)],
)
async def generate_insight(input_data: TextInput) -> InsightResponse:
    """
    Generate AI insight using RAG (Retrieval Augmented Generation).

    Searches for relevant past contexts and uses them to enhance
    the AI's response with personalized, contextual information.
    """
    # 1. Search for relevant memories (similarity > 0.7)
    matches = await search_similar_context(input_data.text, top_k=3)

    relevant_contexts: list[str] = []
    for m in matches:
        score = m.get("score", 0.0)
        if score > 0.7:
            text = m.get("metadata", {}).get("text", "")
            relevant_contexts.append(f"- {text} (similarity: {score:.2f})")

    memory_text = (
        "\n".join(relevant_contexts)
        if relevant_contexts
        else "No relevant past memories found."
    )

    # 2. Construct RAG prompt
    prompt = f"""
    You are PAI, an AI partner who deeply understands the user's context.

    [User's Past Concerns/Interests (Memory)]
    {memory_text}

    [Current Input]
    {input_data.text}

    [Instructions]
    Please provide insightful feedback on the current input, referencing the 'past memories' above.
    If there are connections to previous concerns, mention those relationships.
    """

    # 3. Generate response
    response = get_gemini_response(prompt)

    logger.info(f"Generated insight with {len(relevant_contexts)} context references")

    return InsightResponse(
        insight=response,
        context_used=relevant_contexts,
        model_used="gemini-3-flash-preview",
    )


# =============================================================================
# Sprint 2: Signal System Endpoints
# =============================================================================


@app.get("/api/v1/feeds", tags=["Signals"])
async def list_feeds() -> list[FeedSource]:
    """
    Get list of available RSS feed sources.

    Returns configured feed sources that can be used for news collection.
    """
    return get_available_feeds()


@app.post("/api/v1/feeds/fetch", tags=["Signals"], dependencies=[Depends(rate_limiter)])
async def fetch_news(limit_per_feed: int = 10):
    """
    Fetch and process news articles from all RSS feeds.

    This endpoint:
    1. Fetches articles from all configured RSS feeds
    2. Generates embeddings for each article
    3. Stores embeddings in Pinecone for similarity search

    Args:
        limit_per_feed: Maximum articles to fetch per feed (default: 10)

    Returns:
        Summary of fetched and processed articles.
    """
    # Fetch articles from RSS feeds
    articles = await fetch_all_feeds(limit_per_feed=limit_per_feed)

    if not articles:
        return {
            "status": "warning",
            "message": "No articles fetched from feeds",
            "fetched": 0,
            "processed": 0,
        }

    # Process articles (embed and store)
    processed_count = await process_articles(articles)

    return {
        "status": "success",
        "message": f"Fetched {len(articles)} articles, processed {processed_count}",
        "fetched": len(articles),
        "processed": processed_count,
        "sources": list(set(a.source for a in articles)),
    }


@app.post(
    "/api/v1/signals",
    response_model=SignalResponse,
    tags=["Signals"],
    dependencies=[Depends(rate_limiter)],
)
async def get_signals(input_data: TextInput, top_k: int = 10, min_score: float = 3.0):
    """
    Generate personalized signals based on user context.

    Searches for news articles that match the user's context/interests
    and returns them ranked by relevance score (0-10).

    Args:
        input_data: User's current context or interests.
        top_k: Maximum number of signals to return (default: 10).
        min_score: Minimum relevance score threshold (default: 3.0).

    Returns:
        SignalResponse with ranked signals.
    """
    signals = await generate_signals(
        user_context=input_data.text,
        top_k=top_k,
        min_score=min_score,
    )

    return SignalResponse(
        signals=signals,
        total=len(signals),
        user_context=input_data.text[:100] + "..." if len(input_data.text) > 100 else input_data.text,
    )


@app.get("/api/v1/signals/stats", tags=["Signals"])
async def get_signal_stats():
    """
    Get statistics about the signal system.

    Returns information about stored news articles and system status.
    """
    news_count = await get_news_count()

    return {
        "news_articles_count": news_count,
        "feeds_configured": len(get_available_feeds()),
        "status": "ready" if news_count > 0 else "empty",
    }

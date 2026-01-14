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
from app.services.gemini_service import get_gemini_response, get_text_embedding
from app.services.pinecone_service import search_similar_context, upsert_context

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

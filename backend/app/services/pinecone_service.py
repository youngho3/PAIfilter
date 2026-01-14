"""
Pinecone Vector Database Service Module

Provides vector storage and retrieval capabilities using Pinecone.
"""

import logging
import uuid
from typing import Any

from pinecone import Pinecone

from app.core.config import settings
from app.services.gemini_service import get_text_embedding

logger = logging.getLogger(__name__)

# Pinecone initialization
pc = Pinecone(api_key=settings.PINECONE_API_KEY.get_secret_value())
index = pc.Index(name=settings.PINECONE_INDEX_NAME, host=settings.PINECONE_HOST)


async def upsert_context(
    text: str,
    metadata: dict[str, Any] | None = None
) -> str | None:
    """
    Vectorize text and store in Pinecone.

    Args:
        text: The text content to store.
        metadata: Optional additional metadata to store with the vector.

    Returns:
        The vector ID if successful, None otherwise.

    Example:
        >>> vector_id = await upsert_context("My business concern")
        >>> vector_id is not None
        True
    """
    vector = await get_text_embedding(text)
    if not vector:
        logger.warning("Failed to generate embedding for upsert")
        return None

    # Generate ID and construct payload
    vector_id = str(uuid.uuid4())
    payload = {
        "id": vector_id,
        "values": vector,
        "metadata": {
            "text": text,
            **(metadata or {})
        }
    }

    try:
        index.upsert(vectors=[payload])
        logger.info(f"Successfully stored context with ID: {vector_id}")
        return vector_id
    except Exception as e:
        logger.error(f"Pinecone Upsert Error: {e}", exc_info=True)
        return None


async def search_similar_context(
    text: str,
    top_k: int = 3
) -> list[dict[str, Any]]:
    """
    Search for similar contexts in Pinecone.

    Args:
        text: The query text to search for.
        top_k: Maximum number of results to return.

    Returns:
        List of matching results with scores and metadata.
        Returns empty list if search fails.

    Example:
        >>> matches = await search_similar_context("growth strategies")
        >>> len(matches) <= 3
        True
    """
    vector = await get_text_embedding(text)
    if not vector:
        logger.warning("Failed to generate embedding for search")
        return []

    try:
        results = index.query(
            vector=vector,
            top_k=top_k,
            include_metadata=True
        )
        matches = results["matches"]
        logger.debug(f"Found {len(matches)} similar contexts")
        return matches
    except Exception as e:
        logger.error(f"Pinecone Query Error: {e}", exc_info=True)
        return []

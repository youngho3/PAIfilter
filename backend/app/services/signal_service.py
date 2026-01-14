"""
Signal Service for PAI Intelligence System

Provides:
- Auto-embedding of news articles
- Similarity scoring between user context and news
- Signal generation and ranking
"""

import logging
from datetime import datetime, timezone

from app.models.news import NewsArticle, Signal
from app.services.gemini_service import get_text_embedding
from app.services.pinecone_service import index

logger = logging.getLogger(__name__)

# Pinecone namespace for news articles
NEWS_NAMESPACE = "news"


async def embed_article(article: NewsArticle) -> list[float] | None:
    """
    Generate embedding for a news article.

    Uses title + summary for embedding to capture key information.

    Args:
        article: The news article to embed.

    Returns:
        768-dimensional embedding vector or None if failed.
    """
    # Combine title and summary for better semantic representation
    text = f"{article.title}\n\n{article.summary}"

    # Limit text length to avoid token limits
    if len(text) > 8000:
        text = text[:8000]

    embedding = await get_text_embedding(text)

    if not embedding:
        logger.warning(f"Failed to generate embedding for article: {article.id}")
        return None

    return embedding


async def store_article_embedding(
    article: NewsArticle,
    embedding: list[float]
) -> bool:
    """
    Store article embedding in Pinecone.

    Args:
        article: The news article.
        embedding: The embedding vector.

    Returns:
        True if successful, False otherwise.
    """
    try:
        metadata = {
            "title": article.title[:500],  # Limit metadata size
            "url": article.url,
            "source": article.source,
            "summary": article.summary[:1000] if article.summary else "",
            "published_at": article.published_at.isoformat() if article.published_at else None,
            "type": "news",
        }

        index.upsert(
            vectors=[{
                "id": article.id,
                "values": embedding,
                "metadata": metadata
            }],
            namespace=NEWS_NAMESPACE
        )

        logger.debug(f"Stored embedding for article: {article.id}")
        return True

    except Exception as e:
        logger.error(f"Error storing article embedding: {e}")
        return False


async def process_articles(articles: list[NewsArticle]) -> int:
    """
    Process multiple articles: embed and store them.

    Args:
        articles: List of articles to process.

    Returns:
        Number of successfully processed articles.
    """
    success_count = 0

    for article in articles:
        try:
            # Generate embedding
            embedding = await embed_article(article)
            if not embedding:
                continue

            # Store in Pinecone
            if await store_article_embedding(article, embedding):
                success_count += 1

        except Exception as e:
            logger.error(f"Error processing article {article.id}: {e}")
            continue

    logger.info(f"Processed {success_count}/{len(articles)} articles")
    return success_count


def similarity_to_score(similarity: float) -> float:
    """
    Convert cosine similarity (0-1) to user-friendly score (0-10).

    Uses non-linear scaling to emphasize high-relevance items.

    Args:
        similarity: Cosine similarity value (0 to 1).

    Returns:
        Score from 0 to 10.
    """
    # Non-linear scaling: emphasize higher similarities
    # similarity 0.7+ maps to score 7+
    # similarity 0.5-0.7 maps to score 4-7
    # similarity <0.5 maps to score 0-4

    if similarity >= 0.8:
        return 8 + (similarity - 0.8) * 10  # 8-10
    elif similarity >= 0.6:
        return 5 + (similarity - 0.6) * 15  # 5-8
    elif similarity >= 0.4:
        return 2 + (similarity - 0.4) * 15  # 2-5
    else:
        return similarity * 5  # 0-2


async def get_user_context_embedding(user_id: str = "default") -> list[float] | None:
    """
    Get the user's context embedding from stored contexts.

    For now, returns the centroid of recent user contexts.
    In the future, this could be more sophisticated.

    Args:
        user_id: User identifier.

    Returns:
        Embedding vector representing user context.
    """
    try:
        # Query user's recent contexts from the default namespace
        # We'll use a random vector to get recent items (workaround)
        # In production, you'd store user context embeddings separately

        # For now, return None and handle at the API level
        return None

    except Exception as e:
        logger.error(f"Error getting user context: {e}")
        return None


async def generate_signals(
    user_context: str,
    top_k: int = 10,
    min_score: float = 3.0
) -> list[Signal]:
    """
    Generate ranked signals based on user context.

    Args:
        user_context: User's current context/interests.
        top_k: Maximum number of signals to return.
        min_score: Minimum score threshold (0-10).

    Returns:
        List of Signal objects sorted by score.
    """
    signals: list[Signal] = []

    try:
        # Generate embedding for user context
        user_embedding = await get_text_embedding(user_context)
        if not user_embedding:
            logger.error("Failed to generate user context embedding")
            return signals

        # Query similar news articles
        results = index.query(
            vector=user_embedding,
            top_k=top_k * 2,  # Get more to filter by score
            include_metadata=True,
            namespace=NEWS_NAMESPACE
        )

        for match in results.get("matches", []):
            similarity = match.get("score", 0)
            score = similarity_to_score(similarity)

            # Filter by minimum score
            if score < min_score:
                continue

            metadata = match.get("metadata", {})

            # Reconstruct article from metadata
            article = NewsArticle(
                id=match.get("id", ""),
                title=metadata.get("title", "Untitled"),
                url=metadata.get("url", ""),
                source=metadata.get("source", "Unknown"),
                summary=metadata.get("summary", ""),
                published_at=datetime.fromisoformat(metadata["published_at"]) if metadata.get("published_at") else None,
            )

            signal = Signal(
                article=article,
                score=round(score, 1),
                similarity=round(similarity, 3),
            )
            signals.append(signal)

        # Sort by score descending and limit
        signals.sort(key=lambda s: s.score, reverse=True)
        signals = signals[:top_k]

        logger.info(f"Generated {len(signals)} signals for user context")

    except Exception as e:
        logger.error(f"Error generating signals: {e}")

    return signals


async def get_news_count() -> int:
    """Get the total count of news articles in the database."""
    try:
        stats = index.describe_index_stats()
        namespaces = stats.get("namespaces", {})
        news_stats = namespaces.get(NEWS_NAMESPACE, {})
        return news_stats.get("vector_count", 0)
    except Exception as e:
        logger.error(f"Error getting news count: {e}")
        return 0

"""
Crawler Service for PAI Signal System

Provides RSS feed parsing and web content extraction.
"""

import hashlib
import logging
from datetime import datetime, timezone
from typing import Any

import feedparser
import httpx

from app.models.news import FeedSource, NewsArticle

logger = logging.getLogger(__name__)

# Default RSS feed sources
DEFAULT_FEEDS: list[FeedSource] = [
    FeedSource(
        name="TechCrunch",
        url="https://techcrunch.com/feed/",
        category="tech"
    ),
    FeedSource(
        name="Hacker News",
        url="https://hnrss.org/frontpage",
        category="tech"
    ),
    FeedSource(
        name="MIT Technology Review",
        url="https://www.technologyreview.com/feed/",
        category="tech"
    ),
    FeedSource(
        name="The Verge",
        url="https://www.theverge.com/rss/index.xml",
        category="tech"
    ),
    FeedSource(
        name="Wired",
        url="https://www.wired.com/feed/rss",
        category="tech"
    ),
]


def _generate_article_id(url: str) -> str:
    """Generate a unique ID for an article based on its URL."""
    return hashlib.md5(url.encode()).hexdigest()


def _parse_datetime(date_str: str | None, date_parsed: tuple | None) -> datetime | None:
    """Parse datetime from feedparser date formats."""
    if date_parsed:
        try:
            return datetime(*date_parsed[:6], tzinfo=timezone.utc)
        except (ValueError, TypeError):
            pass
    return None


async def fetch_rss_feed(feed: FeedSource) -> list[NewsArticle]:
    """
    Fetch and parse articles from an RSS feed.

    Args:
        feed: The feed source configuration.

    Returns:
        List of parsed NewsArticle objects.
    """
    articles: list[NewsArticle] = []

    try:
        # Fetch the feed content
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                feed.url,
                headers={"User-Agent": "PAI-Crawler/1.0"}
            )
            response.raise_for_status()
            content = response.text

        # Parse the feed
        parsed = feedparser.parse(content)

        if parsed.bozo and parsed.bozo_exception:
            logger.warning(f"Feed parsing warning for {feed.name}: {parsed.bozo_exception}")

        for entry in parsed.entries:
            try:
                # Extract article data
                url = entry.get("link", "")
                if not url:
                    continue

                article = NewsArticle(
                    id=_generate_article_id(url),
                    title=entry.get("title", "Untitled"),
                    url=url,
                    source=feed.name,
                    summary=_clean_html(entry.get("summary", "")),
                    content=_clean_html(entry.get("content", [{}])[0].get("value", "")) if entry.get("content") else "",
                    author=entry.get("author"),
                    published_at=_parse_datetime(
                        entry.get("published"),
                        entry.get("published_parsed")
                    ),
                    tags=[tag.get("term", "") for tag in entry.get("tags", []) if tag.get("term")],
                    metadata={
                        "category": feed.category,
                        "feed_url": feed.url,
                    }
                )
                articles.append(article)

            except Exception as e:
                logger.error(f"Error parsing entry from {feed.name}: {e}")
                continue

        logger.info(f"Fetched {len(articles)} articles from {feed.name}")

    except httpx.HTTPError as e:
        logger.error(f"HTTP error fetching {feed.name}: {e}")
    except Exception as e:
        logger.error(f"Error fetching feed {feed.name}: {e}")

    return articles


def _clean_html(text: str) -> str:
    """Remove HTML tags from text (simple implementation)."""
    import re
    # Remove HTML tags
    clean = re.sub(r'<[^>]+>', '', text)
    # Decode HTML entities
    clean = clean.replace('&nbsp;', ' ')
    clean = clean.replace('&amp;', '&')
    clean = clean.replace('&lt;', '<')
    clean = clean.replace('&gt;', '>')
    clean = clean.replace('&quot;', '"')
    clean = clean.replace('&#39;', "'")
    # Clean up whitespace
    clean = ' '.join(clean.split())
    return clean.strip()


async def fetch_all_feeds(
    feeds: list[FeedSource] | None = None,
    limit_per_feed: int = 10
) -> list[NewsArticle]:
    """
    Fetch articles from all configured RSS feeds.

    Args:
        feeds: Optional list of feed sources. Uses DEFAULT_FEEDS if not provided.
        limit_per_feed: Maximum articles to return per feed.

    Returns:
        Combined list of articles from all feeds.
    """
    if feeds is None:
        feeds = [f for f in DEFAULT_FEEDS if f.enabled]

    all_articles: list[NewsArticle] = []

    for feed in feeds:
        try:
            articles = await fetch_rss_feed(feed)
            # Limit articles per feed
            all_articles.extend(articles[:limit_per_feed])
        except Exception as e:
            logger.error(f"Error processing feed {feed.name}: {e}")
            continue

    # Sort by published date (newest first)
    all_articles.sort(
        key=lambda a: a.published_at or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True
    )

    logger.info(f"Total articles fetched: {len(all_articles)}")
    return all_articles


def get_available_feeds() -> list[FeedSource]:
    """Get list of available feed sources."""
    return DEFAULT_FEEDS.copy()

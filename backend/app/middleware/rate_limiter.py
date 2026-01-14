"""
Rate Limiter Middleware for PAI API

Provides IP-based rate limiting with:
- In-memory request tracking
- Configurable requests per minute
- Automatic cleanup of old requests
"""

import asyncio
from collections import defaultdict
from datetime import datetime, timedelta

from fastapi import HTTPException, Request

from app.core.config import settings


class RateLimiter:
    """Simple in-memory rate limiter."""

    def __init__(self, requests_per_minute: int | None = None):
        """
        Initialize rate limiter.

        Args:
            requests_per_minute: Maximum requests allowed per minute.
                                 Defaults to settings.RATE_LIMIT_REQUESTS.
        """
        self.requests_per_minute = requests_per_minute or settings.RATE_LIMIT_REQUESTS
        self.requests: dict[str, list[datetime]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def is_allowed(self, client_ip: str) -> bool:
        """
        Check if the client is allowed to make a request.

        Args:
            client_ip: The client's IP address.

        Returns:
            True if request is allowed, False otherwise.
        """
        async with self._lock:
            now = datetime.now()
            minute_ago = now - timedelta(minutes=1)

            # Clean old requests
            self.requests[client_ip] = [
                req_time for req_time in self.requests[client_ip]
                if req_time > minute_ago
            ]

            if len(self.requests[client_ip]) >= self.requests_per_minute:
                return False

            self.requests[client_ip].append(now)
            return True

    async def __call__(self, request: Request) -> None:
        """
        FastAPI dependency for rate limiting.

        Args:
            request: The incoming FastAPI request.

        Raises:
            HTTPException: 429 if rate limit is exceeded.
        """
        client_ip = request.client.host if request.client else "unknown"

        if not await self.is_allowed(client_ip):
            raise HTTPException(
                status_code=429,
                detail={
                    "code": "rate_limit_exceeded",
                    "message": "Too many requests. Please try again later.",
                    "retry_after_seconds": 60
                }
            )


# Global rate limiter instance
rate_limiter = RateLimiter()

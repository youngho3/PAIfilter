"""
API Endpoint Tests

Tests for all PAI API endpoints including:
- Health check
- Vectorize
- Context
- Search
- Insight
"""

import pytest
from fastapi import status


class TestHealthEndpoint:
    """Tests for the root health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_check_returns_online_status(self, async_client):
        """GET / should return service status."""
        response = await async_client.get("/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "online"
        assert data["service"] == "PAI Intelligence Engine"
        assert "config" in data

    @pytest.mark.asyncio
    async def test_health_check_shows_config_status(self, async_client):
        """Health check should indicate API configuration status."""
        response = await async_client.get("/")
        data = response.json()

        assert "gemini_configured" in data["config"]
        assert "pinecone_configured" in data["config"]


class TestVectorizeEndpoint:
    """Tests for the /api/v1/vectorize endpoint."""

    @pytest.mark.asyncio
    async def test_vectorize_success(self, async_client):
        """POST /api/v1/vectorize should return vector data."""
        response = await async_client.post(
            "/api/v1/vectorize",
            json={"text": "Test input text"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "original_text" in data
        assert data["original_text"] == "Test input text"
        assert "vector_dimension" in data
        assert data["vector_dimension"] == 768
        assert "vector_preview" in data
        assert len(data["vector_preview"]) == 5

    @pytest.mark.asyncio
    async def test_vectorize_empty_text_rejected(self, async_client):
        """Empty text should be rejected with 422."""
        response = await async_client.post(
            "/api/v1/vectorize",
            json={"text": ""}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_vectorize_missing_text_field(self, async_client):
        """Missing text field should return 422."""
        response = await async_client.post(
            "/api/v1/vectorize",
            json={}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_vectorize_whitespace_only_rejected(self, async_client):
        """Whitespace-only text should be rejected."""
        response = await async_client.post(
            "/api/v1/vectorize",
            json={"text": "   "}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestContextEndpoint:
    """Tests for the /api/v1/context endpoint."""

    @pytest.mark.asyncio
    async def test_store_context_success(self, async_client):
        """POST /api/v1/context should store and return ID."""
        response = await async_client.post(
            "/api/v1/context",
            json={"text": "My business concern about user acquisition"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert "id" in data
        assert "message" in data

    @pytest.mark.asyncio
    async def test_store_context_empty_text(self, async_client):
        """Empty text should be rejected."""
        response = await async_client.post(
            "/api/v1/context",
            json={"text": ""}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestSearchEndpoint:
    """Tests for the /api/v1/search endpoint."""

    @pytest.mark.asyncio
    async def test_search_returns_matches(self, async_client):
        """POST /api/v1/search should return similar contexts."""
        response = await async_client.post(
            "/api/v1/search",
            json={"text": "SaaS growth strategies"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "matches" in data
        assert len(data["matches"]) > 0

    @pytest.mark.asyncio
    async def test_search_with_custom_top_k(self, async_client):
        """Search should respect top_k parameter."""
        response = await async_client.post(
            "/api/v1/search",
            json={"text": "Test query", "top_k": 5}
        )

        assert response.status_code == status.HTTP_200_OK


class TestInsightEndpoint:
    """Tests for the /api/v1/insight endpoint."""

    @pytest.mark.asyncio
    async def test_insight_returns_response(self, async_client):
        """POST /api/v1/insight should return AI insight."""
        response = await async_client.post(
            "/api/v1/insight",
            json={"text": "How do I grow my user base?"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "insight" in data
        assert "context_used" in data
        assert isinstance(data["insight"], str)
        assert len(data["insight"]) > 0

    @pytest.mark.asyncio
    async def test_insight_empty_text_rejected(self, async_client):
        """Empty text should be rejected."""
        response = await async_client.post(
            "/api/v1/insight",
            json={"text": ""}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

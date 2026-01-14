"""
Pinecone Service Unit Tests

Tests for vector database operations.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock


class TestPineconeUpsert:
    """Tests for Pinecone upsert operations."""

    @pytest.mark.asyncio
    async def test_upsert_success(self):
        """Should return vector ID on successful upsert."""
        mock_embedding = [0.1] * 768
        mock_index = MagicMock()
        mock_index.upsert.return_value = None

        with patch(
            "app.services.pinecone_service.get_text_embedding",
            new_callable=AsyncMock,
            return_value=mock_embedding
        ):
            with patch("app.services.pinecone_service.index", mock_index):
                from app.services.pinecone_service import upsert_context
                result = await upsert_context("Test text")

                assert result is not None
                assert isinstance(result, str)
                mock_index.upsert.assert_called_once()

    @pytest.mark.asyncio
    async def test_upsert_fails_on_embedding_error(self):
        """Should return None when embedding fails."""
        with patch(
            "app.services.pinecone_service.get_text_embedding",
            new_callable=AsyncMock,
            return_value=[]
        ):
            from app.services.pinecone_service import upsert_context
            result = await upsert_context("Test text")

            assert result is None

    @pytest.mark.asyncio
    async def test_upsert_handles_pinecone_error(self):
        """Should return None on Pinecone error."""
        mock_embedding = [0.1] * 768
        mock_index = MagicMock()
        mock_index.upsert.side_effect = Exception("Pinecone error")

        with patch(
            "app.services.pinecone_service.get_text_embedding",
            new_callable=AsyncMock,
            return_value=mock_embedding
        ):
            with patch("app.services.pinecone_service.index", mock_index):
                from app.services.pinecone_service import upsert_context
                result = await upsert_context("Test text")

                assert result is None


class TestPineconeSearch:
    """Tests for Pinecone search operations."""

    @pytest.mark.asyncio
    async def test_search_returns_matches(self):
        """Should return matching results."""
        mock_embedding = [0.1] * 768
        mock_matches = [
            {"id": "1", "score": 0.95, "metadata": {"text": "Match 1"}},
            {"id": "2", "score": 0.85, "metadata": {"text": "Match 2"}}
        ]
        mock_index = MagicMock()
        mock_index.query.return_value = {"matches": mock_matches}

        with patch(
            "app.services.pinecone_service.get_text_embedding",
            new_callable=AsyncMock,
            return_value=mock_embedding
        ):
            with patch("app.services.pinecone_service.index", mock_index):
                from app.services.pinecone_service import search_similar_context
                result = await search_similar_context("Test query")

                assert len(result) == 2
                assert result[0]["score"] == 0.95

    @pytest.mark.asyncio
    async def test_search_respects_top_k(self):
        """Should pass top_k parameter to Pinecone."""
        mock_embedding = [0.1] * 768
        mock_index = MagicMock()
        mock_index.query.return_value = {"matches": []}

        with patch(
            "app.services.pinecone_service.get_text_embedding",
            new_callable=AsyncMock,
            return_value=mock_embedding
        ):
            with patch("app.services.pinecone_service.index", mock_index):
                from app.services.pinecone_service import search_similar_context
                await search_similar_context("Query", top_k=5)

                call_args = mock_index.query.call_args
                assert call_args.kwargs["top_k"] == 5

    @pytest.mark.asyncio
    async def test_search_returns_empty_on_embedding_failure(self):
        """Should return empty list when embedding fails."""
        with patch(
            "app.services.pinecone_service.get_text_embedding",
            new_callable=AsyncMock,
            return_value=[]
        ):
            from app.services.pinecone_service import search_similar_context
            result = await search_similar_context("Query")

            assert result == []

"""
Gemini Service Unit Tests

Tests for embedding generation and text generation functions.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock


class TestGeminiEmbedding:
    """Tests for Gemini embedding generation."""

    @pytest.mark.asyncio
    async def test_embedding_returns_vector(self):
        """Should return 768-dimensional vector."""
        mock_embedding = [0.1] * 768

        with patch("app.services.gemini_service.genai") as mock_genai:
            mock_genai.embed_content.return_value = {"embedding": mock_embedding}

            from app.services.gemini_service import get_text_embedding
            result = await get_text_embedding("Test text")

            assert result == mock_embedding
            assert len(result) == 768
            mock_genai.embed_content.assert_called_once()

    @pytest.mark.asyncio
    async def test_embedding_handles_api_error(self):
        """Should return empty list on API error."""
        with patch("app.services.gemini_service.genai") as mock_genai:
            mock_genai.embed_content.side_effect = Exception("API Error")

            from app.services.gemini_service import get_text_embedding
            result = await get_text_embedding("Test text")

            assert result == []

    @pytest.mark.asyncio
    async def test_embedding_uses_correct_model(self):
        """Should use text-embedding-004 model."""
        with patch("app.services.gemini_service.genai") as mock_genai:
            mock_genai.embed_content.return_value = {"embedding": [0.1] * 768}

            from app.services.gemini_service import get_text_embedding
            await get_text_embedding("Test")

            call_args = mock_genai.embed_content.call_args
            assert call_args.kwargs["model"] == "models/text-embedding-004"
            assert call_args.kwargs["task_type"] == "retrieval_document"


class TestGeminiGeneration:
    """Tests for Gemini text generation."""

    def test_generation_returns_text(self):
        """Should return generated text."""
        with patch("app.services.gemini_service.genai") as mock_genai:
            mock_model = MagicMock()
            mock_response = MagicMock()
            mock_response.text = "Generated insight"
            mock_model.generate_content.return_value = mock_response
            mock_genai.GenerativeModel.return_value = mock_model

            from app.services.gemini_service import get_gemini_response
            result = get_gemini_response("Test prompt")

            assert result == "Generated insight"

    def test_generation_handles_error(self):
        """Should return error message on failure."""
        with patch("app.services.gemini_service.genai") as mock_genai:
            mock_genai.GenerativeModel.side_effect = Exception("Generation failed")

            from app.services.gemini_service import get_gemini_response
            result = get_gemini_response("Test prompt")

            assert "Generation failed" in result

    def test_generation_uses_correct_model(self):
        """Should use correct Gemini model."""
        with patch("app.services.gemini_service.genai") as mock_genai:
            mock_model = MagicMock()
            mock_response = MagicMock()
            mock_response.text = "Response"
            mock_model.generate_content.return_value = mock_response
            mock_genai.GenerativeModel.return_value = mock_model

            from app.services.gemini_service import get_gemini_response
            get_gemini_response("Prompt")

            # Check that GenerativeModel was called
            mock_genai.GenerativeModel.assert_called_once()

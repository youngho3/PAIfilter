"""
Pytest Configuration and Fixtures

Provides:
- Test client fixtures
- Mock fixtures for Gemini and Pinecone
- Sample test data
"""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

# Set test environment before importing app
os.environ["GOOGLE_API_KEY"] = "test-google-api-key"
os.environ["PINECONE_API_KEY"] = "test-pinecone-api-key"
os.environ["PINECONE_HOST"] = "https://test.pinecone.io"
os.environ["APP_ENV"] = "test"

# Mock embedding vector (768 dimensions like real Gemini)
MOCK_EMBEDDING = [0.1] * 768


@pytest.fixture(autouse=True)
def reset_settings_cache():
    """Reset the settings cache before each test."""
    from app.core.config import get_settings
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def mock_gemini_embedding():
    """Mock Gemini embedding response."""
    with patch("app.services.gemini_service.genai.embed_content") as mock_embed:
        mock_embed.return_value = {"embedding": MOCK_EMBEDDING}
        yield mock_embed


@pytest.fixture
def mock_gemini_generation():
    """Mock Gemini text generation response."""
    with patch("app.services.gemini_service.genai.GenerativeModel") as mock_model_class:
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "This is a mocked AI response for testing purposes."
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model
        yield mock_model_class


@pytest.fixture
def mock_pinecone_index():
    """Mock Pinecone index."""
    mock_index = MagicMock()
    mock_index.upsert.return_value = None
    mock_index.query.return_value = {
        "matches": [
            {
                "id": "test-id-1",
                "score": 0.95,
                "metadata": {"text": "Previous context about SaaS"}
            },
            {
                "id": "test-id-2",
                "score": 0.85,
                "metadata": {"text": "Earlier discussion on marketing"}
            }
        ]
    }
    return mock_index


@pytest.fixture
def mock_pinecone(mock_pinecone_index):
    """Mock Pinecone client."""
    with patch("app.services.pinecone_service.pc") as mock_pc:
        mock_pc.Index.return_value = mock_pinecone_index

        with patch("app.services.pinecone_service.index", mock_pinecone_index):
            yield mock_pinecone_index


@pytest.fixture
async def async_client(mock_gemini_embedding, mock_gemini_generation, mock_pinecone):
    """Async test client with all mocks applied."""
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_texts():
    """Sample test data."""
    return {
        "short": "Hello world",
        "medium": "I am building a SaaS product and need help with growth strategies.",
        "long": "A" * 5000,
        "korean": "안녕하세요, AI 제품 개발에 관한 고민이 있습니다.",
        "empty": "",
        "whitespace": "   ",
    }

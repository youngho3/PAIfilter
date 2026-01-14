"""
Gemini AI Service Module

Provides text embedding and content generation capabilities
using Google's Gemini AI models.
"""

import logging

import google.generativeai as genai

from app.core.config import settings

logger = logging.getLogger(__name__)

# Configure Gemini with API key
genai.configure(api_key=settings.GOOGLE_API_KEY.get_secret_value())


async def get_text_embedding(text: str) -> list[float]:
    """
    Generate a vector embedding for the given text using Gemini.

    Args:
        text: The input text to embed (1-10000 characters).

    Returns:
        A 768-dimensional float vector representing the text embedding.
        Returns empty list if embedding generation fails.

    Example:
        >>> embedding = await get_text_embedding("Hello, world!")
        >>> len(embedding)
        768
    """
    try:
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type="retrieval_document",
        )
        embedding = result["embedding"]
        logger.debug(f"Generated embedding with {len(embedding)} dimensions")
        return embedding
    except Exception as e:
        logger.error(f"Gemini Embedding Error: {e}", exc_info=True)
        return []


def get_gemini_response(prompt: str, model_name: str = "gemini-3-flash-preview") -> str:
    """
    Generate a text response using Gemini's generative model.

    Args:
        prompt: The input prompt for text generation.
        model_name: The Gemini model to use. Defaults to "gemini-3-flash-preview".

    Returns:
        The generated text response. Returns error message string on failure.

    Example:
        >>> response = get_gemini_response("Explain quantum computing briefly.")
        >>> isinstance(response, str)
        True
    """
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        logger.debug(f"Generated response using {model_name}")
        return response.text
    except Exception as e:
        logger.error(f"Gemini Generation Error: {e}", exc_info=True)
        return f"Error generating response: {str(e)}"

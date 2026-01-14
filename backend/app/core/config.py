"""
PAI Configuration Module

Provides application configuration using Pydantic settings with:
- SecretStr for sensitive data protection
- Cached settings instance for performance
- Environment-specific configuration
"""

import os
from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration with validation and documentation."""

    # Required API Keys (use SecretStr for sensitive data)
    GOOGLE_API_KEY: SecretStr = Field(
        ...,
        description="Google Generative AI API key for Gemini"
    )
    PINECONE_API_KEY: SecretStr = Field(
        default=SecretStr(""),
        description="Pinecone vector database API key"
    )

    # Pinecone Configuration
    PINECONE_INDEX_NAME: str = Field(
        default="pai",
        description="Name of the Pinecone index"
    )
    PINECONE_ENV: str = Field(
        default="us-east-1",
        description="Pinecone environment/region"
    )
    PINECONE_HOST: str = Field(
        default="",
        description="Pinecone host URL"
    )

    # Application Settings
    APP_ENV: str = Field(
        default="development",
        description="Application environment (development/staging/production)"
    )
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level"
    )
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000"],
        description="Allowed CORS origins"
    )

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = Field(
        default=100,
        description="Maximum requests per minute"
    )

    model_config = SettingsConfigDict(
        env_file=os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            ".env"
        ),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True
    )


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance for dependency injection."""
    return Settings()


settings = get_settings()

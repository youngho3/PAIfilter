"""
Custom Exception Handlers for PAI API

Provides:
- Base PAI exception class
- Specialized exceptions for different error types
- FastAPI exception handlers
"""

import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.models.responses import ErrorCode, ErrorDetail, ErrorResponse

logger = logging.getLogger(__name__)


class PAIException(Exception):
    """Base exception for PAI application."""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        details: dict | None = None,
        status_code: int = 500
    ):
        """
        Initialize PAI exception.

        Args:
            code: Error code from ErrorCode enum.
            message: Human-readable error message.
            details: Additional error details.
            status_code: HTTP status code.
        """
        self.code = code
        self.message = message
        self.details = details
        self.status_code = status_code
        super().__init__(message)


class EmbeddingError(PAIException):
    """Raised when embedding generation fails."""

    def __init__(
        self,
        message: str = "Failed to generate embedding",
        details: dict | None = None
    ):
        super().__init__(
            code=ErrorCode.EMBEDDING_FAILED,
            message=message,
            details=details,
            status_code=502
        )


class VectorDBError(PAIException):
    """Raised when vector database operation fails."""

    def __init__(
        self,
        message: str = "Vector database operation failed",
        details: dict | None = None
    ):
        super().__init__(
            code=ErrorCode.VECTOR_DB_ERROR,
            message=message,
            details=details,
            status_code=502
        )


class AIGenerationError(PAIException):
    """Raised when AI text generation fails."""

    def __init__(
        self,
        message: str = "AI generation failed",
        details: dict | None = None
    ):
        super().__init__(
            code=ErrorCode.AI_GENERATION_ERROR,
            message=message,
            details=details,
            status_code=502
        )


# Exception Handlers
async def pai_exception_handler(request: Request, exc: PAIException) -> JSONResponse:
    """Handle PAI custom exceptions."""
    logger.error(
        f"PAI Exception: {exc.code} - {exc.message}",
        extra={"details": exc.details}
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=ErrorDetail(
                code=exc.code,
                message=exc.message,
                details=exc.details
            )
        ).model_dump(mode="json")
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors."""
    errors = exc.errors()
    logger.warning(f"Validation error: {errors}")

    # Convert errors to serializable format (remove non-serializable objects)
    serializable_errors = []
    for err in errors:
        serializable_err = {
            "type": err.get("type"),
            "loc": err.get("loc"),
            "msg": err.get("msg"),
        }
        # Only include input if it's a basic type
        if isinstance(err.get("input"), (str, int, float, bool, type(None))):
            serializable_err["input"] = err.get("input")
        serializable_errors.append(serializable_err)

    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": {
                "code": ErrorCode.VALIDATION_ERROR.value,
                "message": "Request validation failed",
                "details": {"errors": serializable_errors}
            }
        }
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    logger.error(f"Unexpected error: {exc}", exc_info=True)

    # Import here to avoid circular import
    from app.core.config import settings

    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error=ErrorDetail(
                code=ErrorCode.INTERNAL_ERROR,
                message="An unexpected error occurred",
                details={"type": type(exc).__name__} if settings.APP_ENV == "development" else None
            )
        ).model_dump(mode="json")
    )

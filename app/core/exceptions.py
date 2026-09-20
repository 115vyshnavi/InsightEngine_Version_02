"""InsightEngine Custom Domain Exceptions."""

from typing import Any, Optional


class InsightEngineException(Exception):
    """Base exception for all InsightEngine errors."""

    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class PDFParsingError(InsightEngineException):
    """Raised when PDF document parsing or rendering fails."""
    pass


class TableExtractionError(InsightEngineException):
    """Raised when structured financial table extraction fails."""
    pass


class OCRError(InsightEngineException):
    """Raised when OCR execution on scanned pages fails."""
    pass


class RetrievalError(InsightEngineException):
    """Raised when dense, sparse, or hybrid retrieval fails."""
    pass


class CalculationError(InsightEngineException):
    """Raised when financial arithmetic calculation fails or is undefined."""
    pass


class LLMGenerationError(InsightEngineException):
    """Raised when LLM provider returns an error or invalid response."""
    pass


class DocumentNotFoundError(InsightEngineException):
    """Raised when a requested document ID does not exist in store."""
    pass

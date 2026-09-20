"""Query schemas for API endpoints."""

from typing import Optional
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """User query input schema."""
    question: str = Field(..., description="Financial question to analyze, e.g. What was the revenue growth from Q2 to Q3?")
    document_id: Optional[str] = Field(default=None, description="Optional target document ID. If omitted, searches all uploaded documents.")
    top_k_retrieval: Optional[int] = Field(default=None, description="Optional override for initial hybrid candidate count.")
    top_k_reranked: Optional[int] = Field(default=None, description="Optional override for final reranked evidence count.")

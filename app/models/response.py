"""Structured financial response schemas."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class CalculationDetails(BaseModel):
    """Deterministic calculation metadata."""
    formula: str = Field(..., description="Mathematical formula used")
    inputs: Dict[str, Any] = Field(..., description="Raw input values extracted directly from source")
    steps: Optional[str] = Field(default=None, description="Step-by-step arithmetic substitution")
    result: float = Field(..., description="Computed numerical result")
    formatted_result: Optional[str] = Field(default=None, description="Formatted string with percentage or currency")


class SourceCitation(BaseModel):
    """Source citation maintaining strict forensic grounding."""
    document_name: str
    page_number: Optional[int] = None
    section: Optional[str] = None
    content_type: str = "text"
    snippet: Optional[str] = None
    citation_text: str


class DataPoint(BaseModel):
    """Specific financial metric extracted from context."""
    metric: str
    value: str
    period: Optional[str] = None
    source_reference: Optional[str] = None


class QueryResponse(BaseModel):
    """Complete structured response matching Section 11 & Section 4."""
    answer: str = Field(..., description="Direct synthesized financial answer")
    data_points: List[DataPoint] = Field(default_factory=list, description="Verified source numbers and metrics")
    calculation: Optional[CalculationDetails] = Field(default=None, description="Deterministic arithmetic calculation")
    sources: List[SourceCitation] = Field(default_factory=list, description="Explicit verified document citations")
    confidence: Optional[float] = Field(default=None, description="Confidence score if reliably known, or null")
    raw_context: Optional[List[Dict[str, Any]]] = Field(default=None, description="Evidence chunks retrieved")

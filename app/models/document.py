"""Document data schemas and metadata models."""

from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    """Metadata schema required for strict source citation."""
    document_id: str
    page_number: int
    content_type: Literal["text", "table", "chart", "heading"] = "text"
    section: Optional[str] = "General"
    parent_id: Optional[str] = None
    source: str
    table_id: Optional[str] = None
    extra: Dict[str, Any] = Field(default_factory=dict)


class TableElement(BaseModel):
    """Structured financial table element."""
    table_id: str
    document_id: str
    page_number: int
    section: Optional[str] = "Consolidated Statements"
    raw_markdown: str
    headers: List[str] = Field(default_factory=list)
    rows: List[List[str]] = Field(default_factory=list)
    summary: str
    source: str


class DocumentChunk(BaseModel):
    """A granular chunk indexed into the retrieval system."""
    chunk_id: str
    parent_id: str
    document_id: str
    page_number: int
    content_type: Literal["text", "table", "chart", "heading"]
    content: str  # For text: chunk text. For table: generated summary for retrieval
    raw_content: Optional[str] = None  # Original raw markdown table or complete parent text
    section: Optional[str] = None
    source: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProcessedDocument(BaseModel):
    """Complete representation of an ingested document."""
    document_id: str
    company_name: Optional[str] = "Unknown Company"
    filename: str
    file_path: str
    total_pages: int
    chunks_count: int
    tables_count: int
    created_at: str
    summary: Optional[str] = None

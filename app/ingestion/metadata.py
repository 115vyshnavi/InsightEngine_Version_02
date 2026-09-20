"""Metadata generation and tagging for financial chunks."""

import uuid
from typing import Optional, Dict, Any
from app.models.document import DocumentMetadata


def create_metadata(
    document_id: str,
    page_number: int,
    source: str,
    content_type: str = "text",
    section: Optional[str] = "General",
    parent_id: Optional[str] = None,
    table_id: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> DocumentMetadata:
    """Creates a validated DocumentMetadata instance for citation tracking."""
    return DocumentMetadata(
        document_id=document_id,
        page_number=page_number,
        content_type=content_type,  # type: ignore
        section=section or "General",
        parent_id=parent_id or str(uuid.uuid4()),
        source=source,
        table_id=table_id,
        extra=extra or {},
    )

"""Parent Document Store for resolving context windows."""

from typing import Dict, Optional, List
from app.models.document import DocumentChunk


class ParentStore:
    """Stores full parent contexts (entire statements, raw markdown tables, full pages)."""

    def __init__(self):
        # parent_id -> full raw text/markdown
        self.parents: Dict[str, str] = {}
        # parent_id -> metadata
        self.metadata: Dict[str, dict] = {}

    def register_parent(self, parent_id: str, content: str, meta: Optional[dict] = None) -> None:
        """Stores a full parent context."""
        self.parents[parent_id] = content
        if meta:
            self.metadata[parent_id] = meta

    def get_parent_context(self, chunk: DocumentChunk) -> str:
        """
        Returns full parent context for a chunk.
        If chunk has raw_content (e.g. raw markdown table), returns that.
        Otherwise checks parent store, falling back to chunk content.
        """
        if chunk.raw_content and len(chunk.raw_content.strip()) > 0:
            return chunk.raw_content

        if chunk.parent_id and chunk.parent_id in self.parents:
            return self.parents[chunk.parent_id]

        return chunk.content

    def clear(self) -> None:
        self.parents.clear()
        self.metadata.clear()


parent_store = ParentStore()

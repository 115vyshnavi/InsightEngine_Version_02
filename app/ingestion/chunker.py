"""Hierarchical Chunking Engine with Table-Aware Multi-Vector Indexing."""

import uuid
import re
from typing import List, Dict, Any
from app.models.document import DocumentChunk, TableElement
from app.core.logging import logger


class FinancialChunker:
    """
    Creates discrete semantic chunks while preserving financial tables as atomic units
    and maintaining parent-child relations for narrative disclosures.
    """

    def __init__(self, text_chunk_size: int = 600, chunk_overlap: int = 100):
        self.text_chunk_size = text_chunk_size
        self.chunk_overlap = chunk_overlap

    def process_document(
        self,
        document_id: str,
        filename: str,
        pages: List[Dict[str, Any]],
        tables: List[TableElement],
    ) -> List[DocumentChunk]:
        """
        Transforms parsed pages and tables into indexed DocumentChunks.
        - Tables are kept 100% intact as atomic units with summary for retrieval and raw_markdown for answering.
        - Text is split into coherent paragraphs/chunks linked to parent page context.
        """
        chunks: List[DocumentChunk] = []

        # 1. Process Tables First (Multi-Vector Table Ingestion)
        for tbl in tables:
            chunk_id = f"chunk_tbl_{tbl.table_id}"
            parent_id = f"parent_page_{tbl.page_number}_{tbl.document_id}"

            # The content for embedding/retrieval is the summary + headers
            retrieval_content = (
                f"Table Title/Section: {tbl.section} (Page {tbl.page_number})\n"
                f"Summary: {tbl.summary}\n"
                f"Columns: {', '.join(tbl.headers)}\n"
            )

            # The raw_content returned to the LLM is the exact markdown grid
            table_chunk = DocumentChunk(
                chunk_id=chunk_id,
                parent_id=parent_id,
                document_id=document_id,
                page_number=tbl.page_number,
                content_type="table",
                content=retrieval_content,
                raw_content=tbl.raw_markdown,
                section=tbl.section,
                source=filename,
                metadata={
                    "headers": tbl.headers,
                    "row_count": len(tbl.rows),
                    "table_id": tbl.table_id,
                },
            )
            chunks.append(table_chunk)

        # 2. Process Narrative Text (Parent-Child Hierarchy)
        for page_data in pages:
            page_num = page_data["page_number"]
            page_text = page_data["text"].strip()
            section = page_data["section"]
            parent_id = f"parent_page_{page_num}_{document_id}"

            if not page_text:
                continue

            # Split text by paragraphs
            paragraphs = [p.strip() for p in page_text.split("\n\n") if p.strip()]
            current_buffer = ""

            for p_idx, para in enumerate(paragraphs):
                # If paragraph exceeds chunk size, subdivide with overlap
                if len(para) > self.text_chunk_size:
                    sub_chunks = self._sliding_window_split(para, self.text_chunk_size, self.chunk_overlap)
                    for s_idx, sub in enumerate(sub_chunks):
                        chunks.append(
                            DocumentChunk(
                                chunk_id=f"chunk_txt_p{page_num}_{p_idx}_{s_idx}_{uuid.uuid4().hex[:6]}",
                                parent_id=parent_id,
                                document_id=document_id,
                                page_number=page_num,
                                content_type="text",
                                content=sub,
                                raw_content=para,  # Parent context
                                section=section,
                                source=filename,
                                metadata={"paragraph_index": p_idx},
                            )
                        )
                else:
                    if len(current_buffer) + len(para) < self.text_chunk_size:
                        current_buffer += ("\n\n" if current_buffer else "") + para
                    else:
                        if current_buffer:
                            chunks.append(
                                DocumentChunk(
                                    chunk_id=f"chunk_txt_p{page_num}_{p_idx}_{uuid.uuid4().hex[:6]}",
                                    parent_id=parent_id,
                                    document_id=document_id,
                                    page_number=page_num,
                                    content_type="text",
                                    content=current_buffer,
                                    raw_content=current_buffer,
                                    section=section,
                                    source=filename,
                                    metadata={"page": page_num},
                                )
                            )
                        current_buffer = para

            if current_buffer:
                chunks.append(
                    DocumentChunk(
                        chunk_id=f"chunk_txt_p{page_num}_tail_{uuid.uuid4().hex[:6]}",
                        parent_id=parent_id,
                        document_id=document_id,
                        page_number=page_num,
                        content_type="text",
                        content=current_buffer,
                        raw_content=current_buffer,
                        section=section,
                        source=filename,
                        metadata={"page": page_num},
                    )
                )

        logger.info(
            f"Chunked document {filename}: generated {len(chunks)} chunks ({len(tables)} tables, {len(chunks)-len(tables)} text blocks)."
        )
        return chunks

    def _sliding_window_split(self, text: str, size: int, overlap: int) -> List[str]:
        """Splits long text with overlapping character windows respecting sentence boundaries."""
        sentences = re.split(r"(?<=[.?!])\s+", text)
        result = []
        cur = ""
        for s in sentences:
            if len(cur) + len(s) > size and cur:
                result.append(cur.strip())
                # Keep tail of previous buffer for overlap
                words = cur.split()
                cur = " ".join(words[-max(1, len(words) // 5) :]) + " " + s
            else:
                cur += (" " if cur else "") + s
        if cur:
            result.append(cur.strip())
        return result or [text]


financial_chunker = FinancialChunker()

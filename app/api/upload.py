"""Document upload and ingestion endpoint."""

import os
import uuid
import datetime
from pathlib import Path
from typing import Callable, Dict, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import PDFParsingError
from app.models.document import ProcessedDocument
from app.ingestion.pdf_parser import pdf_parser
from app.ingestion.chunker import financial_chunker
from app.retrieval.vector_store import vector_store
from app.retrieval.bm25 import bm25_index
from app.retrieval.parent_store import parent_store

router = APIRouter(tags=["Document Ingestion"])

DOCUMENT_REGISTRY: Dict[str, ProcessedDocument] = {}


async def _ingest_document(
    file: UploadFile = File(...),
    company_name: str = Form(default="Unknown Company"),
    progress_callback: Optional[Callable[[int, str], None]] = None,
):
    """Uploads a corporate earnings report PDF and indexes it for retrieval."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Unsupported file type. Only PDF documents are supported for financial analysis.")

    company_label = (company_name or "Unknown Company").strip() or "Unknown Company"
    document_id = f"doc_{uuid.uuid4().hex[:10]}"
    safe_filename = Path(file.filename).name
    saved_path = settings.UPLOAD_DIR / f"{document_id}_{safe_filename}"

    try:
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Uploaded PDF is empty (0 bytes).")

        with open(saved_path, "wb") as f:
            f.write(content)
        if progress_callback:
            progress_callback(15, "File saved. Extracting PDF text and tables...")

        logger.info(f"Saved uploaded file {file.filename} to {saved_path}")
        pages_data, tables = pdf_parser.parse_pdf(str(saved_path), document_id, safe_filename)
        if progress_callback:
            progress_callback(35, f"PDF extracted: {len(pages_data)} pages and {len(tables)} tables found.")

        for p in pages_data:
            parent_id = f"parent_page_{p['page_number']}_{document_id}"
            parent_store.register_parent(parent_id, p["text"], {"section": p["section"]})

        chunks = financial_chunker.process_document(document_id, safe_filename, pages_data, tables)
        if progress_callback:
            progress_callback(50, f"Prepared {len(chunks)} searchable chunks. Building indexes...")
        vector_store.add_chunks(chunks)
        if progress_callback:
            progress_callback(85, "Semantic index built. Updating keyword index...")
        bm25_index.build_index(list(vector_store.chunks.values()))
        if progress_callback:
            progress_callback(95, "Finalizing document registration...")

        doc_record = ProcessedDocument(
            document_id=document_id,
            company_name=company_label,
            filename=safe_filename,
            file_path=str(saved_path),
            total_pages=len(pages_data),
            chunks_count=len(chunks),
            tables_count=len(tables),
            created_at=datetime.datetime.utcnow().isoformat() + "Z",
            summary=f"Indexed {len(pages_data)} pages, {len(tables)} financial tables, and {len(chunks)} retrieval chunks.",
        )

        DOCUMENT_REGISTRY[document_id] = doc_record
        logger.info(f"Successfully ingested and indexed document: {doc_record.filename}")
        return doc_record

    except PDFParsingError as ppe:
        logger.error(f"PDF parsing error: {ppe.message}")
        if saved_path.exists():
            os.remove(saved_path)
        raise HTTPException(status_code=422, detail=f"Failed to process financial PDF: {ppe.message}")
    except Exception as e:
        logger.error(f"Unexpected error during document upload: {e}")
        if saved_path.exists():
            os.remove(saved_path)
        raise HTTPException(status_code=500, detail=f"Internal ingestion error: {str(e)}")


@router.post("/upload", response_model=ProcessedDocument)
async def upload_document(
    file: UploadFile = File(...),
    company_name: str = Form(default="Unknown Company"),
):
    """Public upload route; internal progress callbacks stay out of the API schema."""
    return await _ingest_document(file=file, company_name=company_name)

"""Query and document management endpoints."""

from typing import List
from fastapi import APIRouter, HTTPException
from app.models.query import QueryRequest
from app.models.response import QueryResponse
from app.models.document import ProcessedDocument
from app.api.upload import DOCUMENT_REGISTRY
from app.retrieval.hybrid_search import hybrid_search_engine
from app.retrieval.vector_store import vector_store
from app.retrieval.bm25 import bm25_index
from app.llm.answer_generator import answer_generator
from app.core.logging import logger

router = APIRouter(tags=["Financial Analysis & Querying"])


@router.post("/query", response_model=QueryResponse)
def query_financial_report(request: QueryRequest):
    """
    Executes financial question answering over uploaded documents:
    1. Hybrid retrieval (Dense vector + BM25 keyword)
    2. Reciprocal Rank Fusion (top 15)
    3. FlashRank reranking (top 3-4)
    4. Parent document context resolution
    5. Deterministic calculation engine
    6. Forensic LLM answer generation with strict citations
    """
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Query question cannot be empty.")

    if not DOCUMENT_REGISTRY and len(vector_store.chunks) == 0:
        return QueryResponse(
            answer="No documents have been uploaded yet. Please upload a corporate financial report PDF first.",
            data_points=[],
            calculation=None,
            sources=[],
            confidence=None,
        )

    try:
        evidence = hybrid_search_engine.search(
            query=question,
            document_id=request.document_id,
            top_k_candidates=request.top_k_retrieval,
            top_k_final=request.top_k_reranked,
        )
        response = answer_generator.generate_answer(question=question, evidence=evidence)
        return response
    except Exception as e:
        logger.error(f"Error during query execution: {e}")
        raise HTTPException(status_code=500, detail=f"Query execution failure: {str(e)}")


@router.get("/documents", response_model=List[ProcessedDocument])
def list_documents():
    """Returns list of all uploaded and indexed corporate financial reports."""
    return list(DOCUMENT_REGISTRY.values())


@router.delete("/documents/{document_id}")
def delete_document(document_id: str):
    """Deletes an indexed document and its chunks from vector and keyword stores."""
    if document_id not in DOCUMENT_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Document with ID {document_id} not found.")

    doc = DOCUMENT_REGISTRY.pop(document_id)
    vector_store.delete_document(document_id)
    bm25_index.remove_document(document_id)

    logger.info(f"Deleted document {doc.filename} (ID: {document_id})")
    return {"message": f"Successfully deleted document {doc.filename}", "document_id": document_id}

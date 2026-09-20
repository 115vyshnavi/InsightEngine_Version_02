"""Health check endpoint."""

from fastapi import APIRouter
from app.api.upload import DOCUMENT_REGISTRY
from app.core.config import settings
from app.retrieval.vector_store import vector_store

router = APIRouter(tags=["Health"])


@router.get("/health")
def get_health():
    """Returns application health and indexing status."""
    qdrant_ready = settings.VECTOR_DB != "qdrant" or vector_store.qdrant_client is not None
    return {
        "status": "healthy" if qdrant_ready else "degraded",
        "service": "InsightEngine Financial RAG",
        "version": "1.0.0",
        "llm_provider": settings.LLM_PROVIDER,
        "embedding_model": settings.EMBEDDING_MODEL,
        "vector_db": settings.VECTOR_DB,
        "total_indexed_chunks": len(vector_store.chunks),
        "qdrant_ready": qdrant_ready,
    }

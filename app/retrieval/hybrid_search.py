"""Hybrid Retrieval Engine combining Dense Vectors, BM25, and Reciprocal Rank Fusion."""

from typing import List, Dict, Optional, Tuple
from app.models.document import DocumentChunk
from app.core.config import settings
from app.core.logging import logger
from app.retrieval.vector_store import vector_store
from app.retrieval.bm25 import bm25_index
from app.retrieval.reranker import reranker
from app.retrieval.parent_store import parent_store


class HybridSearchEngine:
    """
    Combines dense semantic vector search and BM25 exact keyword search
    using Reciprocal Rank Fusion (RRF), then passes candidates to FlashRank reranking
    and resolves parent document context.
    """

    def __init__(self, rrf_k: int = 60):
        self.rrf_k = rrf_k

    def search(
        self,
        query: str,
        document_id: Optional[str] = None,
        top_k_candidates: Optional[int] = None,
        top_k_final: Optional[int] = None,
    ) -> List[Tuple[DocumentChunk, str]]:
        """
        Executes the full hybrid retrieval pipeline:
        1. Dense Vector Search (top_k_candidates)
        2. BM25 Keyword Search (top_k_candidates)
        3. Reciprocal Rank Fusion (RRF) -> merged candidates (~15)
        4. FlashRank Reranker -> top evidence (~3-4)
        5. Parent Document Resolution -> returns (DocumentChunk, full_parent_context)
        """
        k_candidates = top_k_candidates or settings.TOP_K_RETRIEVAL
        k_final = top_k_final or settings.TOP_K_RERANKED

        # 1. Retrieve Dense Candidates
        dense_results = vector_store.search(query, top_k=k_candidates, document_id=document_id)

        # 2. Retrieve BM25 Candidates
        bm25_results = bm25_index.search(query, top_k=k_candidates, document_id=document_id)

        logger.debug(
            f"Hybrid search candidates: Dense={len(dense_results)}, BM25={len(bm25_results)}"
        )

        # 3. Reciprocal Rank Fusion (RRF)
        rrf_scores: Dict[str, float] = {}
        chunk_map: Dict[str, DocumentChunk] = {}

        # Add dense ranks
        for rank, (chunk, _) in enumerate(dense_results):
            cid = chunk.chunk_id
            chunk_map[cid] = chunk
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (self.rrf_k + rank + 1))

        # Add BM25 ranks
        for rank, (chunk, _) in enumerate(bm25_results):
            cid = chunk.chunk_id
            chunk_map[cid] = chunk
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (self.rrf_k + rank + 1))

        # Sort merged candidates by RRF score
        sorted_chunks = sorted(
            chunk_map.values(), key=lambda c: rrf_scores.get(c.chunk_id, 0.0), reverse=True
        )
        candidates = sorted_chunks[:k_candidates]

        # 4. FlashRank Reranking
        reranked_chunks = reranker.rerank(query, candidates, top_k=k_final)

        # 5. Parent Document Resolution
        final_evidence: List[Tuple[DocumentChunk, str]] = []
        for chk in reranked_chunks:
            full_context = parent_store.get_parent_context(chk)
            final_evidence.append((chk, full_context))

        logger.info(
            f"Hybrid retrieval finished for query='{query[:40]}...': returned {len(final_evidence)} reranked evidence items."
        )
        return final_evidence


hybrid_search_engine = HybridSearchEngine()

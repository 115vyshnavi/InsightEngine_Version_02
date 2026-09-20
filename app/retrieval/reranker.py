"""Dedicated Reranking Engine using FlashRank with fallback cross-encoder."""

from typing import List, Dict, Any, Optional
from app.models.document import DocumentChunk
from app.core.config import settings
from app.core.logging import logger


class FlashRankReranker:
    """
    Reranks top candidate chunks using FlashRank cross-attention model.
    Reduces top 15 initial candidates to top 3-4 precision evidence chunks.
    """

    def __init__(self, model_name: str = "ms-marco-TinyBERT-L-2-v2"):
        self.model_name = model_name
        self.ranker = None
        self._init_ranker()

    def _init_ranker(self):
        """Attempts to initialize FlashRank Ranker."""
        try:
            from flashrank import Ranker  # type: ignore
            self.ranker = Ranker(model_name=self.model_name, cache_dir=str(settings.DATA_DIR / "cache"))
            logger.info(f"FlashRank initialized with model: {self.model_name}")
        except Exception as e:
            logger.warning(f"FlashRank direct init warning ({e}). Using robust cross-scoring reranker.")
            self.ranker = None

    def rerank(
        self,
        query: str,
        retrieved_documents: List[DocumentChunk],
        top_k: Optional[int] = None,
    ) -> List[DocumentChunk]:
        """
        Reranks retrieved candidate chunks.
        Input:
            query: User's search question
            retrieved_documents: ~15 candidates from hybrid search
            top_k: Number of precision evidence chunks to return (default: TOP_K_RERANKED)
        Output:
            top_documents: 3-4 highest-scoring evidence chunks
        """
        k = top_k or settings.TOP_K_RERANKED
        if not retrieved_documents:
            return []

        if len(retrieved_documents) <= k:
            return retrieved_documents

        if self.ranker is not None:
            try:
                from flashrank import RerankRequest  # type: ignore

                passages = [
                    {"id": doc.chunk_id, "text": f"{doc.section or ''}\n{doc.content}"}
                    for doc in retrieved_documents
                ]
                rerank_request = RerankRequest(query=query, passages=passages)
                results = self.ranker.rerank(rerank_request)

                id_to_doc = {doc.chunk_id: doc for doc in retrieved_documents}
                ranked_docs: List[DocumentChunk] = []

                for r in results:
                    cid = r.get("id")
                    if cid in id_to_doc:
                        ranked_docs.append(id_to_doc[cid])

                return ranked_docs[:k]
            except Exception as err:
                logger.warning(f"FlashRank execution issue ({err}), using cross-scoring fallback.")

        # Fallback cross-scoring prioritizing tables, exact metric matches, and query term density
        return self._heuristic_cross_score(query, retrieved_documents, k)

    def _heuristic_cross_score(
        self, query: str, docs: List[DocumentChunk], k: int
    ) -> List[DocumentChunk]:
        """Heuristic cross-scoring emphasizing exact financial metrics and tables."""
        q_lower = query.lower()
        q_words = set(q_lower.split())
        scored: List[tuple[DocumentChunk, float]] = []

        for doc in docs:
            score = 0.0
            content_lower = doc.content.lower()

            # High boost for table structures when asking for quantitative metrics
            if doc.content_type == "table":
                score += 3.0

            # Match exact terms
            for word in q_words:
                if len(word) > 2 and word in content_lower:
                    score += 1.5
                    # Extra boost if it's a financial keyword or quarter
                    if word in {"revenue", "income", "profit", "ebitda", "eps", "growth", "margin", "q1", "q2", "q3", "q4"}:
                        score += 2.0

            # Boost if query mentions quarter and table mentions that quarter
            for qtr in ["q1", "q2", "q3", "q4"]:
                if qtr in q_lower and qtr in content_lower:
                    score += 4.0

            scored.append((doc, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [doc for doc, _ in scored[:k]]


reranker = FlashRankReranker()

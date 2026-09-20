"""BM25 Keyword Search Engine customized for financial terminology."""

import re
import math
from typing import List, Tuple, Dict, Optional
from rank_bm25 import BM25Okapi
from app.models.document import DocumentChunk
from app.core.logging import logger


class BM25Index:
    """BM25 keyword search index optimized for exact financial entity matches."""

    def __init__(self):
        self.chunks: List[DocumentChunk] = []
        self.bm25_model: Optional[BM25Okapi] = None
        self.corpus_tokens: List[List[str]] = []

    @staticmethod
    def tokenize(text: str) -> List[str]:
        """
        Specialized tokenizer for financial documents.
        Preserves:
          - Quarters: Q1, Q2, Q3, Q4, FY23, FY24
          - Currency symbols: $, €, £
          - Metric tokens: EBITDA, EPS, GAAP, Net, Income, Margin, Growth
          - Numerical tokens: 12M, 50%, 8.5
        """
        if not text:
            return []

        # Standardize quarters and common abbreviations
        text_norm = re.sub(r"\b([Qq])([1-4])\b", r"q\2", text)

        # Extract tokens preserving financial numbers and acronyms
        raw_tokens = re.findall(r"[\$\€\£]?[a-zA-Z0-9_\-\.\%]+", text_norm.lower())
        stopwords = {"the", "a", "an", "in", "on", "at", "to", "for", "of", "and", "or", "is", "was", "were", "are", "be"}

        filtered = [t for t in raw_tokens if t not in stopwords and len(t) > 1]
        return filtered

    def build_index(self, chunks: List[DocumentChunk]) -> None:
        """Builds or refreshes the BM25 index with current chunks."""
        self.chunks = list(chunks)
        if not self.chunks:
            self.bm25_model = None
            self.corpus_tokens = []
            return

        self.corpus_tokens = [
            self.tokenize(f"{c.content} {c.section or ''} {c.raw_content or ''}")
            for c in self.chunks
        ]
        self.bm25_model = BM25Okapi(self.corpus_tokens)
        logger.info(f"BM25 index built with {len(self.chunks)} documents.")

    def search(
        self, query: str, top_k: int = 15, document_id: Optional[str] = None
    ) -> List[Tuple[DocumentChunk, float]]:
        """Searches BM25 index for keyword relevance."""
        if not self.bm25_model or not self.chunks:
            return []

        q_tokens = self.tokenize(query)
        if not q_tokens:
            return []

        scores = self.bm25_model.get_scores(q_tokens)
        results: List[Tuple[DocumentChunk, float]] = []

        for idx, score in enumerate(scores):
            if score <= 0:
                continue
            chunk = self.chunks[idx]
            if document_id and chunk.document_id != document_id:
                continue
            results.append((chunk, float(score)))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def remove_document(self, document_id: str) -> None:
        """Removes a document from BM25 corpus and rebuilds."""
        remaining = [c for c in self.chunks if c.document_id != document_id]
        self.build_index(remaining)


bm25_index = BM25Index()

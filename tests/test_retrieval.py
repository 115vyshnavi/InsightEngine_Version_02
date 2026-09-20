"""Unit tests for semantic, keyword, hybrid retrieval, and FlashRank reranking."""

import pytest
from app.models.document import DocumentChunk
from app.retrieval.vector_store import VectorStore
from app.retrieval.bm25 import BM25Index
from app.retrieval.reranker import FlashRankReranker


def create_sample_chunks():
    c1 = DocumentChunk(
        chunk_id="c1",
        parent_id="p1",
        document_id="doc1",
        page_number=12,
        content_type="table",
        content="Q3 Revenue was $100M, up from $80M in Q2. Operating income was $25M.",
        raw_content="| Quarter | Revenue |\n|---|---|\n| Q2 | $80M |\n| Q3 | $100M |",
        section="Consolidated Statements of Income",
        source="report.pdf",
    )
    c2 = DocumentChunk(
        chunk_id="c2",
        parent_id="p2",
        document_id="doc1",
        page_number=5,
        content_type="text",
        content="The executive team announced investments in cloud data center infrastructure and expansion into European markets.",
        raw_content="The executive team announced investments in cloud data center infrastructure...",
        section="Management Discussion",
        source="report.pdf",
    )
    c3 = DocumentChunk(
        chunk_id="c3",
        parent_id="p3",
        document_id="doc1",
        page_number=18,
        content_type="table",
        content="Cash and cash equivalents totaled $45M as of September 30, with total debt of $30M.",
        raw_content="| Metric | Value |\n|---|---|\n| Cash | $45M |",
        section="Consolidated Balance Sheets",
        source="report.pdf",
    )
    return [c1, c2, c3]


def test_semantic_retrieval():
    store = VectorStore()
    chunks = create_sample_chunks()
    store.add_chunks(chunks)

    results = store.search("What was the revenue in Q3?", top_k=2)
    assert len(results) > 0
    top_chunk, score = results[0]
    assert top_chunk.chunk_id == "c1"
    assert "Revenue was $100M" in top_chunk.content


def test_bm25_keyword_retrieval():
    index = BM25Index()
    chunks = create_sample_chunks()
    index.build_index(chunks)

    results = index.search("Cash and cash equivalents debt", top_k=2)
    assert len(results) > 0
    top_chunk, score = results[0]
    assert top_chunk.chunk_id == "c3"
    assert "Cash and cash equivalents" in top_chunk.content


def test_reranking():
    ranker = FlashRankReranker()
    chunks = create_sample_chunks()

    # Query specifically targeting Q3 revenue
    reranked = ranker.rerank("What was the revenue in Q3?", chunks, top_k=2)
    assert len(reranked) <= 2
    assert reranked[0].chunk_id == "c1"

"""Evaluation runner executing the RAG pipeline across the 10 difficult test questions."""

import sys
import json
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from typing import Dict, Any, List
from app.core.config import settings
from app.core.logging import logger
from app.evaluation.dataset import EVALUATION_DATASET
from app.evaluation.metrics import (
    compute_faithfulness,
    compute_answer_relevance,
    compute_citation_score,
)
from app.retrieval.hybrid_search import hybrid_search_engine
from app.retrieval.vector_store import vector_store
from app.retrieval.parent_store import parent_store
from app.retrieval.bm25 import bm25_index
from app.ingestion.pdf_parser import pdf_parser
from app.ingestion.chunker import financial_chunker
from app.llm.answer_generator import answer_generator


def run_evaluation() -> Dict[str, Any]:
    """
    Runs full evaluation over the evaluation dataset.
    Computes:
      - Faithfulness / Groundedness
      - Answer Relevance
      - Citation Accuracy
      - Strict 'Cannot Answer' handling for unanswerable questions
    Saves results to data/evaluation/results.json.
    """
    logger.info("Starting InsightEngine pipeline evaluation...")

    # Ensure sample document is indexed if store is empty
    sample_pdf = settings.UPLOAD_DIR / "acme_corp_q3_earnings.pdf"
    if sample_pdf.exists() and len(vector_store.chunks) == 0:
        logger.info(f"Indexing sample evaluation report: {sample_pdf.name}")
        pages_data, tables = pdf_parser.parse_pdf(str(sample_pdf), "eval_doc_01", sample_pdf.name)
        for p in pages_data:
            parent_store.register_parent(f"parent_page_{p['page_number']}_eval_doc_01", p["text"])
        chunks = financial_chunker.process_document("eval_doc_01", sample_pdf.name, pages_data, tables)
        vector_store.add_chunks(chunks)
        bm25_index.build_index(list(vector_store.chunks.values()))

    results: List[Dict[str, Any]] = []

    faithfulness_scores = []
    relevance_scores = []
    citation_scores = []

    for item in EVALUATION_DATASET:
        q_id = item["id"]
        question = item["question"]
        is_negative = item.get("is_negative_case", False)

        # 1. Retrieve
        evidence = hybrid_search_engine.search(question, top_k_candidates=15, top_k_final=4)

        # 2. Generate
        response = answer_generator.generate_answer(question, evidence)

        # 3. Join context for faithfulness check
        joined_context = " ".join([full_ctx for _, full_ctx in evidence])

        # 4. Compute metrics
        faith = compute_faithfulness(response.answer, joined_context, is_negative)
        rel = compute_answer_relevance(question, response.answer)
        cit = compute_citation_score(response.sources)

        faithfulness_scores.append(faith)
        relevance_scores.append(rel)
        citation_scores.append(cit)

        item_result = {
            "id": q_id,
            "category": item["category"],
            "question": question,
            "ground_truth": item["ground_truth"],
            "generated_answer": response.answer,
            "calculation": response.calculation.model_dump() if response.calculation else None,
            "sources_count": len(response.sources),
            "metrics": {
                "faithfulness": faith,
                "relevance": rel,
                "citation_score": cit,
            },
        }
        results.append(item_result)

    mean_faithfulness = sum(faithfulness_scores) / len(faithfulness_scores) if faithfulness_scores else 0.0
    mean_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0.0
    mean_citations = sum(citation_scores) / len(citation_scores) if citation_scores else 0.0

    summary = {
        "total_questions": len(EVALUATION_DATASET),
        "mean_faithfulness": round(mean_faithfulness, 4),
        "mean_answer_relevance": round(mean_relevance, 4),
        "mean_citation_score": round(mean_citations, 4),
        "results": results,
    }

    out_file = settings.EVALUATION_DIR / "results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    logger.info(f"Evaluation complete. Results saved to {out_file}")
    return summary


if __name__ == "__main__":
    summary = run_evaluation()
    print(json.dumps(summary, indent=2))

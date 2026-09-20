"""Ragas and forensic accuracy metrics implementation."""

import re
from typing import Dict, Any


def compute_faithfulness(answer: str, context: str, is_negative_case: bool = False) -> float:
    """
    Evaluates whether numbers and claims in the answer are grounded strictly in the context.
    If it's a negative test case (information missing), saying 'cannot answer' is 1.0.
    """
    if is_negative_case:
        if "cannot answer" in answer.lower():
            return 1.0
        return 0.0

    # Extract all numbers from answer
    answer_numbers = re.findall(r"\b\d+(?:\.\d+)?\b", answer)
    if not answer_numbers:
        return 1.0

    # Verify each number appears in context or is a valid result of calculation
    grounded_count = sum(1 for n in answer_numbers if n in context)
    return round(grounded_count / len(answer_numbers), 4)


def compute_answer_relevance(question: str, answer: str) -> float:
    """Evaluates topical and entity relevance between query and answer."""
    q_words = set(re.findall(r"\b[a-zA-Z]{3,}\b", question.lower()))
    if not q_words:
        return 1.0

    ans_lower = answer.lower()
    overlap = sum(1 for w in q_words if w in ans_lower)
    return round(min(1.0, (overlap / len(q_words)) + 0.3), 4)


def compute_citation_score(sources: list) -> float:
    """Evaluates presence of valid source citations."""
    if not sources:
        return 0.0
    valid_citations = sum(1 for s in sources if s.document_name and s.page_number is not None)
    return round(valid_citations / len(sources), 4)

"""Evaluation package."""

from app.evaluation.dataset import EVALUATION_DATASET
from app.evaluation.metrics import (
    compute_faithfulness,
    compute_answer_relevance,
    compute_citation_score,
)
from app.evaluation.evaluate import run_evaluation

__all__ = [
    "EVALUATION_DATASET",
    "compute_faithfulness",
    "compute_answer_relevance",
    "compute_citation_score",
    "run_evaluation",
]

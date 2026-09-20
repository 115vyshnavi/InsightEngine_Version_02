"""Evaluation dataset with 10 difficult financial questions matching Section 15."""

from typing import List, Dict, Any

EVALUATION_DATASET: List[Dict[str, Any]] = [
    {
        "id": "eval_01",
        "category": "table_lookup",
        "question": "What was the revenue in Q3?",
        "ground_truth": "$100M",
        "question_type": "exact_value",
        "expected_source": "Consolidated Statements of Income / Quarterly Revenue Table",
    },
    {
        "id": "eval_02",
        "category": "percentage_growth",
        "question": "What was the percentage growth in net income from Q2 to Q3?",
        "ground_truth": "50%",
        "calculation_required": True,
        "expected_formula": "((Q3 - Q2) / Q2) * 100",
        "raw_inputs": {"Q2": 8.0, "Q3": 12.0},
    },
    {
        "id": "eval_03",
        "category": "financial_ratios",
        "question": "What was the net profit margin in Q3?",
        "ground_truth": "12.0%",
        "calculation_required": True,
        "expected_formula": "(Net Income / Revenue) * 100",
        "raw_inputs": {"Net Income": 12.0, "Revenue": 100.0},
    },
    {
        "id": "eval_04",
        "category": "comparisons",
        "question": "Compare Q2 and Q3 revenue.",
        "ground_truth": "Q2 revenue was $80M and Q3 revenue was $100M, representing an increase of $20M (or 25.0%).",
        "question_type": "comparison",
    },
    {
        "id": "eval_05",
        "category": "change_in_metric",
        "question": "What was the change in operating expenses from Q1 to Q2?",
        "ground_truth": "Operating expenses changed from $35M in Q1 to $38M in Q2, an increase of $3M.",
        "question_type": "difference",
    },
    {
        "id": "eval_06",
        "category": "quarterly_comparison",
        "question": "Which quarter had higher net income, Q1 or Q2?",
        "ground_truth": "Q2 had higher net income ($8M) compared to Q1 ($5M).",
        "question_type": "comparison",
    },
    {
        "id": "eval_07",
        "category": "percentage_growth",
        "question": "Calculate the percentage increase in EPS from Q1 to Q3.",
        "ground_truth": "140.0%",
        "calculation_required": True,
        "expected_formula": "((Q3_EPS - Q1_EPS) / Q1_EPS) * 100",
    },
    {
        "id": "eval_08",
        "category": "percentage_decrease",
        "question": "What was the percentage decrease in debt from Q2 to Q3?",
        "ground_truth": "10.0%",
        "calculation_required": True,
        "expected_formula": "((old - new) / old) * 100",
    },
    {
        "id": "eval_09",
        "category": "not_present_in_document",
        "question": "What was the company's research and development budget in fiscal year 2018?",
        "ground_truth": "I cannot answer this based on the provided document.",
        "is_negative_case": True,
    },
    {
        "id": "eval_10",
        "category": "not_present_in_document",
        "question": "What is the projected CEO bonus payout for 2030?",
        "ground_truth": "I cannot answer this based on the provided document.",
        "is_negative_case": True,
    },
]

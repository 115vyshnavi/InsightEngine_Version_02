"""Standard financial metrics definitions and terminology."""

from typing import Dict, List

STANDARD_METRICS: Dict[str, Dict[str, str]] = {
    "revenue": {
        "name": "Revenue",
        "aliases": ["total revenue", "sales", "net sales", "turnover", "total sales"],
        "category": "Income Statement",
    },
    "net_income": {
        "name": "Net Income",
        "aliases": ["net profit", "earnings", "net earnings", "bottom line", "profit after tax"],
        "category": "Income Statement",
    },
    "operating_income": {
        "name": "Operating Income",
        "aliases": ["operating profit", "ebit", "operating earnings"],
        "category": "Income Statement",
    },
    "gross_profit": {
        "name": "Gross Profit",
        "aliases": ["gross margin (dollars)", "gross earnings"],
        "category": "Income Statement",
    },
    "operating_expenses": {
        "name": "Operating Expenses",
        "aliases": ["opex", "total operating expenses", "sg&a", "r&d"],
        "category": "Income Statement",
    },
    "eps": {
        "name": "Earnings Per Share",
        "aliases": ["diluted eps", "basic eps", "net income per share"],
        "category": "Per Share Metrics",
    },
    "ebitda": {
        "name": "EBITDA",
        "aliases": ["earnings before interest, taxes, depreciation, and amortization"],
        "category": "Non-GAAP Metrics",
    },
    "cash_and_equivalents": {
        "name": "Cash and Cash Equivalents",
        "aliases": ["cash", "liquid assets", "marketable securities"],
        "category": "Balance Sheet",
    },
    "free_cash_flow": {
        "name": "Free Cash Flow",
        "aliases": ["fcf", "operating cash flow minus capex"],
        "category": "Cash Flow Statement",
    },
}

FINANCIAL_ACRONYMS: List[str] = [
    "EBITDA", "EBIT", "EPS", "GAAP", "Non-GAAP", "CAGR", "SG&A", "R&D", "FCF", "ROIC", "ROE", "ROA", "P/E", "Q1", "Q2", "Q3", "Q4", "FY", "YoY", "QoQ"
]

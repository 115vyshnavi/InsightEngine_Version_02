"""Financial value parsing and forensic validation."""

import re
from typing import Optional, Tuple


def parse_financial_number(text: str) -> Optional[float]:
    """
    Parses financial string representation into exact float.
    Handles:
      - Parentheses for negative numbers: (50) -> -50
      - Currencies: $120.5M, €50B, £30K
      - Suffixes: M (million), B (billion), K (thousand), T (trillion), %
      - Commas in numbers: 1,234,567.89
    """
    if not text or not isinstance(text, str):
        return None

    cleaned = text.strip()
    is_negative = False

    # Check for accounting parentheses e.g. (1,240.5) or ($50M)
    if (cleaned.startswith("(") and cleaned.endswith(")")) or cleaned.startswith("-"):
        is_negative = True
        cleaned = cleaned.strip("()-")

    # Remove currency symbols and whitespace
    cleaned = re.sub(r"[\$\€\£\¥\₹\s]", "", cleaned)

    # Detect scale multiplier
    multiplier = 1.0
    if cleaned.endswith("%"):
        cleaned = cleaned[:-1]
    elif cleaned.endswith("k") or cleaned.endswith("K"):
        multiplier = 1_000.0
        cleaned = cleaned[:-1]
    elif cleaned.endswith("m") or cleaned.endswith("M") or cleaned.endswith("mn"):
        multiplier = 1_000_000.0
        cleaned = re.sub(r"(mn|m|M)$", "", cleaned)
    elif cleaned.endswith("b") or cleaned.endswith("B") or cleaned.endswith("bn"):
        multiplier = 1_000_000_000.0
        cleaned = re.sub(r"(bn|b|B)$", "", cleaned)
    elif cleaned.endswith("t") or cleaned.endswith("T"):
        multiplier = 1_000_000_000_000.0
        cleaned = cleaned[:-1]

    # Remove thousands separators
    cleaned = cleaned.replace(",", "")

    try:
        val = float(cleaned) * multiplier
        return -val if is_negative else val
    except ValueError:
        return None


def extract_unit_and_currency(text: str) -> Tuple[Optional[str], Optional[str]]:
    """Identifies currency symbol and scaling unit from financial statement header/context."""
    currency = None
    if "$" in text:
        currency = "USD ($)"
    elif "€" in text:
        currency = "EUR (€)"
    elif "£" in text:
        currency = "GBP (£)"
    elif "¥" in text:
        currency = "JPY (¥)"

    unit = None
    lower = text.lower()
    if "in billions" in lower or "(in billions)" in lower:
        unit = "billions"
    elif "in millions" in lower or "(in millions)" in lower:
        unit = "millions"
    elif "in thousands" in lower or "(in thousands)" in lower:
        unit = "thousands"

    return currency, unit

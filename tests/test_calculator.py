"""Unit tests for the Deterministic Financial Calculator."""

import pytest
from app.finance.calculator import FinancialCalculator
from app.core.exceptions import CalculationError


def test_percentage_growth():
    # Growth from 8 to 12 should be ((12 - 8) / 8) * 100 = 50%
    result = FinancialCalculator.percentage_growth(old_value=8.0, new_value=12.0)
    assert result.result == 50.0
    assert result.formula == "((new_value - old_value) / old_value) * 100"
    assert "50.00%" in result.formatted_result


def test_percentage_growth_division_by_zero():
    with pytest.raises(CalculationError, match="division by zero"):
        FinancialCalculator.percentage_growth(old_value=0.0, new_value=10.0)


def test_percentage_decrease():
    # Decrease from 100 to 80 should be ((100 - 80) / 100) * 100 = 20%
    result = FinancialCalculator.percentage_decrease(old_value=100.0, new_value=80.0)
    assert result.result == 20.0
    assert "20.00%" in result.formatted_result


def test_margin():
    # Net profit margin: 15 / 100 = 15%
    result = FinancialCalculator.margin(numerator=15.0, denominator=100.0)
    assert result.result == 15.0
    assert "15.00%" in result.formatted_result


def test_ratio():
    # Current ratio: 200 / 100 = 2.0x
    result = FinancialCalculator.ratio(numerator=200.0, denominator=100.0)
    assert result.result == 2.0
    assert "2.00x" in result.formatted_result


def test_cagr():
    # CAGR from 100 to 144 over 2 periods: ((144 / 100) ** (1/2) - 1) * 100 = 20%
    result = FinancialCalculator.cagr(start_value=100.0, end_value=144.0, periods=2.0)
    assert result.result == 20.0
    assert "20.00%" in result.formatted_result

"""Deterministic Financial Calculation Engine.

Implements exact arithmetic for financial analysis to prevent LLM calculation errors.
Never silently performs arithmetic. Always returns source formula, inputs, and steps.
"""

from typing import Dict, Any, Optional
from app.core.exceptions import CalculationError
from app.models.response import CalculationDetails


class FinancialCalculator:
    """Deterministic financial calculator returning auditable computation metadata."""

    @staticmethod
    def percentage_growth(old_value: float, new_value: float) -> CalculationDetails:
        """Calculate percentage growth: ((new - old) / old) * 100."""
        if old_value == 0:
            raise CalculationError("Cannot calculate percentage growth: base value is zero (division by zero).")

        result = ((new_value - old_value) / old_value) * 100
        formula = "((new_value - old_value) / old_value) * 100"
        steps = f"(({new_value} - {old_value}) / {old_value}) * 100 = {result:.4f}%"

        return CalculationDetails(
            formula=formula,
            inputs={"old_value": old_value, "new_value": new_value},
            steps=steps,
            result=round(result, 4),
            formatted_result=f"{result:+.2f}%" if result != 0 else "0.00%",
        )

    @staticmethod
    def percentage_decrease(old_value: float, new_value: float) -> CalculationDetails:
        """Calculate percentage decrease: ((old - new) / old) * 100."""
        if old_value == 0:
            raise CalculationError("Cannot calculate percentage decrease: base value is zero (division by zero).")

        result = ((old_value - new_value) / old_value) * 100
        formula = "((old_value - new_value) / old_value) * 100"
        steps = f"(({old_value} - {new_value}) / {old_value}) * 100 = {result:.4f}%"

        return CalculationDetails(
            formula=formula,
            inputs={"old_value": old_value, "new_value": new_value},
            steps=steps,
            result=round(result, 4),
            formatted_result=f"{result:.2f}%",
        )

    @staticmethod
    def margin(numerator: float, denominator: float) -> CalculationDetails:
        """Calculate financial margin (e.g. net profit margin, gross margin): (part / total) * 100."""
        if denominator == 0:
            raise CalculationError("Cannot calculate margin: denominator (revenue/total) is zero.")

        result = (numerator / denominator) * 100
        formula = "(numerator / denominator) * 100"
        steps = f"({numerator} / {denominator}) * 100 = {result:.4f}%"

        return CalculationDetails(
            formula=formula,
            inputs={"numerator": numerator, "denominator": denominator},
            steps=steps,
            result=round(result, 4),
            formatted_result=f"{result:.2f}%",
        )

    @staticmethod
    def ratio(numerator: float, denominator: float) -> CalculationDetails:
        """Calculate financial ratio (e.g. Current Ratio, Debt-to-Equity): numerator / denominator."""
        if denominator == 0:
            raise CalculationError("Cannot calculate ratio: denominator is zero.")

        result = numerator / denominator
        formula = "numerator / denominator"
        steps = f"{numerator} / {denominator} = {result:.4f}"

        return CalculationDetails(
            formula=formula,
            inputs={"numerator": numerator, "denominator": denominator},
            steps=steps,
            result=round(result, 4),
            formatted_result=f"{result:.2f}x",
        )

    @staticmethod
    def difference(value_a: float, value_b: float) -> CalculationDetails:
        """Calculate absolute difference between two values: value_a - value_b."""
        result = value_a - value_b
        formula = "value_a - value_b"
        steps = f"{value_a} - {value_b} = {result:.4f}"

        return CalculationDetails(
            formula=formula,
            inputs={"value_a": value_a, "value_b": value_b},
            steps=steps,
            result=round(result, 4),
            formatted_result=f"{result:+.2f}",
        )

    @staticmethod
    def change(old_value: float, new_value: float) -> CalculationDetails:
        """Calculate net change (new - old)."""
        result = new_value - old_value
        formula = "new_value - old_value"
        steps = f"{new_value} - {old_value} = {result:.4f}"

        return CalculationDetails(
            formula=formula,
            inputs={"old_value": old_value, "new_value": new_value},
            steps=steps,
            result=round(result, 4),
            formatted_result=f"{result:+.2f}",
        )

    @staticmethod
    def cagr(start_value: float, end_value: float, periods: float) -> CalculationDetails:
        """Calculate Compound Annual Growth Rate (CAGR): ((end / start) ** (1 / periods) - 1) * 100."""
        if start_value <= 0:
            raise CalculationError("Cannot calculate CAGR: start_value must be strictly positive.")
        if end_value <= 0:
            raise CalculationError("Cannot calculate CAGR: end_value must be strictly positive.")
        if periods <= 0:
            raise CalculationError("Cannot calculate CAGR: number of periods must be greater than zero.")

        result = (((end_value / start_value) ** (1.0 / periods)) - 1.0) * 100
        formula = "((end_value / start_value) ** (1 / periods) - 1) * 100"
        steps = f"(({end_value} / {start_value}) ** (1 / {periods}) - 1) * 100 = {result:.4f}%"

        return CalculationDetails(
            formula=formula,
            inputs={"start_value": start_value, "end_value": end_value, "periods": periods},
            steps=steps,
            result=round(result, 4),
            formatted_result=f"{result:.2f}%",
        )

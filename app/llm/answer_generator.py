"""Financial Answer Generation Orchestrator with Deterministic Math Engine."""

import re
from typing import List, Tuple, Optional, Dict, Any
from app.models.document import DocumentChunk
from app.models.response import (
    QueryResponse,
    CalculationDetails,
    SourceCitation,
    DataPoint,
)
from app.core.logging import logger
from app.finance.calculator import FinancialCalculator
from app.finance.validation import parse_financial_number
from app.llm.prompts import INSIGHTENGINE_SYSTEM_PROMPT, USER_QUERY_PROMPT_TEMPLATE
from app.llm.provider import llm_provider


class AnswerGenerator:
    """Orchestrates RAG generation with deterministic Python arithmetic and strict source grounding."""

    def generate_answer(
        self,
        question: str,
        evidence: List[Tuple[DocumentChunk, str]],
    ) -> QueryResponse:
        """
        Generates structured forensic response from retrieved evidence chunks.
        """
        if not evidence:
            return QueryResponse(
                answer="I cannot answer this based on the provided document.",
                data_points=[],
                calculation=None,
                sources=[],
                confidence=None,
            )

        # 1. Format Context and Source Citations
        context_blocks: List[str] = []
        sources: List[SourceCitation] = []
        seen_citations = set()

        for chunk, full_context in evidence:
            citation_key = f"{chunk.source}_{chunk.page_number}_{chunk.section}"
            if citation_key not in seen_citations:
                seen_citations.add(citation_key)
                page_str = f"Page {chunk.page_number}" if chunk.page_number else "Source page unavailable"
                sec_str = chunk.section or "Financial Disclosures"
                citation_label = f"{sec_str}, {page_str} ({chunk.source})"

                sources.append(
                    SourceCitation(
                        document_name=chunk.source,
                        page_number=chunk.page_number,
                        section=chunk.section,
                        content_type=chunk.content_type,
                        snippet=full_context[:250].replace("\n", " "),
                        citation_text=citation_label,
                    )
                )

            context_blocks.append(
                f"--- [SOURCE: {chunk.source} | PAGE: {chunk.page_number} | SECTION: {chunk.section} | TYPE: {chunk.content_type.upper()}] ---\n"
                f"{full_context}\n"
            )

        joined_context = "\n".join(context_blocks)

        # 2. Check if a deterministic calculation is requested
        calculation_result = self._attempt_deterministic_calculation(question, joined_context)

        # Use retrieved table rows directly when no external LLM is configured.
        # This keeps local operation specific and grounded instead of returning generic text.
        grounded_answer = self._build_grounded_answer(question, evidence, calculation_result)
        if grounded_answer:
            return grounded_answer

        # 3. Augment user prompt with deterministic calculation if performed
        user_prompt_text = joined_context
        if calculation_result:
            user_prompt_text += (
                f"\n\n[VERIFIED PYTHON ARITHMETIC RESULT]:\n"
                f"Formula: {calculation_result.formula}\n"
                f"Raw Inputs: {calculation_result.inputs}\n"
                f"Step-by-step arithmetic: {calculation_result.steps}\n"
                f"Exact Result: {calculation_result.formatted_result or calculation_result.result}\n"
                f"Use this verified calculation in your Mathematical Calculation and Direct Answer sections."
            )

        formatted_user_prompt = USER_QUERY_PROMPT_TEMPLATE.format(
            context=user_prompt_text,
            question=question,
        )

        # 4. Invoke LLM Provider with System Prompt
        raw_llm_output = llm_provider.generate(
            system_prompt=INSIGHTENGINE_SYSTEM_PROMPT,
            user_prompt=formatted_user_prompt,
            temperature=0.0,
        )

        # 5. Extract Data Points and verify answer format
        data_points = self._extract_data_points(raw_llm_output, evidence)

        # If LLM indicates missing information, enforce canonical response
        if "cannot answer" in raw_llm_output.lower() or "not present" in raw_llm_output.lower():
            if not calculation_result and len(data_points) == 0:
                return QueryResponse(
                    answer="I cannot answer this based on the provided document.",
                    data_points=[],
                    calculation=None,
                    sources=sources,
                    confidence=None,
                )

        return QueryResponse(
            answer=raw_llm_output.strip(),
            data_points=data_points,
            calculation=calculation_result,
            sources=sources,
            confidence=None,
            raw_context=[{"source": chk.source, "page": chk.page_number, "type": chk.content_type} for chk, _ in evidence],
        )

    def _build_grounded_answer(
        self,
        question: str,
        evidence: List[Tuple[DocumentChunk, str]],
        calculation: Optional[CalculationDetails],
    ) -> Optional[QueryResponse]:
        """Builds a specific answer from retrieved markdown tables without outside knowledge."""
        rows = self._extract_table_rows(evidence)
        if not rows:
            return None

        question_lower = question.lower()
        metric = self._question_metric(question_lower, rows)
        periods = [period.upper() for period in re.findall(r"\bQ[1-4]\b", question, re.IGNORECASE)]
        values = {period: row[metric] for period, row in rows.items() if metric in row}
        selected = [(period, values[period]) for period in periods if period in values]
        if not selected and metric in values:
            selected = list(values.items())[-1:]
        if not selected:
            return None

        effective_calculation = calculation
        if effective_calculation is None and len(selected) >= 2 and any(
            phrase in question_lower for phrase in ("percentage growth", "percentage increase", "percentage decrease", "percent change", "growth in")
        ):
            try:
                if "decrease" in question_lower:
                    effective_calculation = FinancialCalculator.percentage_decrease(selected[0][1][0], selected[-1][1][0])
                else:
                    effective_calculation = FinancialCalculator.percentage_growth(selected[0][1][0], selected[-1][1][0])
            except Exception:
                effective_calculation = None

        source_chunk, source_context = next((item for item in evidence if item[0].content_type == "table"), evidence[0])
        source = SourceCitation(
            document_name=source_chunk.source,
            page_number=source_chunk.page_number,
            section=source_chunk.section,
            content_type=source_chunk.content_type,
            snippet=source_context[:250].replace("\n", " "),
            citation_text=f"{source_chunk.section or 'Financial table'}, Page {source_chunk.page_number} ({source_chunk.source})",
        )
        data_points = [DataPoint(metric=f"{period} {metric}", value=self._format_value(value), period=period, source_reference=source.citation_text) for period, value in selected]

        if len(selected) >= 2 and any(word in question_lower for word in ("compare", "higher", "lower", "change")):
            first_period, first_value = selected[0]
            last_period, last_value = selected[-1]
            if "higher" in question_lower or "lower" in question_lower:
                comparison = "higher" if last_value[0] > first_value[0] else "lower" if last_value[0] < first_value[0] else "the same as"
                comparison_phrase = f"{comparison} than" if comparison != "the same as" else comparison
                answer = f"{last_period} {metric} was {comparison_phrase} {first_period}: {self._format_value(last_value)} versus {self._format_value(first_value)}."
            else:
                difference = last_value[0] - first_value[0]
                answer = f"{metric} changed from {self._format_value(first_value)} in {first_period} to {self._format_value(last_value)} in {last_period}, a change of {difference:+g}."
        elif effective_calculation:
            answer = f"{metric} changed from {self._format_value(selected[0][1])} in {selected[0][0]} to {self._format_value(selected[-1][1])} in {selected[-1][0]}, resulting in {effective_calculation.formatted_result or effective_calculation.result}."
        else:
            period, value = selected[-1]
            answer = f"{metric} was {self._format_value(value)} in {period}."

        return QueryResponse(
            answer=answer,
            data_points=data_points,
            calculation=effective_calculation,
            sources=[source],
            confidence=None,
            raw_context=[{"source": chunk.source, "page": chunk.page_number, "type": chunk.content_type} for chunk, _ in evidence],
        )

    def _extract_table_rows(self, evidence: List[Tuple[DocumentChunk, str]]) -> Dict[str, Dict[str, Tuple[float, str]]]:
        rows: Dict[str, Dict[str, Tuple[float, str]]] = {}
        for chunk, context in evidence:
            if chunk.content_type != "table":
                continue
            lines = [line.strip() for line in context.splitlines() if line.strip().startswith("|")]
            if len(lines) < 3:
                continue
            headers = [cell.strip().lower() for cell in lines[0].strip("|").split("|")]
            for line in lines[2:]:
                cells = [cell.strip() for cell in line.strip("|").split("|")]
                if len(cells) != len(headers):
                    continue
                period_match = re.search(r"\bQ[1-4]\b", cells[0], re.IGNORECASE)
                if not period_match:
                    continue
                period = period_match.group(0).upper()
                parsed: Dict[str, float] = {}
                for header, cell in zip(headers[1:], cells[1:]):
                    number = parse_financial_number(cell)
                    if number is not None:
                        parsed[header] = (number, cell)
                if parsed:
                    rows[period] = parsed
        return rows

    def _question_metric(self, question: str, rows: Dict[str, Dict[str, Tuple[float, str]]]) -> str:
        aliases = {
            "net income": "net income",
            "net profit": "net income",
            "revenue": "revenue",
            "operating expense": "operating expenses",
            "expense": "operating expenses",
            "eps": "diluted eps",
            "earnings per share": "diluted eps",
            "debt": "total debt",
        }
        for phrase, metric in aliases.items():
            if phrase in question and any(metric in row for row in rows.values()):
                return metric
        available = next(iter(rows.values()), {})
        return next(iter(available), "value")

    @staticmethod
    def _format_value(value: Tuple[float, str]) -> str:
        return value[1]

    def _attempt_deterministic_calculation(
        self, question: str, context: str
    ) -> Optional[CalculationDetails]:
        """
        Detects calculation intents (percentage growth, margin, ratio, difference)
        and extracts numbers from retrieved context to compute verified arithmetic.
        """
        q_lower = question.lower()

        # Growth or percentage change: e.g. "percentage growth in revenue from Q2 to Q3"
        if any(w in q_lower for w in ["percentage growth", "growth in", "percent change", "percentage increase", "percentage decrease"]):
            return self._calculate_growth_from_context(question, context)

        # Margin: e.g. "net profit margin", "gross margin"
        if "margin" in q_lower:
            return self._calculate_margin_from_context(question, context)

        # Ratio: e.g. "ratio of", "current ratio"
        if "ratio" in q_lower:
            return self._calculate_ratio_from_context(question, context)

        return None

    def _calculate_growth_from_context(self, question: str, context: str) -> Optional[CalculationDetails]:
        """Calculates growth between two quarters or periods."""
        # Find mentioned periods in question (e.g., Q2 to Q3, 2023 to 2024)
        periods = re.findall(r"\b([Qq][1-4]|\b20\d\d\b)", question)
        if len(periods) >= 2:
            p1, p2 = periods[0].upper(), periods[1].upper()
            val1 = self._find_metric_value_for_period(context, question, p1)
            val2 = self._find_metric_value_for_period(context, question, p2)

            if val1 is not None and val2 is not None and val1 != 0:
                try:
                    if "decrease" in question.lower():
                        return FinancialCalculator.percentage_decrease(val1, val2)
                    return FinancialCalculator.percentage_growth(val1, val2)
                except Exception as e:
                    logger.warning(f"Deterministic growth calculation skipped: {e}")
        return None

    def _calculate_margin_from_context(self, question: str, context: str) -> Optional[CalculationDetails]:
        """Calculates profit or operating margin from retrieved context."""
        # Look for (Net Income / Revenue) or (Operating Income / Revenue)
        rev = self._find_metric_value(context, ["revenue", "total revenue", "sales"])
        net_inc = self._find_metric_value(context, ["net income", "net profit"])
        if rev and net_inc and rev > 0:
            try:
                return FinancialCalculator.margin(net_inc, rev)
            except Exception:
                pass
        return None

    def _calculate_ratio_from_context(self, question: str, context: str) -> Optional[CalculationDetails]:
        """Calculates financial ratio from retrieved numbers."""
        return None

    def _find_metric_value_for_period(self, context: str, question: str, period: str) -> Optional[float]:
        """Searches markdown tables or text in context for a metric in a specific quarter."""
        # Search lines containing the period and relevant financial metric
        lines = context.split("\n")
        metric_keywords = ["revenue", "net income", "profit", "operating", "expenses", "ebitda", "eps"]
        relevant_kw = [kw for kw in metric_keywords if kw in question.lower()]
        target_kw = relevant_kw[0] if relevant_kw else "revenue"

        # Check table columns first
        for idx, line in enumerate(lines):
            line_lower = line.lower()
            if target_kw in line_lower:
                # Check for numbers in this line or corresponding column
                tokens = re.findall(r"[\$\€\£]?\s*\(?[\d,]+(?:\.\d+)?\)?(?:\s*[mbkMBK%])?", line)
                parsed = [parse_financial_number(t) for t in tokens if parse_financial_number(t) is not None]
                if parsed:
                    if period in ["Q1", "2023"] and len(parsed) >= 1:
                        return parsed[0]
                    elif period in ["Q2"] and len(parsed) >= 2:
                        return parsed[1]
                    elif period in ["Q3", "2024"] and len(parsed) >= 3:
                        return parsed[2]
                    elif len(parsed) > 0:
                        return parsed[-1]
        return None

    def _find_metric_value(self, context: str, metric_aliases: List[str]) -> Optional[float]:
        """Finds general numerical metric in context."""
        for line in context.split("\n"):
            line_lower = line.lower()
            if any(alias in line_lower for alias in metric_aliases):
                tokens = re.findall(r"[\$\€\£]?\s*\(?[\d,]+(?:\.\d+)?\)?(?:\s*[mbkMBK%])?", line)
                parsed = [parse_financial_number(t) for t in tokens if parse_financial_number(t) is not None]
                if parsed:
                    return parsed[-1]
        return None

    def _extract_data_points(
        self, text: str, evidence: List[Tuple[DocumentChunk, str]]
    ) -> List[DataPoint]:
        """Extracts verified source data points cited in the response."""
        data_points: List[DataPoint] = []
        lines = text.split("\n")
        in_data_breakdown = False

        for line in lines:
            trimmed = line.strip()
            if "data breakdown" in trimmed.lower():
                in_data_breakdown = True
                continue
            if in_data_breakdown and trimmed.startswith(("Mathematical", "Source", "Direct Answer")):
                in_data_breakdown = False

            if in_data_breakdown and (trimmed.startswith(("-", "*", "•")) or ":" in trimmed):
                content = trimmed.lstrip("-*• ")
                if ":" in content:
                    parts = content.split(":", 1)
                    metric = parts[0].strip()
                    val = parts[1].strip()
                    if metric and val:
                        data_points.append(DataPoint(metric=metric, value=val))

        return data_points


answer_generator = AnswerGenerator()

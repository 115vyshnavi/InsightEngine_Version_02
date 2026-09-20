"""Multi-vector financial table extraction and summary generation."""

import re
import uuid
from typing import List, Dict, Any, Optional
from app.models.document import TableElement
from app.core.logging import logger


class TableExtractor:
    """Detects, formats, and generates retrieval summaries for financial tables."""

    @staticmethod
    def format_as_markdown(headers: List[str], rows: List[List[str]]) -> str:
        """Converts raw table grid into clean GitHub-flavored markdown."""
        if not headers and not rows:
            return ""

        # Normalize column widths
        col_count = max(len(headers), max((len(r) for r in rows), default=0))
        norm_headers = [headers[i] if i < len(headers) else f"Col {i+1}" for i in range(col_count)]

        header_line = "| " + " | ".join(h.strip() for h in norm_headers) + " |"
        sep_line = "| " + " | ".join("---" for _ in range(col_count)) + " |"

        body_lines = []
        for r in rows:
            norm_row = [r[i].strip() if i < len(r) else "" for i in range(col_count)]
            body_lines.append("| " + " | ".join(norm_row) + " |")

        return "\n".join([header_line, sep_line] + body_lines)

    @staticmethod
    def generate_table_summary(headers: List[str], rows: List[List[str]], section_hint: str = "") -> str:
        """
        Generates an information-dense textual summary of the table
        specifically optimized for dense semantic vector retrieval.
        """
        summary_parts = []
        if section_hint:
            summary_parts.append(f"Financial table in section: {section_hint}.")

        if headers:
            headers_clean = [h for h in headers if h.strip()]
            summary_parts.append(f"Table columns: {', '.join(headers_clean)}.")

        # Identify key financial row metrics
        metric_rows = []
        for row in rows:
            if not row:
                continue
            first_cell = row[0].strip()
            # If the row looks like a metric name
            if len(first_cell) > 1 and not first_cell.isdigit():
                vals = [f"{headers[i] if i < len(headers) else 'col'}: {row[i].strip()}" for i in range(1, len(row)) if i < len(headers) and row[i].strip()]
                if vals:
                    metric_rows.append(f"{first_cell} ({', '.join(vals[:4])})")

        if metric_rows:
            summary_parts.append("Reported financial metrics include: " + "; ".join(metric_rows[:8]) + ".")

        return " ".join(summary_parts)

    def extract_tables_from_text(
        self,
        page_text: str,
        document_id: str,
        page_number: int,
        source: str,
        section: str = "Financial Statements",
    ) -> List[TableElement]:
        """
        Detects tabular structures in text (aligned columns, pipes, or tab-delimited values)
        and constructs TableElements with both raw markdown and retrieval summaries.
        """
        table_elements: List[TableElement] = []
        lines = page_text.split("\n")

        # Detect consecutive lines with multiple delimiters (tabs, pipes, or 3+ multi-space separated columns)
        current_table_lines: List[str] = []
        is_in_table = False

        for line in lines:
            trimmed = line.strip()
            if not trimmed:
                if is_in_table and len(current_table_lines) >= 2:
                    t_elem = self._parse_table_block(
                        current_table_lines, document_id, page_number, source, section
                    )
                    if t_elem:
                        table_elements.append(t_elem)
                current_table_lines = []
                is_in_table = False
                continue

            # Check if line looks like tabular data
            pipe_count = trimmed.count("|")
            tab_count = trimmed.count("\t")
            # Multi-space separated columns
            space_cols = [c.strip() for c in re.split(r"\s{2,}", trimmed) if c.strip()]

            if pipe_count >= 1 or tab_count >= 1 or len(space_cols) >= 2:
                is_in_table = True
                current_table_lines.append(trimmed)
            else:
                if is_in_table and len(current_table_lines) >= 2:
                    t_elem = self._parse_table_block(
                        current_table_lines, document_id, page_number, source, section
                    )
                    if t_elem:
                        table_elements.append(t_elem)
                current_table_lines = []
                is_in_table = False

        if is_in_table and len(current_table_lines) >= 2:
            t_elem = self._parse_table_block(
                current_table_lines, document_id, page_number, source, section
            )
            if t_elem:
                table_elements.append(t_elem)

        return table_elements

    def _parse_table_block(
        self,
        lines: List[str],
        document_id: str,
        page_number: int,
        source: str,
        section: str,
    ) -> Optional[TableElement]:
        """Parses a candidate list of lines into a structured TableElement."""
        if len(lines) < 2:
            return None

        # Determine delimiter
        if lines[0].count("|") >= 1:
            headers = [c.strip() for c in lines[0].split("|") if c.strip()]
            start_idx = 2 if len(lines) > 1 and "---" in lines[1] else 1
            rows = []
            for l in lines[start_idx:]:
                row_cols = [c.strip() for c in l.split("|") if c.strip()]
                if row_cols:
                    rows.append(row_cols)
        elif lines[0].count("\t") >= 1:
            headers = [c.strip() for c in lines[0].split("\t") if c.strip()]
            rows = [[c.strip() for c in l.split("\t") if c.strip()] for l in lines[1:]]
        else:
            headers = [c.strip() for c in re.split(r"\s{2,}", lines[0]) if c.strip()]
            rows = [[c.strip() for c in re.split(r"\s{2,}", l) if c.strip()] for l in lines[1:]]

        if not headers or not rows:
            return None

        raw_markdown = self.format_as_markdown(headers, rows)
        summary = self.generate_table_summary(headers, rows, section)

        return TableElement(
            table_id=f"tbl_{uuid.uuid4().hex[:8]}",
            document_id=document_id,
            page_number=page_number,
            section=section,
            raw_markdown=raw_markdown,
            headers=headers,
            rows=rows,
            summary=summary,
            source=source,
        )


table_extractor = TableExtractor()

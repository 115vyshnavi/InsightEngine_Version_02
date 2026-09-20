"""Forensic PDF Parser using PyMuPDF and pypdf fallback with table awareness."""

import os
import uuid
from pathlib import Path
from typing import List, Tuple, Dict, Any
from app.models.document import TableElement
from app.core.logging import logger
from app.core.exceptions import PDFParsingError
from app.ingestion.table_extractor import table_extractor
from app.ingestion.ocr import ocr_processor


class PDFParser:
    """Extracts text and structured financial tables page-by-page from PDF files."""

    def parse_pdf(
        self, file_path: str, document_id: str, original_filename: str
    ) -> Tuple[List[Dict[str, Any]], List[TableElement]]:
        """
        Parses PDF into a list of page text records and table elements.
        Returns:
            pages: List of dicts with keys: page_number, text, section
            tables: List of TableElement objects
        """
        path = Path(file_path)
        if not path.exists():
            raise PDFParsingError(f"PDF file does not exist: {file_path}")

        try:
            return self._parse_with_pymupdf(file_path, document_id, original_filename)
        except Exception as pymupdf_err:
            logger.warning(f"PyMuPDF parsing encountered issue ({pymupdf_err}), attempting pypdf fallback.")
            try:
                return self._parse_with_pypdf(file_path, document_id, original_filename)
            except Exception as pypdf_err:
                raise PDFParsingError(
                    f"Failed to parse PDF using both PyMuPDF and pypdf: {pypdf_err}"
                ) from pypdf_err

    def _parse_with_pymupdf(
        self, file_path: str, document_id: str, original_filename: str
    ) -> Tuple[List[Dict[str, Any]], List[TableElement]]:
        """Extracts using PyMuPDF (fitz) with native table detection and block analysis."""
        import fitz  # PyMuPDF

        pages_data: List[Dict[str, Any]] = []
        all_tables: List[TableElement] = []

        doc = fitz.open(file_path)
        if doc.page_count == 0:
            raise PDFParsingError(f"PDF document is empty (0 pages): {original_filename}")

        for page_idx in range(doc.page_count):
            page_num = page_idx + 1
            page = doc.load_page(page_idx)

            # Detect current section header (look for prominent text or title)
            section = self._detect_section_header(page)

            # 1. Native PyMuPDF table extraction if supported
            page_tables: List[TableElement] = []
            try:
                tabs = page.find_tables()
                if tabs and len(tabs.tables) > 0:
                    for t_idx, tab in enumerate(tabs.tables):
                        extracted_grid = tab.extract()
                        if extracted_grid and len(extracted_grid) >= 2:
                            raw_headers = [str(c or "").strip() for c in extracted_grid[0]]
                            raw_rows = [
                                [str(c or "").strip() for c in row]
                                for row in extracted_grid[1:]
                            ]
                            raw_md = table_extractor.format_as_markdown(raw_headers, raw_rows)
                            summary = table_extractor.generate_table_summary(
                                raw_headers, raw_rows, section
                            )
                            page_tables.append(
                                TableElement(
                                    table_id=f"tbl_p{page_num}_{t_idx+1}_{uuid.uuid4().hex[:6]}",
                                    document_id=document_id,
                                    page_number=page_num,
                                    section=section,
                                    raw_markdown=raw_md,
                                    headers=raw_headers,
                                    rows=raw_rows,
                                    summary=summary,
                                    source=original_filename,
                                )
                            )
            except Exception as tab_err:
                logger.debug(f"fitz native table search on page {page_num}: {tab_err}")

            # 2. Page text extraction
            text = page.get_text("text")

            # 3. If text is sparse or empty, attempt OCR on page rendering
            if len(text.strip()) < 30 and ocr_processor.engine_available:
                try:
                    pix = page.get_pixmap(dpi=150)
                    img_bytes = pix.tobytes("png")
                    text = ocr_processor.extract_text_from_image(img_bytes)
                except Exception as ocr_err:
                    logger.warning(f"OCR fallback on page {page_num} failed: {ocr_err}")

            # 4. If native tables weren't found, try text pattern table detector
            if not page_tables:
                text_tables = table_extractor.extract_tables_from_text(
                    text, document_id, page_num, original_filename, section
                )
                page_tables.extend(text_tables)

            all_tables.extend(page_tables)
            pages_data.append(
                {
                    "page_number": page_num,
                    "text": text,
                    "section": section,
                }
            )

        doc.close()
        return pages_data, all_tables

    def _parse_with_pypdf(
        self, file_path: str, document_id: str, original_filename: str
    ) -> Tuple[List[Dict[str, Any]], List[TableElement]]:
        """Fallback extraction using standard pypdf."""
        import pypdf

        pages_data: List[Dict[str, Any]] = []
        all_tables: List[TableElement] = []

        reader = pypdf.PdfReader(file_path)
        if len(reader.pages) == 0:
            raise PDFParsingError(f"PDF document is empty: {original_filename}")

        for idx, page in enumerate(reader.pages):
            page_num = idx + 1
            text = page.extract_text() or ""
            section = "Financial Disclosures"

            page_tables = table_extractor.extract_tables_from_text(
                text, document_id, page_num, original_filename, section
            )
            all_tables.extend(page_tables)

            pages_data.append(
                {
                    "page_number": page_num,
                    "text": text,
                    "section": section,
                }
            )

        return pages_data, all_tables

    def _detect_section_header(self, fitz_page) -> str:
        """Heuristically detects current financial statement section from headings."""
        try:
            blocks = fitz_page.get_text("blocks")
            for b in blocks[:5]:
                b_text = b[4].strip()
                b_lower = b_text.lower()
                if "condensed consolidated statements" in b_lower:
                    return b_text[:80]
                if "statement of income" in b_lower or "operations" in b_lower:
                    return "Consolidated Statements of Income"
                if "balance sheet" in b_lower:
                    return "Consolidated Balance Sheets"
                if "cash flows" in b_lower:
                    return "Consolidated Statements of Cash Flows"
                if "notes to consolidated financial" in b_lower:
                    return "Notes to Financial Statements"
                if "management's discussion" in b_lower or "md&a" in b_lower:
                    return "Management's Discussion & Analysis"
        except Exception:
            pass
        return "Financial Section"


pdf_parser = PDFParser()

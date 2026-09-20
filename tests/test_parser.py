"""Unit tests for text extraction, table extraction, and chunk metadata preservation."""

from app.ingestion.table_extractor import TableExtractor
from app.ingestion.chunker import FinancialChunker


def test_table_extraction_and_markdown_formatting():
    extractor = TableExtractor()
    headers = ["Quarter", "Revenue", "Net Income"]
    rows = [
        ["Q1", "70M", "5M"],
        ["Q2", "80M", "8M"],
        ["Q3", "100M", "12M"],
    ]
    md = extractor.format_as_markdown(headers, rows)
    assert "| Quarter | Revenue | Net Income |" in md
    assert "| Q3 | 100M | 12M |" in md

    summary = extractor.generate_table_summary(headers, rows, "Consolidated Statements")
    assert "Consolidated Statements" in summary
    assert "Quarter" in summary
    assert "Revenue" in summary


def test_chunker_metadata_preservation():
    extractor = TableExtractor()
    tbl = extractor.extract_tables_from_text(
        "Quarter | Revenue\nQ1 | 70M\nQ2 | 80M\nQ3 | 100M\n",
        document_id="doc_123",
        page_number=12,
        source="earnings.pdf",
        section="Statements of Income",
    )
    assert len(tbl) == 1

    chunker = FinancialChunker()
    pages = [{"page_number": 12, "text": "Discussion of quarterly results follows below.", "section": "MD&A"}]
    chunks = chunker.process_document("doc_123", "earnings.pdf", pages, tbl)

    # Check table chunk
    table_chunk = next(c for c in chunks if c.content_type == "table")
    assert table_chunk.document_id == "doc_123"
    assert table_chunk.page_number == 12
    assert table_chunk.source == "earnings.pdf"
    assert table_chunk.raw_content is not None
    assert "Q3" in table_chunk.raw_content

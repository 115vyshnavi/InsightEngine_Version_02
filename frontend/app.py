"""InsightEngine Streamlit Financial Analysis Workbench."""

import os
import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
from app.core.config import settings
from app.retrieval.hybrid_search import hybrid_search_engine
from app.retrieval.vector_store import vector_store
from app.retrieval.parent_store import parent_store
from app.retrieval.bm25 import bm25_index
from app.ingestion.pdf_parser import pdf_parser
from app.ingestion.chunker import financial_chunker
from app.llm.answer_generator import answer_generator
from app.evaluation.dataset import EVALUATION_DATASET

st.set_page_config(
    page_title="InsightEngine | Forensic Financial AI",
    page_icon="📊",
    layout="wide",
)

st.title("📊 InsightEngine: Financial Report Analysis System")
st.caption("Forensic Accountant & Financial Analyst AI | Zero-Hallucination RAG & Deterministic Arithmetic")

# Sidebar
st.sidebar.header("📁 Document Ingestion")
uploaded_file = st.sidebar.file_uploader("Upload Earnings Report (PDF)", type=["pdf"])

if uploaded_file is not None:
    save_path = settings.UPLOAD_DIR / uploaded_file.name
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    with st.sidebar.status("Processing and indexing document..."):
        pages_data, tables = pdf_parser.parse_pdf(str(save_path), "doc_uploaded", uploaded_file.name)
        for p in pages_data:
            parent_store.register_parent(f"parent_{p['page_number']}_doc_uploaded", p["text"])
        chunks = financial_chunker.process_document("doc_uploaded", uploaded_file.name, pages_data, tables)
        vector_store.add_chunks(chunks)
        bm25_index.build_index(list(vector_store.chunks.values()))
    st.sidebar.success(f"Indexed {len(pages_data)} pages, {len(tables)} tables, {len(chunks)} chunks.")

# Pre-load sample report button
if st.sidebar.button("Load Acme Corp Q3 2024 Sample 10-Q"):
    sample_pdf = settings.UPLOAD_DIR / "acme_corp_q3_earnings.pdf"
    if sample_pdf.exists():
        pages_data, tables = pdf_parser.parse_pdf(str(sample_pdf), "acme_sample", sample_pdf.name)
        for p in pages_data:
            parent_store.register_parent(f"parent_{p['page_number']}_acme", p["text"])
        chunks = financial_chunker.process_document("acme_sample", sample_pdf.name, pages_data, tables)
        vector_store.add_chunks(chunks)
        bm25_index.build_index(list(vector_store.chunks.values()))
        st.sidebar.success("Sample 10-Q Report loaded into index!")

st.sidebar.markdown("---")
st.sidebar.subheader("System Status")
st.sidebar.metric("Indexed Chunks", len(vector_store.chunks))
st.sidebar.write(f"**LLM Provider:** `{settings.LLM_PROVIDER}`")
st.sidebar.write(f"**Embedding:** `{settings.EMBEDDING_MODEL}`")
st.sidebar.write(f"**Reranker:** FlashRank (TinyBERT)")

# Main Query Interface
st.subheader("🔎 Ask Financial Question")

example_queries = [
    "What was the revenue in Q3?",
    "What was the percentage growth in net income from Q2 to Q3?",
    "What was the net profit margin in Q3?",
    "What was the percentage decrease in debt from Q2 to Q3?",
    "Compare Q2 and Q3 revenue.",
    "What was the company's research and development budget in fiscal year 2018?",
]

selected_example = st.selectbox("Or choose a benchmark test question:", ["(Custom Query)"] + example_queries)

query_input = st.text_input(
    "Financial Query:",
    value="" if selected_example == "(Custom Query)" else selected_example,
    placeholder="e.g. What was the percentage growth in net income from Q2 to Q3?",
)

if st.button("Analyze Financial Report", type="primary"):
    if not query_input.strip():
        st.warning("Please enter a financial question.")
    elif len(vector_store.chunks) == 0:
        st.error("No document indexed yet. Please upload a PDF or load the sample report from the sidebar.")
    else:
        with st.spinner("Executing hybrid search, FlashRank reranking, and deterministic calculation..."):
            evidence = hybrid_search_engine.search(query_input, top_k_candidates=15, top_k_final=4)
            response = answer_generator.generate_answer(query_input, evidence)

        # 1. Direct Answer
        st.markdown("### 📋 Forensic Analysis")
        st.markdown(response.answer)

        # 2. Deterministic Calculation Breakdown
        if response.calculation:
            st.markdown("### 🧮 Verified Arithmetic Breakdown")
            col1, col2, col3 = st.columns(3)
            col1.metric("Result", response.calculation.formatted_result or response.calculation.result)
            col2.write(f"**Formula:** `{response.calculation.formula}`")
            col3.write(f"**Inputs:** `{response.calculation.inputs}`")
            if response.calculation.steps:
                st.info(f"**Step-by-step substitution:** {response.calculation.steps}")

        # 3. Source Citations
        if response.sources:
            st.markdown("### 📑 Evidence Citations")
            for src in response.sources:
                with st.expander(f"📌 {src.citation_text} [{src.content_type.upper()}]"):
                    st.write(f"**Document:** `{src.document_name}` | **Page:** `{src.page_number}` | **Section:** `{src.section}`")
                    st.code(src.snippet, language="markdown")

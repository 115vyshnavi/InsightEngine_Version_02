# InsightEngine: Production-Grade Financial Report Analysis System

InsightEngine is an AI-powered financial RAG system designed for forensic accountants, equity research analysts, and finance teams. It extracts text and tabular structures from corporate earnings reports (PDFs), indexes them with table-aware multi-vector representations, performs hybrid retrieval with FlashRank cross-attention reranking, and produces mathematically verified answers with strict source citations.

---

## Core Principle

> **NEVER invent financial information.**
> The AI answers ONLY from verified context retrieved from the document.
> If the required information is not present, the system strictly responds:
> *"I cannot answer this based on the provided document."*

---

## Architectural Highlights

1. **Table-Aware Multi-Vector Ingestion**:
   - Preserves complete table geometries as markdown structures.
   - Generates summary representations for semantic dense retrieval.
   - Retains original raw grid tables for LLM answering.
   - Retains exact page numbers, statement sections, and parent IDs.

2. **Hybrid Retrieval Pipeline**:
   ```
   User Query
       ↓
   Dense Semantic Search (bge-large-en-v1.5) + BM25 Keyword Search
       ↓
   Reciprocal Rank Fusion (RRF) -> Top 15 Candidates
       ↓
   FlashRank Cross-Encoder Reranker -> Top 3–4 Evidence Items
       ↓
   Parent Document Resolution -> Exact Table / Section Restored
       ↓
   Deterministic Arithmetic Engine -> LLM Forensic Synthesis
   ```

3. **Deterministic Financial Calculation Engine**:
   - Python-powered arithmetic for percentage growth, percentage decrease, margin, ratio, difference, and CAGR.
   - Zero division prevention and exact raw value auditing.
   - Step-by-step mathematical substitution displayed to the user.

4. **Forensic Source Citations**:
   - Citations identify the document name, page number, section, and snippet.

---

## Tech Stack

- **Backend**: Python 3.10+, FastAPI, Uvicorn, Pydantic v2
- **PDF Ingestion**: PyMuPDF (`fitz`), pypdf, TableExtractor
- **Retrieval**: Dense Vector Store + BM25Okapi + FlashRank Reranker
- **LLM Providers**: Google Gemini, Groq, OpenAI (configurable via `.env`)
- **Containerization**: Docker & Docker Compose (with Qdrant support)
- **Testing**: pytest

---

## Quick Start

### 1. Environment Configuration

Copy `.env.example` to `.env` and set your preferred LLM provider:

```bash
cp .env.example .env
```

Example `.env`:
```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here
TOP_K_RETRIEVAL=15
TOP_K_RERANKED=4
```

### 2. Run with Python

```bash
pip install -r requirements.txt
python run.py
```
FastAPI Swagger documentation will be accessible at: `http://localhost:8000/docs`

### 3. Run with Docker Compose

```bash
docker-compose -f docker/docker-compose.yml up --build
```

---

## API Reference

### `POST /upload`
Uploads a financial report PDF, extracts text and tables, and indexes chunks.
```bash
curl -X POST "http://localhost:8000/upload" -F "file=@sample_report.pdf"
```

### `POST /query`
Queries the indexed document:
```json
{
  "question": "What was the percentage growth in net income from Q2 to Q3?"
}
```

Response schema:
```json
{
  "answer": "Net income increased by 50.00% from Q2 to Q3.",
  "data_points": [
    {"metric": "Q2 Net Income", "value": "$8M"},
    {"metric": "Q3 Net Income", "value": "$12M"}
  ],
  "calculation": {
    "formula": "((new_value - old_value) / old_value) * 100",
    "inputs": {"old_value": 8.0, "new_value": 12.0},
    "steps": "((12.0 - 8.0) / 8.0) * 100 = 50.0000%",
    "result": 50.0,
    "formatted_result": "+50.00%"
  },
  "sources": [
    {
      "document_name": "sample_report.pdf",
      "page_number": 12,
      "section": "Consolidated Statements of Income",
      "citation_text": "Consolidated Statements of Income, Page 12 (sample_report.pdf)"
    }
  ]
}
```

### `GET /documents`
Returns all indexed financial reports.

### `DELETE /documents/{document_id}`
Deletes document chunks from vector and BM25 indices.

### `GET /health`
Returns system health, indexed chunk counts, and active providers.

---

## Running Evaluation and Tests

### Unit Tests
```bash
pytest tests/ -v
```

### Ragas Benchmark Evaluation
```bash
python app/evaluation/evaluate.py
```
Results will be saved to `data/evaluation/results.json`.

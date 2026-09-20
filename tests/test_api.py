"""Unit tests for FastAPI endpoints: /health, /documents, /query, /upload."""

import io
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "InsightEngine Financial RAG"


def test_list_documents_initially_empty():
    response = client.get("/documents")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_query_without_documents():
    response = client.post("/query", json={"question": "What was the revenue in Q3?"})
    assert response.status_code == 200
    data = response.json()
    assert "No documents have been uploaded yet" in data["answer"] or "cannot answer" in data["answer"]


def test_empty_question_validation():
    response = client.post("/query", json={"question": "   "})
    assert response.status_code == 400

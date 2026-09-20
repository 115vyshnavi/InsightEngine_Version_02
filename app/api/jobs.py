"""Real-time job orchestration for uploads and financial queries."""

from __future__ import annotations

import asyncio
import io
import json
import threading
import uuid
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Dict, Literal, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.api.query import query_financial_report
from app.api.upload import DOCUMENT_REGISTRY, _ingest_document
from app.core.config import settings
from app.core.logging import logger
from app.models.query import QueryRequest

router = APIRouter(tags=["Realtime Jobs"])

JobType = Literal["upload", "query"]
JobStatus = Literal["queued", "running", "succeeded", "failed"]
JOB_STORE: Dict[str, Dict[str, Any]] = {}
JOB_LOCK = threading.Lock()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _job_snapshot(job: Dict[str, Any]) -> Dict[str, Any]:
    snapshot = dict(job)
    result = snapshot.get("result")
    if hasattr(result, "model_dump"):
        snapshot["result"] = result.model_dump()
    return snapshot


def _update_job(job_id: str, **changes: Any) -> Dict[str, Any]:
    with JOB_LOCK:
        job = JOB_STORE.setdefault(job_id, {
            "id": job_id,
            "type": "query",
            "status": "queued",
            "progress": 0,
            "message": "Queued",
            "created_at": _utc_now(),
            "updated_at": _utc_now(),
            "result": None,
            "error": None,
        })
        job.update(changes)
        job["updated_at"] = _utc_now()
        return _job_snapshot(job)


async def _process_upload_job(job_id: str, original_name: str, file_bytes: bytes, company_name: str = "Unknown Company") -> None:
    try:
        _update_job(job_id, status="running", progress=10, message=f"Saving uploaded file: {original_name}")
        file_obj = UploadFile(file=io.BytesIO(file_bytes), filename=original_name)
        doc = await _ingest_document(
            file_obj,
            company_name=company_name,
            progress_callback=lambda progress, message: _update_job(
                job_id,
                progress=progress,
                message=message,
            ),
        )
        _update_job(
            job_id,
            status="succeeded",
            progress=100,
            message="Upload completed and indexed successfully.",
            result=doc.model_dump(),
        )
    except Exception as exc:  # pragma: no cover - exercised by runtime worker
        logger.exception("Job upload failed")
        _update_job(job_id, status="failed", progress=100, message="Upload failed.", error=str(exc))


async def _process_query_job(job_id: str, payload: Dict[str, Any]) -> None:
    try:
        _update_job(job_id, status="running", progress=20, message="Searching relevant document evidence...")
        req = QueryRequest(**payload)
        response = query_financial_report(req)
        _update_job(
            job_id,
            status="succeeded",
            progress=100,
            message="Answer generated successfully.",
            result=response.model_dump() if hasattr(response, "model_dump") else response,
        )
    except Exception as exc:  # pragma: no cover - exercised by runtime worker
        logger.exception("Job query failed")
        _update_job(job_id, status="failed", progress=100, message="Query failed.", error=str(exc))


@router.get("/jobs")
def list_jobs() -> Dict[str, Any]:
    with JOB_LOCK:
        jobs = [_job_snapshot(job) for job in JOB_STORE.values()]
    return {"jobs": jobs}


@router.get("/jobs/{job_id}")
def get_job(job_id: str) -> Dict[str, Any]:
    with JOB_LOCK:
        job = JOB_STORE.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return _job_snapshot(job)


@router.get("/jobs/{job_id}/events")
async def stream_job_events(job_id: str) -> StreamingResponse:
    async def event_stream() -> AsyncIterator[str]:
        while True:
            with JOB_LOCK:
                job = JOB_STORE.get(job_id)
            if job is None:
                yield "event: error\ndata: {\"detail\": \"Job not found\"}\n\n"
                break
            payload = json.dumps(_job_snapshot(job))
            yield f"data: {payload}\n\n"
            if job["status"] in {"succeeded", "failed"}:
                break
            await asyncio.sleep(0.6)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/jobs/upload")
async def create_upload_job(
    file: UploadFile = File(...),
    company_name: str = Form(default="Unknown Company"),
) -> Dict[str, Any]:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF uploads are supported.")

    file_bytes = await file.read()
    company_label = (company_name or "Unknown Company").strip() or "Unknown Company"
    job_id = uuid.uuid4().hex
    _update_job(job_id, type="upload", status="queued", progress=0, message="Queued for PDF ingestion.")
    thread = threading.Thread(
        target=lambda: asyncio.run(_process_upload_job(job_id, file.filename, file_bytes, company_label)),
        daemon=True,
    )
    thread.start()
    return _job_snapshot(JOB_STORE[job_id])


@router.post("/jobs/query")
async def create_query_job(request: QueryRequest) -> Dict[str, Any]:
    job_id = uuid.uuid4().hex
    payload = request.model_dump()
    _update_job(job_id, type="query", status="queued", progress=0, message="Queued for analysis.")
    thread = threading.Thread(
        target=lambda: asyncio.run(_process_query_job(job_id, payload)),
        daemon=True,
    )
    thread.start()
    return _job_snapshot(JOB_STORE[job_id])


@router.get("/jobs/health")
def jobs_health() -> Dict[str, Any]:
    with JOB_LOCK:
        running = sum(1 for job in JOB_STORE.values() if job["status"] == "running")
        queued = sum(1 for job in JOB_STORE.values() if job["status"] == "queued")
    return {
        "status": "healthy",
        "jobs_total": len(JOB_STORE),
        "jobs_running": running,
        "jobs_queued": queued,
        "storage": settings.VECTOR_DB,
        "documents_indexed": len(DOCUMENT_REGISTRY),
    }

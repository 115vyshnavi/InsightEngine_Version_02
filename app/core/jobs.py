"""Small in-process job coordinator used by the HTTP streaming endpoints."""

from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4


class JobManager:
    """Runs blocking ingestion and query work outside the FastAPI event loop."""

    def __init__(self, max_workers: int = 4) -> None:
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="insight-job")
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()

    def submit(self, task: Callable[..., Any], *args: Any, **kwargs: Any) -> str:
        job_id = uuid4().hex
        now = self._now()
        with self._lock:
            self._jobs[job_id] = {
                "job_id": job_id,
                "status": "queued",
                "progress": 0,
                "message": "Job queued",
                "created_at": now,
                "updated_at": now,
                "result": None,
                "error": None,
                "events": [{"event": "queued", "progress": 0, "message": "Job queued"}],
            }
        future = self._executor.submit(self._run, job_id, task, *args, **kwargs)
        with self._lock:
            self._jobs[job_id]["future"] = future
        return job_id

    def _run(self, job_id: str, task: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        self.update(job_id, "running", 5, "Job started")
        try:
            result = task(job_id, *args, **kwargs)
            with self._lock:
                self._jobs[job_id]["result"] = result
            self.update(job_id, "succeeded", 100, "Job completed")
        except Exception as exc:
            with self._lock:
                self._jobs[job_id]["error"] = str(exc)
            self.update(job_id, "failed", 100, str(exc))

    def update(self, job_id: str, status: str, progress: int, message: str) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return
            job["status"] = status
            job["progress"] = max(0, min(progress, 100))
            job["message"] = message
            job["updated_at"] = self._now()
            job["events"].append({"event": status, "progress": job["progress"], "message": message})

    def get(self, job_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None
            return {key: value for key, value in job.items() if key not in {"future", "events"}}

    def events_after(self, job_id: str, index: int) -> tuple[List[Dict[str, Any]], int]:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return [], index
            events = job["events"][index:]
            return events, len(job["events"])

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()


job_manager = JobManager()

"""Thread-safe job registry for background scan tasks."""
from __future__ import annotations

import queue
import uuid
from typing import Optional


_jobs: dict[str, dict] = {}


def create_job() -> str:
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {"q": queue.SimpleQueue(), "done": False}
    return job_id


def get_queue(job_id: str) -> Optional[queue.SimpleQueue]:
    job = _jobs.get(job_id)
    return job["q"] if job else None


def mark_done(job_id: str) -> None:
    if job_id in _jobs:
        _jobs[job_id]["done"] = True
        _jobs[job_id]["q"].put({"type": "done"})


def is_done(job_id: str) -> bool:
    job = _jobs.get(job_id)
    return job["done"] if job else True

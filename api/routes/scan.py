"""Scan and submit background task routes with SSE streaming."""
from __future__ import annotations

import asyncio
import json
import os
import queue
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from api.auth import get_session
from api.jobs import create_job, get_queue, mark_done
from privguard.db import DB_PATH
from privguard.scanner import scan_user
from privguard.submitter import submit_removals

router = APIRouter()

_executor = ThreadPoolExecutor(max_workers=4)


def _db_path() -> Path:
    env = os.environ.get("PRIVGUARD_DB_PATH")
    return Path(env) if env else DB_PATH


def _find_profile(vault: dict, name: str) -> dict:
    for user in vault.get("users", []):
        if user["display_name"] == name:
            return user
    raise HTTPException(status_code=404, detail=f"User '{name}' not found.")


class ScanRequest(BaseModel):
    source: Optional[str] = None
    force: bool = False


def _run_scan_in_background(job_id: str, profile: dict, api_keys: dict,
                             source: Optional[str], force: bool, db_path: Path) -> None:
    q = get_queue(job_id)
    try:
        scan_user(profile, api_keys=api_keys, source=source,
                  force=force, db_path=db_path,
                  progress_cb=lambda e: q.put(e) if q else None)
    finally:
        mark_done(job_id)


def _run_submit_in_background(job_id: str, profile: dict, force: bool, db_path: Path) -> None:
    q = get_queue(job_id)
    try:
        submit_removals(profile, force=force, db_path=db_path)
    finally:
        mark_done(job_id)


@router.post("/api/users/{name}/scan", status_code=202)
def start_scan(name: str, body: ScanRequest = ScanRequest(),
               session_data: dict = Depends(get_session)):
    profile = _find_profile(session_data["vault"], name)
    api_keys = session_data["vault"].get("api_keys", {})
    db_path = _db_path()
    job_id = create_job()
    _executor.submit(_run_scan_in_background, job_id, profile, api_keys,
                     body.source, body.force, db_path)
    return {"job_id": job_id}


@router.post("/api/users/{name}/submit", status_code=202)
def start_submit(name: str, body: ScanRequest = ScanRequest(),
                 session_data: dict = Depends(get_session)):
    profile = _find_profile(session_data["vault"], name)
    db_path = _db_path()
    job_id = create_job()
    _executor.submit(_run_submit_in_background, job_id, profile, body.force, db_path)
    return {"job_id": job_id}


@router.get("/api/jobs/{job_id}/stream")
async def stream_job(job_id: str, session_data: dict = Depends(get_session)):
    q = get_queue(job_id)
    if q is None:
        raise HTTPException(status_code=404, detail="Job not found.")

    async def event_generator():
        while True:
            try:
                event = q.get_nowait()
                yield f"data: {json.dumps(event)}\n\n"
                if event.get("type") == "done":
                    break
            except queue.Empty:
                yield ": keepalive\n\n"
                await asyncio.sleep(0.2)

    return StreamingResponse(event_generator(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache",
                                      "X-Accel-Buffering": "no"})

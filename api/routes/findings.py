"""Findings and breaches read routes, plus status PATCH."""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, field_validator

from api.auth import get_session
from privguard.db import DB_PATH, get_breaches, get_findings, update_finding_status

router = APIRouter()

_VALID_STATUSES = {
    "found", "not_found", "submitted", "pending_verification",
    "manual_required", "cleared",
}


def _db_path() -> Path:
    env = os.environ.get("PRIVGUARD_DB_PATH")
    return Path(env) if env else DB_PATH


@router.get("/api/users/{name}/findings")
def list_findings(name: str, session_data: dict = Depends(get_session)):
    return get_findings(user_display_name=name, db_path=_db_path())


@router.get("/api/users/{name}/breaches")
def list_breaches(name: str, request: Request, session_data: dict = Depends(get_session)):
    breaches = get_breaches(user_display_name=name, db_path=_db_path())
    catalogue: dict = getattr(request.app.state, "breach_catalogue", {})
    result = []
    for b in breaches:
        entry = dict(b)
        entry["catalogue"] = catalogue.get(b["breach_name"])
        result.append(entry)
    return result


class StatusUpdate(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in _VALID_STATUSES:
            raise ValueError(f"status must be one of {sorted(_VALID_STATUSES)}")
        return v


@router.patch("/api/findings/{finding_id}/status")
def patch_status(finding_id: int, body: StatusUpdate,
                 session_data: dict = Depends(get_session)):
    update_finding_status(finding_id, body.status, db_path=_db_path())
    return {"status": "updated", "finding_id": finding_id, "new_status": body.status}

"""Findings and breaches read routes, plus status PATCH."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, field_validator

from api.auth import get_session
from privguard.db import DB_PATH, get_breaches, get_findings, update_finding_status, update_listing_url
from privguard.scanner import BROKERS_PATH

router = APIRouter()

_VALID_STATUSES = {
    "found", "not_found", "submitted", "pending_verification",
    "manual_required", "cleared",
}

_brokers_cache: dict[str, dict] | None = None


def _brokers_by_id() -> dict[str, dict]:
    global _brokers_cache
    if _brokers_cache is None:
        try:
            data = json.loads(BROKERS_PATH.read_text(encoding="utf-8"))
            _brokers_cache = {b["id"]: b for b in data}
        except Exception:
            _brokers_cache = {}
    return _brokers_cache


def _interpolate(template: str, profile: dict) -> str:
    full_name = profile.get("full_name") or profile.get("display_name", "")
    parts = full_name.strip().split()
    first = parts[0] if parts else ""
    last = parts[-1] if len(parts) > 1 else ""
    name_slug = re.sub(r"\s+", "-", full_name.lower())
    city = state = zip_code = ""
    for addr in profile.get("addresses", []):
        if addr.get("current", False) or not city:
            city = addr.get("city", "")
            state = addr.get("state", "")
            zip_code = addr.get("zip", "")
    primary_email = (profile.get("emails") or [""])[0]
    return (
        template
        .replace("{first_name}", first)
        .replace("{last_name}", last)
        .replace("{full_name}", full_name)
        .replace("{name_slug}", name_slug)
        .replace("{city}", city)
        .replace("{state}", state)
        .replace("{zip}", zip_code)
        .replace("{primary_email}", primary_email)
    )


def _db_path() -> Path:
    env = os.environ.get("PRIVGUARD_DB_PATH")
    return Path(env) if env else DB_PATH


@router.get("/api/users/{name}/findings")
def list_findings(name: str, session_data: dict = Depends(get_session)):
    findings = get_findings(user_display_name=name, db_path=_db_path())

    profile = next(
        (u for u in session_data["vault"].get("users", []) if u["display_name"] == name),
        None,
    )

    if profile:
        brokers = _brokers_by_id()
        db_path = _db_path()
        for f in findings:
            if f.get("listing_url"):
                continue
            broker = brokers.get(f["site_id"])
            if not broker:
                continue
            tpl = broker.get("search_url")
            if not tpl:
                continue
            url = _interpolate(tpl, profile)
            f["listing_url"] = url
            update_listing_url(f["id"], url, db_path=db_path)

    return findings


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

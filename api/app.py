"""PrivGuard FastAPI application."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from fastapi import Cookie, Depends, FastAPI, HTTPException, Response
from pydantic import BaseModel

from api.auth import create_session, destroy_session, get_session
from privguard.vault import VAULT_PATH, load_vault

app = FastAPI(title="PrivGuard API")


def _vault_path() -> Path:
    env = os.environ.get("PRIVGUARD_VAULT_PATH")
    return Path(env) if env else VAULT_PATH


class UnlockRequest(BaseModel):
    password: str


@app.post("/api/auth/unlock")
def unlock(body: UnlockRequest, response: Response):
    if not body.password:
        raise HTTPException(status_code=401, detail="Password must not be empty.")
    try:
        vault = load_vault(body.password, vault_path=_vault_path())
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    token = create_session(vault, body.password)
    response.set_cookie("session", token, httponly=True, samesite="strict")
    return {"status": "unlocked"}


@app.post("/api/auth/lock")
def lock(response: Response, session: Optional[str] = Cookie(default=None)):
    if session:
        destroy_session(session)
    response.delete_cookie("session")
    return {"status": "locked"}


@app.get("/api/users")
def list_users_stub(session_data: dict = Depends(get_session)):
    return session_data["vault"].get("users", [])

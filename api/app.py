"""PrivGuard FastAPI application — full assembly."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import requests as http_requests
from fastapi import Cookie, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from api.auth import create_session, destroy_session
from api.routes.findings import router as findings_router
from api.routes.scan import router as scan_router
from api.routes.users import router as users_router
from privguard.vault import VAULT_PATH, load_vault

app = FastAPI(title="PrivGuard API", docs_url="/api/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users_router)
app.include_router(scan_router)
app.include_router(findings_router)


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


@app.on_event("startup")
async def _load_breach_catalogue() -> None:
    try:
        resp = http_requests.get(
            "https://haveibeenpwned.com/api/v3/breaches",
            timeout=10,
            headers={"user-agent": "PrivGuard/2.0"},
        )
        if resp.status_code == 200:
            app.state.breach_catalogue = {b["Name"]: b for b in resp.json()}
        else:
            app.state.breach_catalogue = {}
    except Exception:
        app.state.breach_catalogue = {}


_STATIC_DIR = Path(__file__).parent.parent / "web" / "out"
if _STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(_STATIC_DIR), html=True), name="static")

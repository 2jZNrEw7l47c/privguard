"""In-memory session store for PrivGuard API."""
from __future__ import annotations

import secrets
from typing import Optional

from fastapi import Cookie, HTTPException


_sessions: dict[str, dict] = {}


def create_session(vault: dict, password: str) -> str:
    token = secrets.token_urlsafe(32)
    _sessions[token] = {"vault": vault, "password": password}
    return token


def get_session(session: Optional[str] = Cookie(default=None)) -> dict:
    if session is None or session not in _sessions:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    return _sessions[session]


def destroy_session(token: str) -> None:
    _sessions.pop(token, None)

"""User profile CRUD routes."""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.auth import get_session
from privguard.vault import VAULT_PATH, save_vault

router = APIRouter(prefix="/api/users")


def _vault_path() -> Path:
    env = os.environ.get("PRIVGUARD_VAULT_PATH")
    return Path(env) if env else VAULT_PATH


class ProfileIn(BaseModel):
    display_name: str
    full_name: str
    date_of_birth: str = ""
    emails: list[str] = []
    phone_numbers: list[str] = []
    addresses: list[dict] = []
    aliases: list[str] = []
    ssn_last4: str = ""


@router.get("")
def list_users(session_data: dict = Depends(get_session)):
    return session_data["vault"].get("users", [])


@router.post("", status_code=201)
def add_user(profile: ProfileIn, session_data: dict = Depends(get_session)):
    vault = session_data["vault"]
    password = session_data["password"]
    users = vault.setdefault("users", [])
    users.append(profile.model_dump())
    save_vault(password, vault, vault_path=_vault_path())
    return profile.model_dump()


@router.delete("/{name}")
def remove_user(name: str, session_data: dict = Depends(get_session)):
    vault = session_data["vault"]
    password = session_data["password"]
    users = vault.get("users", [])
    updated = [u for u in users if u["display_name"] != name]
    if len(updated) == len(users):
        raise HTTPException(status_code=404, detail=f"User '{name}' not found.")
    vault["users"] = updated
    save_vault(password, vault, vault_path=_vault_path())
    return {"status": "removed", "display_name": name}

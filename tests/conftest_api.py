"""Shared fixtures for FastAPI endpoint tests."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from privguard.vault import save_vault


MASTER_PASSWORD = "test-master-password"

VAULT_DATA = {
    "users": [
        {
            "display_name": "Alice Test",
            "full_name": "Alice Test",
            "aliases": [],
            "date_of_birth": "1990-01-01",
            "emails": ["alice@example.com"],
            "phone_numbers": ["555-0100"],
            "addresses": [{"street": "1 Main St", "city": "Portland",
                           "state": "OR", "zip": "97201", "current": True}],
            "ssn_last4": "",
        }
    ],
    "api_keys": {"hibp": ""},
}


@pytest.fixture()
def tmp_vault(tmp_path):
    vault_path = tmp_path / "vault.enc"
    save_vault(MASTER_PASSWORD, VAULT_DATA, vault_path=vault_path)
    return vault_path


@pytest.fixture()
def tmp_db(tmp_path):
    from privguard.db import init_db
    db_path = tmp_path / "test.db"
    init_db(db_path=db_path)
    return db_path


@pytest.fixture()
def client(tmp_vault, tmp_db, monkeypatch):
    monkeypatch.setenv("PRIVGUARD_VAULT_PATH", str(tmp_vault))
    monkeypatch.setenv("PRIVGUARD_DB_PATH", str(tmp_db))
    from api.app import app
    return TestClient(app, raise_server_exceptions=True)


@pytest.fixture()
def auth_client(client):
    resp = client.post("/api/auth/unlock", json={"password": MASTER_PASSWORD})
    assert resp.status_code == 200
    return client

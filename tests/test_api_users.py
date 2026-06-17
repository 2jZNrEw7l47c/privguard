"""Tests for GET/POST/DELETE /api/users."""
from __future__ import annotations

import urllib.parse


def test_list_users_returns_profiles(auth_client):
    resp = auth_client.get("/api/users")
    assert resp.status_code == 200
    users = resp.json()
    assert isinstance(users, list)
    assert any(u["display_name"] == "Alice Test" for u in users)


def test_list_users_unauthenticated_returns_401(client):
    resp = client.get("/api/users")
    assert resp.status_code == 401


def test_add_user_returns_201(auth_client):
    new_user = {
        "display_name": "Bob Test",
        "full_name": "Bob Test",
        "date_of_birth": "1985-06-15",
        "emails": ["bob@example.com"],
        "phone_numbers": [],
        "addresses": [],
        "aliases": [],
        "ssn_last4": "",
    }
    resp = auth_client.post("/api/users", json=new_user)
    assert resp.status_code == 201
    assert resp.json()["display_name"] == "Bob Test"


def test_add_user_persists_in_list(auth_client):
    new_user = {
        "display_name": "Carol Test",
        "full_name": "Carol Test",
        "date_of_birth": "",
        "emails": ["carol@example.com"],
        "phone_numbers": [],
        "addresses": [],
        "aliases": [],
        "ssn_last4": "",
    }
    auth_client.post("/api/users", json=new_user)
    resp = auth_client.get("/api/users")
    names = [u["display_name"] for u in resp.json()]
    assert "Carol Test" in names


def test_delete_user_removes_from_list(auth_client):
    name = urllib.parse.quote("Alice Test")
    resp = auth_client.delete(f"/api/users/{name}")
    assert resp.status_code == 200
    resp2 = auth_client.get("/api/users")
    names = [u["display_name"] for u in resp2.json()]
    assert "Alice Test" not in names


def test_delete_nonexistent_user_returns_404(auth_client):
    resp = auth_client.delete("/api/users/Nobody%20Here")
    assert resp.status_code == 404

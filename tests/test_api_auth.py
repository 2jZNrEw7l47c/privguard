"""Tests for POST /api/auth/unlock and POST /api/auth/lock."""
from __future__ import annotations


def test_unlock_valid_password_returns_200(client):
    resp = client.post("/api/auth/unlock", json={"password": "test-master-password"})
    assert resp.status_code == 200


def test_unlock_sets_session_cookie(client):
    resp = client.post("/api/auth/unlock", json={"password": "test-master-password"})
    assert "session" in resp.cookies


def test_unlock_wrong_password_returns_401(client):
    resp = client.post("/api/auth/unlock", json={"password": "wrong-password"})
    assert resp.status_code == 401


def test_unlock_empty_password_returns_401(client):
    resp = client.post("/api/auth/unlock", json={"password": ""})
    assert resp.status_code == 401


def test_lock_clears_session(auth_client):
    resp = auth_client.post("/api/auth/lock")
    assert resp.status_code == 200
    resp2 = auth_client.get("/api/users")
    assert resp2.status_code == 401


def test_protected_route_without_cookie_returns_401(client):
    resp = client.get("/api/users")
    assert resp.status_code == 401

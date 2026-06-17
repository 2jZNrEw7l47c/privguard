"""Tests for findings and breaches endpoints."""
from __future__ import annotations

import json


def _seed_finding(db_path, display_name="Alice Test"):
    from privguard.db import upsert_finding
    upsert_finding(
        user_display_name=display_name,
        source="brokers",
        site_id="test_broker",
        site_name="Test Broker",
        status="found",
        opt_out_url="https://example.com",
        db_path=db_path,
    )


def _seed_breach(db_path, display_name="Alice Test"):
    from privguard.db import upsert_breach
    upsert_breach(
        user_display_name=display_name,
        email="alice@example.com",
        breach_name="TestBreach",
        breach_date="2023-01-01",
        exposed_fields=json.dumps(["Email", "Password"]),
        hibp_url="https://haveibeenpwned.com/account/alice@example.com",
        db_path=db_path,
    )


def test_get_findings_returns_list(auth_client, tmp_db):
    _seed_finding(tmp_db)
    resp = auth_client.get("/api/users/Alice%20Test/findings")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    assert any(f["site_name"] == "Test Broker" for f in resp.json())


def test_get_findings_unauthenticated_returns_401(client):
    resp = client.get("/api/users/Alice%20Test/findings")
    assert resp.status_code == 401


def test_get_findings_unknown_user_returns_empty_list(auth_client):
    resp = auth_client.get("/api/users/Nobody/findings")
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_breaches_returns_list(auth_client, tmp_db):
    _seed_breach(tmp_db)
    resp = auth_client.get("/api/users/Alice%20Test/breaches")
    assert resp.status_code == 200
    breaches = resp.json()
    assert any(b["breach_name"] == "TestBreach" for b in breaches)


def test_patch_finding_status(auth_client, tmp_db):
    _seed_finding(tmp_db)
    findings_resp = auth_client.get("/api/users/Alice%20Test/findings")
    finding_id = findings_resp.json()[0]["id"]
    resp = auth_client.patch(f"/api/findings/{finding_id}/status",
                             json={"status": "cleared"})
    assert resp.status_code == 200
    findings_resp2 = auth_client.get("/api/users/Alice%20Test/findings")
    updated = next(f for f in findings_resp2.json() if f["id"] == finding_id)
    assert updated["status"] == "cleared"


def test_patch_finding_invalid_status_returns_422(auth_client, tmp_db):
    _seed_finding(tmp_db)
    findings_resp = auth_client.get("/api/users/Alice%20Test/findings")
    finding_id = findings_resp.json()[0]["id"]
    resp = auth_client.patch(f"/api/findings/{finding_id}/status",
                             json={"status": "invalid_status"})
    assert resp.status_code == 422

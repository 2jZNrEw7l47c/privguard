"""Tests for POST /api/users/{name}/scan, POST /api/users/{name}/submit,
and GET /api/jobs/{job_id}/stream."""
from __future__ import annotations

from unittest.mock import patch


def test_start_scan_returns_job_id(auth_client):
    with patch("api.routes.scan._run_scan_in_background"):
        resp = auth_client.post("/api/users/Alice%20Test/scan")
    assert resp.status_code == 202
    assert "job_id" in resp.json()


def test_start_scan_unknown_user_returns_404(auth_client):
    resp = auth_client.post("/api/users/Nobody/scan")
    assert resp.status_code == 404


def test_start_scan_with_source_param(auth_client):
    with patch("api.routes.scan._run_scan_in_background"):
        resp = auth_client.post("/api/users/Alice%20Test/scan",
                                json={"source": "brokers"})
    assert resp.status_code == 202


def test_start_submit_returns_job_id(auth_client):
    with patch("api.routes.scan._run_submit_in_background"):
        resp = auth_client.post("/api/users/Alice%20Test/submit")
    assert resp.status_code == 202
    assert "job_id" in resp.json()


def test_sse_stream_unknown_job_returns_404(auth_client):
    resp = auth_client.get("/api/jobs/nonexistent-job-id/stream")
    assert resp.status_code == 404

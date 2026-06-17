"""Tests for scanner.py v2 additions: new social sites, ad_networks source, progress_cb."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from privguard.scanner import _SOCIAL_SITES, _scan_ad_networks, scan_user


def _make_profile():
    return {
        "display_name": "Test User",
        "full_name": "Test User",
        "emails": ["test@example.com"],
        "phone_numbers": [],
        "addresses": [],
    }


# --- Social platforms ---

def test_social_sites_includes_instagram():
    ids = [s["id"] for s in _SOCIAL_SITES]
    assert "instagram" in ids


def test_social_sites_includes_tiktok():
    ids = [s["id"] for s in _SOCIAL_SITES]
    assert "tiktok" in ids


def test_social_sites_includes_reddit():
    ids = [s["id"] for s in _SOCIAL_SITES]
    assert "reddit" in ids


def test_social_sites_includes_youtube():
    ids = [s["id"] for s in _SOCIAL_SITES]
    assert "youtube" in ids


def test_social_sites_includes_pinterest():
    ids = [s["id"] for s in _SOCIAL_SITES]
    assert "pinterest" in ids


# --- Ad networks ---

def test_scan_ad_networks_stores_manual_required(tmp_path):
    from privguard.db import get_findings, init_db

    db = tmp_path / "test.db"
    init_db(db_path=db)
    profile = _make_profile()

    _scan_ad_networks(profile, force=True, db_path=db)

    findings = get_findings(user_display_name="Test User", db_path=db)
    ad_findings = [f for f in findings if f["source"] == "ad_networks"]
    assert len(ad_findings) == 4
    assert all(f["status"] == "manual_required" for f in ad_findings)


def test_scan_ad_networks_stores_manual_instructions(tmp_path):
    from privguard.db import get_findings, init_db

    db = tmp_path / "test.db"
    init_db(db_path=db)
    profile = _make_profile()

    _scan_ad_networks(profile, force=True, db_path=db)

    findings = get_findings(user_display_name="Test User", db_path=db)
    ad_findings = [f for f in findings if f["source"] == "ad_networks"]
    assert all(f["manual_instructions"] for f in ad_findings)


def test_scan_user_calls_ad_networks_when_source_is_none(tmp_path):
    from privguard.db import init_db

    db = tmp_path / "test.db"
    init_db(db_path=db)
    profile = _make_profile()

    with patch("privguard.scanner._scan_ad_networks") as mock_ad, \
         patch("privguard.scanner._scan_brokers"), \
         patch("privguard.scanner._scan_hibp"), \
         patch("privguard.scanner._scan_social"), \
         patch("privguard.scanner._scan_search_engines"), \
         patch("privguard.scanner.load_brokers", return_value=[]):
        scan_user(profile, api_keys={}, source=None, db_path=db)
        mock_ad.assert_called_once()


def test_scan_user_calls_ad_networks_when_source_is_ad_networks(tmp_path):
    from privguard.db import init_db

    db = tmp_path / "test.db"
    init_db(db_path=db)
    profile = _make_profile()

    with patch("privguard.scanner._scan_ad_networks") as mock_ad, \
         patch("privguard.scanner.load_brokers", return_value=[]):
        scan_user(profile, api_keys={}, source="ad_networks", db_path=db)
        mock_ad.assert_called_once()


# --- Progress callback ---

def test_scan_user_calls_progress_cb_for_each_broker(tmp_path):
    from privguard.db import init_db

    db = tmp_path / "test.db"
    init_db(db_path=db)
    profile = _make_profile()

    events = []

    brokers = [
        {"id": "test1", "name": "TestBroker1", "opt_out_url": "https://example.com/1",
         "submission_method": "manual", "form_fields": {}, "requires_email_verification": False,
         "requires_id_verification": False, "manual_instructions": "step 1"},
        {"id": "test2", "name": "TestBroker2", "opt_out_url": "https://example.com/2",
         "submission_method": "manual", "form_fields": {}, "requires_email_verification": False,
         "requires_id_verification": False, "manual_instructions": "step 1"},
    ]

    with patch("privguard.scanner.load_brokers", return_value=brokers), \
         patch("privguard.scanner.requests.head") as mock_head, \
         patch("privguard.scanner.time.sleep"):
        mock_head.return_value = MagicMock(status_code=200)
        scan_user(profile, api_keys={}, source="brokers", db_path=db,
                  progress_cb=events.append)

    progress_events = [e for e in events if e["type"] == "progress"]
    assert len(progress_events) == 2
    assert progress_events[0]["source"] == "brokers"
    assert progress_events[0]["site"] in ("TestBroker1", "TestBroker2")

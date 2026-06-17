"""Tests for privguard/db.py — SQLite access layer."""
import sqlite3
from pathlib import Path

import pytest

from privguard.db import (
    get_breaches,
    get_findings,
    init_db,
    update_finding_status,
    upsert_breach,
    upsert_finding,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _finding_rows(db_path: Path) -> list[dict]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM findings").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _breach_rows(db_path: Path) -> list[dict]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM breaches").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# init_db
# ---------------------------------------------------------------------------

def test_init_db_creates_findings_table(tmp_path):
    db = tmp_path / "test.db"
    init_db(db_path=db)
    conn = sqlite3.connect(db)
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    conn.close()
    assert "findings" in tables


def test_init_db_creates_breaches_table(tmp_path):
    db = tmp_path / "test.db"
    init_db(db_path=db)
    conn = sqlite3.connect(db)
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    conn.close()
    assert "breaches" in tables


def test_init_db_is_idempotent(tmp_path):
    """Calling init_db twice must not raise and must not duplicate tables."""
    db = tmp_path / "test.db"
    init_db(db_path=db)
    init_db(db_path=db)  # second call should be a no-op


# ---------------------------------------------------------------------------
# upsert_finding — insert
# ---------------------------------------------------------------------------

def test_upsert_finding_inserts_new_row(tmp_path):
    db = tmp_path / "test.db"
    init_db(db_path=db)
    upsert_finding(
        user_display_name="Alice",
        source="data_broker",
        site_id="spokeo",
        site_name="Spokeo",
        status="found",
        opt_out_url="https://spokeo.com/opt-out",
        data_found="Alice Smith, Austin TX",
        db_path=db,
    )
    rows = _finding_rows(db)
    assert len(rows) == 1
    assert rows[0]["user_display_name"] == "Alice"
    assert rows[0]["site_id"] == "spokeo"
    assert rows[0]["status"] == "found"


def test_upsert_finding_stores_optional_fields(tmp_path):
    db = tmp_path / "test.db"
    init_db(db_path=db)
    upsert_finding(
        user_display_name="Alice",
        source="data_broker",
        site_id="intelius",
        site_name="Intelius",
        status="found",
        manual_instructions="Send email to privacy@intelius.com",
        notes="Tried twice",
        db_path=db,
    )
    rows = _finding_rows(db)
    assert rows[0]["manual_instructions"] == "Send email to privacy@intelius.com"
    assert rows[0]["notes"] == "Tried twice"


# ---------------------------------------------------------------------------
# upsert_finding — update
# ---------------------------------------------------------------------------

def test_upsert_finding_updates_existing_row(tmp_path):
    db = tmp_path / "test.db"
    init_db(db_path=db)
    upsert_finding(
        user_display_name="Alice",
        source="data_broker",
        site_id="spokeo",
        site_name="Spokeo",
        status="found",
        db_path=db,
    )
    upsert_finding(
        user_display_name="Alice",
        source="data_broker",
        site_id="spokeo",
        site_name="Spokeo",
        status="submitted",
        db_path=db,
    )
    rows = _finding_rows(db)
    assert len(rows) == 1, "upsert must not create a duplicate row"
    assert rows[0]["status"] == "submitted"


def test_upsert_finding_different_users_create_separate_rows(tmp_path):
    db = tmp_path / "test.db"
    init_db(db_path=db)
    upsert_finding(
        user_display_name="Alice",
        source="data_broker",
        site_id="spokeo",
        site_name="Spokeo",
        status="found",
        db_path=db,
    )
    upsert_finding(
        user_display_name="Bob",
        source="data_broker",
        site_id="spokeo",
        site_name="Spokeo",
        status="found",
        db_path=db,
    )
    rows = _finding_rows(db)
    assert len(rows) == 2


# ---------------------------------------------------------------------------
# upsert_finding — status downgrade protection
# ---------------------------------------------------------------------------

def test_upsert_finding_does_not_downgrade_from_submitted(tmp_path):
    db = tmp_path / "test.db"
    init_db(db_path=db)
    upsert_finding(
        user_display_name="Alice",
        source="data_broker",
        site_id="spokeo",
        site_name="Spokeo",
        status="submitted",
        db_path=db,
    )
    # Attempt to downgrade to "found"
    upsert_finding(
        user_display_name="Alice",
        source="data_broker",
        site_id="spokeo",
        site_name="Spokeo",
        status="found",
        db_path=db,
    )
    rows = _finding_rows(db)
    assert rows[0]["status"] == "submitted", "Status must not be downgraded from 'submitted'"


def test_upsert_finding_does_not_downgrade_from_pending_verification(tmp_path):
    db = tmp_path / "test.db"
    init_db(db_path=db)
    upsert_finding(
        user_display_name="Alice",
        source="data_broker",
        site_id="spokeo",
        site_name="Spokeo",
        status="pending_verification",
        db_path=db,
    )
    upsert_finding(
        user_display_name="Alice",
        source="data_broker",
        site_id="spokeo",
        site_name="Spokeo",
        status="found",
        db_path=db,
    )
    rows = _finding_rows(db)
    assert rows[0]["status"] == "pending_verification"


def test_upsert_finding_does_not_downgrade_from_cleared(tmp_path):
    db = tmp_path / "test.db"
    init_db(db_path=db)
    upsert_finding(
        user_display_name="Alice",
        source="data_broker",
        site_id="spokeo",
        site_name="Spokeo",
        status="cleared",
        db_path=db,
    )
    upsert_finding(
        user_display_name="Alice",
        source="data_broker",
        site_id="spokeo",
        site_name="Spokeo",
        status="found",
        db_path=db,
    )
    rows = _finding_rows(db)
    assert rows[0]["status"] == "cleared"


# ---------------------------------------------------------------------------
# update_finding_status
# ---------------------------------------------------------------------------

def test_update_finding_status_changes_status(tmp_path):
    db = tmp_path / "test.db"
    init_db(db_path=db)
    upsert_finding(
        user_display_name="Alice",
        source="data_broker",
        site_id="spokeo",
        site_name="Spokeo",
        status="found",
        db_path=db,
    )
    rows = _finding_rows(db)
    finding_id = rows[0]["id"]
    update_finding_status(finding_id=finding_id, status="submitted", db_path=db)
    rows = _finding_rows(db)
    assert rows[0]["status"] == "submitted"


def test_update_finding_status_sets_screenshot_path(tmp_path):
    db = tmp_path / "test.db"
    init_db(db_path=db)
    upsert_finding(
        user_display_name="Alice",
        source="data_broker",
        site_id="spokeo",
        site_name="Spokeo",
        status="found",
        db_path=db,
    )
    rows = _finding_rows(db)
    finding_id = rows[0]["id"]
    update_finding_status(
        finding_id=finding_id,
        status="submitted",
        screenshot_path="/home/user/.privguard/screenshots/spokeo_alice.png",
        db_path=db,
    )
    rows = _finding_rows(db)
    assert rows[0]["screenshot_path"] == "/home/user/.privguard/screenshots/spokeo_alice.png"


# ---------------------------------------------------------------------------
# upsert_breach — insert
# ---------------------------------------------------------------------------

def test_upsert_breach_inserts_new_breach(tmp_path):
    db = tmp_path / "test.db"
    init_db(db_path=db)
    upsert_breach(
        user_display_name="Alice",
        email="alice@example.com",
        breach_name="LinkedIn",
        breach_date="2021-06-22",
        exposed_fields="Email, Password",
        hibp_url="https://haveibeenpwned.com/breach/LinkedIn",
        db_path=db,
    )
    rows = _breach_rows(db)
    assert len(rows) == 1
    assert rows[0]["breach_name"] == "LinkedIn"
    assert rows[0]["email"] == "alice@example.com"


# ---------------------------------------------------------------------------
# upsert_breach — no duplicates
# ---------------------------------------------------------------------------

def test_upsert_breach_no_duplicate_same_user_email_breach(tmp_path):
    db = tmp_path / "test.db"
    init_db(db_path=db)
    kwargs = dict(
        user_display_name="Alice",
        email="alice@example.com",
        breach_name="LinkedIn",
        breach_date="2021-06-22",
        exposed_fields="Email, Password",
        hibp_url="https://haveibeenpwned.com/breach/LinkedIn",
        db_path=db,
    )
    upsert_breach(**kwargs)
    upsert_breach(**kwargs)  # second call must be a no-op
    rows = _breach_rows(db)
    assert len(rows) == 1, "Duplicate breach must not be inserted"


def test_upsert_breach_different_users_separate_rows(tmp_path):
    db = tmp_path / "test.db"
    init_db(db_path=db)
    upsert_breach(
        user_display_name="Alice",
        email="alice@example.com",
        breach_name="LinkedIn",
        breach_date="2021-06-22",
        exposed_fields="Email",
        hibp_url="https://haveibeenpwned.com/breach/LinkedIn",
        db_path=db,
    )
    upsert_breach(
        user_display_name="Bob",
        email="bob@example.com",
        breach_name="LinkedIn",
        breach_date="2021-06-22",
        exposed_fields="Email",
        hibp_url="https://haveibeenpwned.com/breach/LinkedIn",
        db_path=db,
    )
    rows = _breach_rows(db)
    assert len(rows) == 2


# ---------------------------------------------------------------------------
# get_findings
# ---------------------------------------------------------------------------

def test_get_findings_returns_all_when_no_filter(tmp_path):
    db = tmp_path / "test.db"
    init_db(db_path=db)
    for name in ("Alice", "Bob"):
        upsert_finding(
            user_display_name=name,
            source="data_broker",
            site_id="spokeo",
            site_name="Spokeo",
            status="found",
            db_path=db,
        )
    results = get_findings(db_path=db)
    assert len(results) == 2


def test_get_findings_filters_by_user_display_name(tmp_path):
    db = tmp_path / "test.db"
    init_db(db_path=db)
    upsert_finding(
        user_display_name="Alice",
        source="data_broker",
        site_id="spokeo",
        site_name="Spokeo",
        status="found",
        db_path=db,
    )
    upsert_finding(
        user_display_name="Bob",
        source="data_broker",
        site_id="spokeo",
        site_name="Spokeo",
        status="found",
        db_path=db,
    )
    results = get_findings(user_display_name="Alice", db_path=db)
    assert len(results) == 1
    assert results[0]["user_display_name"] == "Alice"


def test_get_findings_filters_by_status(tmp_path):
    db = tmp_path / "test.db"
    init_db(db_path=db)
    upsert_finding(
        user_display_name="Alice",
        source="data_broker",
        site_id="spokeo",
        site_name="Spokeo",
        status="found",
        db_path=db,
    )
    upsert_finding(
        user_display_name="Alice",
        source="data_broker",
        site_id="intelius",
        site_name="Intelius",
        status="submitted",
        db_path=db,
    )
    results = get_findings(status="submitted", db_path=db)
    assert len(results) == 1
    assert results[0]["site_id"] == "intelius"


def test_get_findings_returns_list_of_dicts(tmp_path):
    db = tmp_path / "test.db"
    init_db(db_path=db)
    upsert_finding(
        user_display_name="Alice",
        source="data_broker",
        site_id="spokeo",
        site_name="Spokeo",
        status="found",
        db_path=db,
    )
    results = get_findings(db_path=db)
    assert isinstance(results, list)
    assert isinstance(results[0], dict)
    assert "id" in results[0]
    assert "site_name" in results[0]


# ---------------------------------------------------------------------------
# get_breaches
# ---------------------------------------------------------------------------

def test_get_breaches_filters_by_user_display_name(tmp_path):
    db = tmp_path / "test.db"
    init_db(db_path=db)
    upsert_breach(
        user_display_name="Alice",
        email="alice@example.com",
        breach_name="LinkedIn",
        breach_date="2021-06-22",
        exposed_fields="Email",
        hibp_url="https://haveibeenpwned.com/breach/LinkedIn",
        db_path=db,
    )
    upsert_breach(
        user_display_name="Bob",
        email="bob@example.com",
        breach_name="LinkedIn",
        breach_date="2021-06-22",
        exposed_fields="Email",
        hibp_url="https://haveibeenpwned.com/breach/LinkedIn",
        db_path=db,
    )
    results = get_breaches(user_display_name="Alice", db_path=db)
    assert len(results) == 1
    assert results[0]["user_display_name"] == "Alice"


def test_get_breaches_returns_all_when_no_filter(tmp_path):
    db = tmp_path / "test.db"
    init_db(db_path=db)
    upsert_breach(
        user_display_name="Alice",
        email="alice@example.com",
        breach_name="LinkedIn",
        breach_date="2021-06-22",
        exposed_fields="Email",
        hibp_url="https://haveibeenpwned.com/breach/LinkedIn",
        db_path=db,
    )
    upsert_breach(
        user_display_name="Bob",
        email="bob@example.com",
        breach_name="Adobe",
        breach_date="2013-10-04",
        exposed_fields="Email, Password",
        hibp_url="https://haveibeenpwned.com/breach/Adobe",
        db_path=db,
    )
    results = get_breaches(db_path=db)
    assert len(results) == 2

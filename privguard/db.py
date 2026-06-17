"""SQLite access layer for PrivGuard."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path.home() / ".privguard" / "privguard.db"

# Statuses that must never be overwritten by a lower-priority status
_PROTECTED_STATUSES = {"submitted", "pending_verification", "cleared"}

_DDL = """
CREATE TABLE IF NOT EXISTS findings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_display_name TEXT NOT NULL,
    source TEXT NOT NULL,
    site_id TEXT NOT NULL,
    site_name TEXT NOT NULL,
    data_found TEXT,
    status TEXT NOT NULL,
    opt_out_url TEXT,
    manual_instructions TEXT,
    screenshot_path TEXT,
    last_checked DATETIME,
    last_submitted DATETIME,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS breaches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_display_name TEXT NOT NULL,
    email TEXT NOT NULL,
    breach_name TEXT NOT NULL,
    breach_date TEXT,
    exposed_fields TEXT,
    hibp_url TEXT,
    added_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""


def _connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(db_path: Path = DB_PATH) -> None:
    """Create tables if they do not already exist."""
    conn = _connect(db_path)
    conn.executescript(_DDL)
    conn.commit()
    conn.close()


def upsert_finding(
    user_display_name: str,
    source: str,
    site_id: str,
    site_name: str,
    status: str,
    opt_out_url: str | None = None,
    manual_instructions: str | None = None,
    data_found: str | None = None,
    notes: str | None = None,
    db_path: Path = DB_PATH,
) -> None:
    """Insert a new finding or update an existing one.

    The unique key is (user_display_name, site_id).  When an existing row
    already has a protected status ('submitted', 'pending_verification',
    'cleared'), the status column is left unchanged.
    """
    now = datetime.now(timezone.utc).isoformat()
    conn = _connect(db_path)
    try:
        existing = conn.execute(
            "SELECT id, status FROM findings WHERE user_display_name = ? AND site_id = ?",
            (user_display_name, site_id),
        ).fetchone()

        if existing is None:
            conn.execute(
                """
                INSERT INTO findings
                    (user_display_name, source, site_id, site_name, data_found,
                     status, opt_out_url, manual_instructions, notes, last_checked)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_display_name, source, site_id, site_name, data_found,
                    status, opt_out_url, manual_instructions, notes, now,
                ),
            )
        else:
            # Decide which status to keep
            current_status = existing["status"]
            new_status = current_status if current_status in _PROTECTED_STATUSES else status

            conn.execute(
                """
                UPDATE findings
                SET source = ?,
                    site_name = ?,
                    data_found = COALESCE(?, data_found),
                    status = ?,
                    opt_out_url = COALESCE(?, opt_out_url),
                    manual_instructions = COALESCE(?, manual_instructions),
                    notes = COALESCE(?, notes),
                    last_checked = ?
                WHERE user_display_name = ? AND site_id = ?
                """,
                (
                    source, site_name, data_found, new_status,
                    opt_out_url, manual_instructions, notes, now,
                    user_display_name, site_id,
                ),
            )

        conn.commit()
    finally:
        conn.close()


def get_findings(
    user_display_name: str | None = None,
    status: str | None = None,
    db_path: Path = DB_PATH,
) -> list[dict]:
    """Return findings, optionally filtered by user and/or status."""
    conn = _connect(db_path)
    try:
        query = "SELECT * FROM findings WHERE 1=1"
        params: list = []
        if user_display_name is not None:
            query += " AND user_display_name = ?"
            params.append(user_display_name)
        if status is not None:
            query += " AND status = ?"
            params.append(status)
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def update_finding_status(
    finding_id: int,
    status: str,
    screenshot_path: str | None = None,
    db_path: Path = DB_PATH,
) -> None:
    """Update the status (and optionally screenshot_path) of a finding by id."""
    now = datetime.now(timezone.utc).isoformat()
    conn = _connect(db_path)
    try:
        conn.execute(
            """
            UPDATE findings
            SET status = ?,
                screenshot_path = COALESCE(?, screenshot_path),
                last_submitted = CASE WHEN ? = 'submitted' THEN ? ELSE last_submitted END
            WHERE id = ?
            """,
            (status, screenshot_path, status, now, finding_id),
        )
        conn.commit()
    finally:
        conn.close()


def upsert_breach(
    user_display_name: str,
    email: str,
    breach_name: str,
    breach_date: str,
    exposed_fields: str,
    hibp_url: str,
    db_path: Path = DB_PATH,
) -> None:
    """Insert a breach record; skip silently if the same breach already exists."""
    conn = _connect(db_path)
    try:
        existing = conn.execute(
            """
            SELECT id FROM breaches
            WHERE user_display_name = ? AND email = ? AND breach_name = ?
            """,
            (user_display_name, email, breach_name),
        ).fetchone()
        if existing is None:
            conn.execute(
                """
                INSERT INTO breaches
                    (user_display_name, email, breach_name, breach_date, exposed_fields, hibp_url)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_display_name, email, breach_name, breach_date, exposed_fields, hibp_url),
            )
            conn.commit()
    finally:
        conn.close()


def get_breaches(
    user_display_name: str | None = None,
    db_path: Path = DB_PATH,
) -> list[dict]:
    """Return breach records, optionally filtered by user."""
    conn = _connect(db_path)
    try:
        query = "SELECT * FROM breaches WHERE 1=1"
        params: list = []
        if user_display_name is not None:
            query += " AND user_display_name = ?"
            params.append(user_display_name)
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

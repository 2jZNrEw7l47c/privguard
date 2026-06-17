# PrivGuard Phase 2 — Advanced Scan Sources Design Spec
**Date:** 2026-06-17
**Status:** Draft — saved for future implementation

---

## Overview

Phase 2 adds two advanced scan sources to PrivGuard that require external paid or rate-limited APIs and more complex data processing than the Phase 1 broker/social/HIBP sources:

1. **DeHashed dark web scanning** — searches leaked database dumps for exposed PII (emails, passwords, usernames, IPs, phone numbers)
2. **Email / username enumeration** — checks whether a given email or username is registered on 100+ platforms, identifying accounts the user may have forgotten

These are kept out of Phase 1 because each requires a third-party API key (DeHashed) or a dependency on an external tool (holehe), and both produce different output shapes than the existing `findings` / `breaches` tables — potentially requiring DB schema additions.

---

## Prerequisites for Phase 2

- Phase 1 web dashboard fully deployed and working
- DeHashed API subscription (paid — see pricing at dehashed.com/pricing)
- Python `holehe` package installed, or equivalent username-check library

---

## Feature 1: DeHashed Dark Web Scanning

### What it does

[DeHashed](https://dehashed.com) indexes leaked database dumps from data breaches and dark web sources not covered by HIBP. Where HIBP tells you "your email appeared in the Adobe breach," DeHashed can return the actual leaked records — exposed passwords (hashed), usernames, IP addresses, physical addresses, and phone numbers from the leak.

PrivGuard uses the DeHashed API to search for each of the user's emails, phone numbers, and name. Results are stored in the existing `breaches` table with `source = "dehashed"` to distinguish them from HIBP results.

### API Integration

**Endpoint:** `GET https://api.dehashed.com/search?query={value}&size=10`
**Auth:** HTTP Basic auth — API key as password, email as username
**Rate limit:** Varies by plan; add 2-second delay between queries

**Query strategy — one request per identifier:**
1. Each email address: `query=email:{email}`
2. Each phone number: `query=phone:{phone}`
3. Full name: `query=name:"{full_name}"`

**Response shape:**
```json
{
  "entries": [
    {
      "id": "...",
      "email": "alice@gmail.com",
      "username": "alice85",
      "password": "$2y$10$...",
      "hashed_password": "$2y$10$...",
      "name": "Alice Johnson",
      "vin": null,
      "address": "123 Main St",
      "ip_address": "1.2.3.4",
      "phone": "5035550142",
      "database_name": "SomeLeakedDB_2023"
    }
  ],
  "total": 3,
  "took": 0.023,
  "balance": 497
}
```

### DB Storage

DeHashed results are stored in the existing `breaches` table:

| Column | Value |
|--------|-------|
| `user_display_name` | profile display name |
| `email` | the email/phone/name queried |
| `breach_name` | `entry["database_name"]` |
| `breach_date` | not available — store `""` |
| `exposed_fields` | JSON array of non-null field names from the entry (e.g. `["email", "username", "password"]`) |
| `hibp_url` | `https://dehashed.com/search?query=email:{email}` |

A `source` column must be added to the `breaches` table to distinguish HIBP from DeHashed results:
```sql
ALTER TABLE breaches ADD COLUMN source TEXT NOT NULL DEFAULT 'hibp';
```

### Scanner Changes

New `_scan_dehashed()` function added to `scanner.py`, called when `source in (None, "dehashed")`. The `scan_user()` function gains:

```python
if source is None or source == "dehashed":
    _scan_dehashed(profile, api_key=api_keys.get("dehashed"), force=force, db_path=db_path)
```

API key stored in the vault under `api_keys.dehashed`. User adds it via the "Add Profile" or a new "API Keys" settings page in the web UI.

### UI Changes

- Breaches tab on the User Detail page gains a source filter toggle: **HIBP** | **DeHashed** | **All**
- DeHashed-sourced rows show an additional "Leaked Fields" column listing what the dump contained (username, hashed password, IP, etc.)
- Dashboard stat cards: "Breaches" count includes both sources combined

---

## Feature 2: Email / Username Enumeration

### What it does

Given an email address or username, checks whether an account with that identifier exists on 100+ online platforms — social networks, forums, gaming sites, productivity tools, and more. This surfaces accounts the user may have created years ago and forgotten, which are exposure risks (old passwords, stale personal data, abandoned profiles).

Example: a scan for `alice85` might reveal active accounts on Reddit, Twitch, DeviantArt, Flickr, Gravatar, and 12 other platforms the user didn't know were associated with their identity.

### Implementation: `holehe`

[holehe](https://github.com/megadose/holehe) is a Python library that checks email registration on 120+ services using account-recovery flows (not scraping). It returns which platforms have an account for a given email without needing the account password.

```bash
pip install holehe
```

**Usage pattern:**
```python
import asyncio
from holehe.core import get_holehe_modules, get_email_infos

modules = get_holehe_modules()
results = asyncio.run(get_email_infos(email, modules))
# results: list of {"name": "twitter", "exists": True, "emailrecovery": None, ...}
```

### New DB Table

Enumeration results don't fit cleanly into `findings` (no opt-out URL) or `breaches` (no breach event). A new table is required:

```sql
CREATE TABLE enumerated_accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_display_name TEXT NOT NULL,
    identifier TEXT NOT NULL,         -- the email or username queried
    platform TEXT NOT NULL,           -- e.g. "twitter", "github"
    exists INTEGER NOT NULL,          -- 1 = account found, 0 = not found
    profile_url TEXT,                 -- constructed URL if known
    last_checked DATETIME,
    notes TEXT,
    UNIQUE(user_display_name, identifier, platform)
);
```

### Scanner Changes

New `_scan_enumeration()` function, called when `source in (None, "enumeration")`. Iterates over all emails in the user's profile and runs holehe on each. Results stored in `enumerated_accounts`.

The `scan_user()` function gains:
```python
if source is None or source == "enumeration":
    _scan_enumeration(profile, force=force, db_path=db_path)
```

`get_findings()` and `get_breaches()` in `db.py` remain unchanged. A new `get_enumerated_accounts()` function is added to `db.py`.

### UI Changes

New sixth tab added to the User Detail page: **Accounts Found** — lists each platform where an account was detected, with a constructed profile URL where available and a note: "Review this account — it may contain outdated personal information."

No opt-out automation is possible for this source (account deletion is always manual). All rows have status `manual_required`.

---

## API Changes for Phase 2

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/users/{name}/accounts` | Return enumerated accounts from new DB table |
| `POST` | `/api/users/{name}/scan` | `source` gains two new valid values: `"dehashed"`, `"enumeration"` |

---

## Dependencies Added in Phase 2

```
# pyproject.toml additions
holehe>=1.13
```

DeHashed uses standard `requests` HTTP calls (already a dependency).

---

## Out of Scope for Phase 2

- Automatic account deletion (holehe detects accounts only; deletion is always manual)
- DeHashed result deduplication against HIBP (both stored independently)
- Credential stuffing detection
- Proxy rotation for holehe (some platforms may block repeated requests)

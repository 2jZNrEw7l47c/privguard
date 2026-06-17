# PrivGuard v2.0.0 — Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the FastAPI backend that wraps existing PrivGuard Python logic as a REST/SSE API, expand broker/social/ad-network data sources, and replace the CLI entry point with `privguard serve`.

**Architecture:** FastAPI app lives in `api/` and imports from the existing `privguard/` package directly — no duplication. Session auth uses an in-memory dict keyed by a random token stored in an httpOnly cookie. Long-running scans run in a thread-pool executor and publish progress events to a `queue.SimpleQueue` that the SSE endpoint drains.

**Tech Stack:** Python 3.11+, FastAPI 0.110+, uvicorn, python-multipart, pytest, httpx (for TestClient)

---

## File Map

| File | Action | Purpose |
|------|--------|---------|
| `data/brokers.json` | Modify | Expand from 44 → ~200 entries |
| `privguard/scanner.py` | Modify | Add 5 social platforms, `_scan_ad_networks()`, optional `progress_cb` param |
| `api/__init__.py` | Create | Empty package marker |
| `api/auth.py` | Create | In-memory session store, `get_session` dependency |
| `api/jobs.py` | Create | Thread-safe job registry with `queue.SimpleQueue` per job |
| `api/routes/__init__.py` | Create | Empty package marker |
| `api/routes/users.py` | Create | GET/POST/DELETE /api/users |
| `api/routes/scan.py` | Create | POST scan/submit, GET SSE stream |
| `api/routes/findings.py` | Create | GET findings, breaches, PATCH status |
| `api/app.py` | Create | FastAPI instance, startup HIBP catalogue, router registration |
| `api/serve.py` | Create | `privguard serve` entry point (starts uvicorn + npm) |
| `tests/test_api_auth.py` | Create | Auth endpoint tests |
| `tests/test_api_users.py` | Create | User CRUD tests |
| `tests/test_api_findings.py` | Create | Findings/breaches tests |
| `tests/test_scanner_v2.py` | Create | Tests for new scanner additions |
| `pyproject.toml` | Modify | Add fastapi/uvicorn deps, replace entry point |
| `privguard/main.py` | Delete | CLI replaced by `privguard serve` |
| `privguard/reporter.py` | Delete | Excel replaced by web UI |
| `tests/test_reporter.py` | Delete | Reporter removed |

---

## Task 1: Expand brokers.json to ~200 entries

**Files:**
- Modify: `data/brokers.json`

No tests needed — this is a data file. The scanner already loads and iterates it.

- [ ] **Step 1: Open `data/brokers.json` and append the following new entries inside the top-level array, after the existing 44 entries.**

Each entry follows the existing schema exactly. Add all entries below:

```json
  ,
  {
    "id": "zoominfo",
    "name": "ZoomInfo",
    "category": "marketing_database",
    "opt_out_url": "https://www.zoominfo.com/about/privacy/privacychoice",
    "submission_method": "manual",
    "form_fields": {},
    "requires_email_verification": false,
    "requires_id_verification": false,
    "manual_instructions": "1. Go to https://www.zoominfo.com/about/privacy/privacychoice\n2. Click 'Do Not Sell or Share My Personal Information'.\n3. Enter your name and email address.\n4. Complete the CAPTCHA and submit.\n5. You will receive a confirmation email within 72 hours."
  },
  {
    "id": "clearbit",
    "name": "Clearbit",
    "category": "marketing_database",
    "opt_out_url": "https://clearbit.com/privacy-request",
    "submission_method": "manual",
    "form_fields": {},
    "requires_email_verification": false,
    "requires_id_verification": false,
    "manual_instructions": "1. Go to https://clearbit.com/privacy-request\n2. Select 'Delete my personal data'.\n3. Enter your email address and submit.\n4. Clearbit will process the request within 30 days."
  },
  {
    "id": "apollo_io",
    "name": "Apollo.io",
    "category": "marketing_database",
    "opt_out_url": "https://www.apollo.io/privacy-policy/remove",
    "submission_method": "manual",
    "form_fields": {},
    "requires_email_verification": false,
    "requires_id_verification": false,
    "manual_instructions": "1. Go to https://www.apollo.io/privacy-policy/remove\n2. Enter your first name, last name, and email address.\n3. Click 'Submit Request'.\n4. Apollo will remove your data within 30 days."
  },
  {
    "id": "fullcontact",
    "name": "FullContact",
    "category": "marketing_database",
    "opt_out_url": "https://www.fullcontact.com/privacy/privacy-request/",
    "submission_method": "manual",
    "form_fields": {},
    "requires_email_verification": false,
    "requires_id_verification": false,
    "manual_instructions": "1. Go to https://www.fullcontact.com/privacy/privacy-request/\n2. Select 'Delete My Data'.\n3. Enter your email address.\n4. Submit. FullContact processes requests within 45 days."
  },
  {
    "id": "bombora",
    "name": "Bombora",
    "category": "marketing_database",
    "opt_out_url": "https://bombora.com/privacy/",
    "submission_method": "manual",
    "form_fields": {},
    "requires_email_verification": false,
    "requires_id_verification": false,
    "manual_instructions": "1. Go to https://bombora.com/privacy/\n2. Scroll to 'Your Privacy Rights' and click 'Submit a Request'.\n3. Select 'Delete' and provide your email address.\n4. Submit the form."
  },
  {
    "id": "epsilon",
    "name": "Epsilon / Conversant",
    "category": "marketing_database",
    "opt_out_url": "https://www.epsilon.com/us/privacy-policy/privacy-request",
    "submission_method": "manual",
    "form_fields": {},
    "requires_email_verification": false,
    "requires_id_verification": false,
    "manual_instructions": "1. Go to https://www.epsilon.com/us/privacy-policy/privacy-request\n2. Select 'Delete My Personal Information'.\n3. Fill in your name, email, and state.\n4. Submit. Epsilon responds within 45 days."
  },
  {
    "id": "neustar",
    "name": "Neustar / TransUnion Marketing",
    "category": "marketing_database",
    "opt_out_url": "https://www.home.neustar/privacy/privacy-request",
    "submission_method": "manual",
    "form_fields": {},
    "requires_email_verification": false,
    "requires_id_verification": false,
    "manual_instructions": "1. Go to https://www.home.neustar/privacy/privacy-request\n2. Select 'Opt Out of Sale of Personal Data'.\n3. Enter your name and email.\n4. Submit the form."
  },
  {
    "id": "acxiom",
    "name": "Acxiom",
    "category": "marketing_database",
    "opt_out_url": "https://isapps.acxiom.com/optout/optout.aspx",
    "submission_method": "playwright",
    "form_fields": {
      "firstName": "{first_name}",
      "lastName": "{last_name}",
      "addressLine1": "{street}",
      "city": "{city}",
      "state": "{state}",
      "zipCode": "{zip}",
      "email": "{primary_email}"
    },
    "requires_email_verification": false,
    "requires_id_verification": false,
    "manual_instructions": null
  },
  {
    "id": "oracle_bluekai",
    "name": "Oracle Data Cloud (BlueKai)",
    "category": "marketing_database",
    "opt_out_url": "https://datacloudoptout.oracle.com/optout",
    "submission_method": "manual",
    "form_fields": {},
    "requires_email_verification": false,
    "requires_id_verification": false,
    "manual_instructions": "1. Go to https://datacloudoptout.oracle.com/optout\n2. Click 'Opt Out' to opt out of all Oracle Data Cloud interest-based advertising.\n3. Note: this opt-out is cookie-based — repeat on each browser you use."
  },
  {
    "id": "lexisnexis",
    "name": "LexisNexis Risk Solutions",
    "category": "data_aggregator",
    "opt_out_url": "https://optout.lexisnexis.com/",
    "submission_method": "manual",
    "form_fields": {},
    "requires_email_verification": false,
    "requires_id_verification": true,
    "manual_instructions": "1. Go to https://optout.lexisnexis.com/\n2. Click 'Opt Out'.\n3. Enter your first name, last name, address, and date of birth.\n4. You will need to upload a government-issued photo ID.\n5. Submit. LexisNexis responds within 30 days."
  },
  {
    "id": "corelogic",
    "name": "CoreLogic",
    "category": "data_aggregator",
    "opt_out_url": "https://www.corelogic.com/privacy/",
    "submission_method": "manual",
    "form_fields": {},
    "requires_email_verification": false,
    "requires_id_verification": false,
    "manual_instructions": "1. Go to https://www.corelogic.com/privacy/\n2. Scroll to 'California Consumer Rights' or 'Privacy Requests'.\n3. Click 'Submit a Privacy Request'.\n4. Select 'Delete My Personal Information' and complete the form.\n5. CoreLogic responds within 45 days."
  },
  {
    "id": "versium",
    "name": "Versium",
    "category": "data_aggregator",
    "opt_out_url": "https://versium.com/privacy-policy/",
    "submission_method": "manual",
    "form_fields": {},
    "requires_email_verification": false,
    "requires_id_verification": false,
    "manual_instructions": "1. Go to https://versium.com/privacy-policy/\n2. Scroll to 'Your Privacy Rights' section.\n3. Email privacy@versium.com with subject 'Data Deletion Request'.\n4. Include your full name, email address, and mailing address."
  },
  {
    "id": "equifax_ixi",
    "name": "Equifax IXI Services",
    "category": "data_aggregator",
    "opt_out_url": "https://www.equifax.com/personal/privacy/",
    "submission_method": "manual",
    "form_fields": {},
    "requires_email_verification": false,
    "requires_id_verification": false,
    "manual_instructions": "1. Go to https://www.equifax.com/personal/privacy/\n2. Click 'Submit a Privacy Request'.\n3. Select 'Delete My Personal Information'.\n4. Complete identity verification and submit.\n5. Equifax responds within 45 days."
  },
  {
    "id": "transunion_tlo",
    "name": "TransUnion TLO",
    "category": "data_aggregator",
    "opt_out_url": "https://www.transunion.com/consumer-privacy",
    "submission_method": "manual",
    "form_fields": {},
    "requires_email_verification": false,
    "requires_id_verification": false,
    "manual_instructions": "1. Go to https://www.transunion.com/consumer-privacy\n2. Click 'Do Not Sell or Share My Personal Information'.\n3. Follow the identity verification steps.\n4. Submit your deletion request."
  },
  {
    "id": "datalogix",
    "name": "Oracle DataLogix",
    "category": "data_aggregator",
    "opt_out_url": "https://datacloudoptout.oracle.com/registry",
    "submission_method": "manual",
    "form_fields": {},
    "requires_email_verification": false,
    "requires_id_verification": false,
    "manual_instructions": "1. Go to https://datacloudoptout.oracle.com/registry\n2. Click 'Remove My Information'.\n3. Enter your name, email, and postal address.\n4. Submit the form."
  },
  {
    "id": "spydialer",
    "name": "Spy Dialer",
    "category": "phone_lookup",
    "opt_out_url": "https://www.spydialer.com/optout.aspx",
    "submission_method": "playwright",
    "form_fields": {
      "phone": "{phone}",
      "email": "{primary_email}"
    },
    "requires_email_verification": true,
    "requires_id_verification": false,
    "manual_instructions": null
  },
  {
    "id": "numlookup",
    "name": "NumLookup",
    "category": "phone_lookup",
    "opt_out_url": "https://www.numlookup.com/opt-out",
    "submission_method": "playwright",
    "form_fields": {
      "phone": "{phone}",
      "email": "{primary_email}"
    },
    "requires_email_verification": true,
    "requires_id_verification": false,
    "manual_instructions": null
  },
  {
    "id": "usphonebook",
    "name": "USPhoneBook",
    "category": "phone_lookup",
    "opt_out_url": "https://www.usphonebook.com/opt-out",
    "submission_method": "manual",
    "form_fields": {},
    "requires_email_verification": false,
    "requires_id_verification": false,
    "manual_instructions": "1. Go to https://www.usphonebook.com/opt-out\n2. Search for your phone number or name.\n3. Click 'Remove' next to your listing.\n4. Complete the CAPTCHA and confirm."
  },
  {
    "id": "411_com",
    "name": "411.com",
    "category": "phone_lookup",
    "opt_out_url": "https://www.411.com/privacy/edit",
    "submission_method": "manual",
    "form_fields": {},
    "requires_email_verification": false,
    "requires_id_verification": false,
    "manual_instructions": "1. Go to https://www.411.com/privacy/edit\n2. Enter your name, city, and state to find your listing.\n3. Click 'Remove Listing' next to your entry.\n4. Enter your email to confirm removal."
  },
  {
    "id": "whocalledme",
    "name": "WhoCalledMe",
    "category": "phone_lookup",
    "opt_out_url": "https://www.whocalledme.com/Privacy",
    "submission_method": "manual",
    "form_fields": {},
    "requires_email_verification": false,
    "requires_id_verification": false,
    "manual_instructions": "1. Go to https://www.whocalledme.com/Privacy\n2. Submit a removal request using the contact form.\n3. Include your phone number and name in the request."
  },
  {
    "id": "anywho",
    "name": "AnyWho",
    "category": "phone_lookup",
    "opt_out_url": "https://www.anywho.com/optout",
    "submission_method": "manual",
    "form_fields": {},
    "requires_email_verification": false,
    "requires_id_verification": false,
    "manual_instructions": "1. Go to https://www.anywho.com/optout\n2. Enter your first name, last name, city, and state.\n3. Find your listing and click 'Opt Out'.\n4. Enter your email to confirm."
  },
  {
    "id": "addresses_com",
    "name": "Addresses.com",
    "category": "address_lookup",
    "opt_out_url": "https://www.addresses.com/optout.php",
    "submission_method": "playwright",
    "form_fields": {
      "firstname": "{first_name}",
      "lastname": "{last_name}",
      "city": "{city}",
      "state": "{state}"
    },
    "requires_email_verification": true,
    "requires_id_verification": false,
    "manual_instructions": null
  },
  {
    "id": "publicrecordsnow",
    "name": "PublicRecordsNow",
    "category": "address_lookup",
    "opt_out_url": "https://www.publicrecordsnow.com/removal-request/",
    "submission_method": "manual",
    "form_fields": {},
    "requires_email_verification": false,
    "requires_id_verification": false,
    "manual_instructions": "1. Go to https://www.publicrecordsnow.com/removal-request/\n2. Enter your full name and state.\n3. Find your record and click 'Remove This Record'.\n4. Submit the form with your email address."
  },
  {
    "id": "ussearch",
    "name": "US Search",
    "category": "address_lookup",
    "opt_out_url": "https://www.ussearch.com/opt-out/submit/",
    "submission_method": "playwright",
    "form_fields": {
      "firstName": "{first_name}",
      "lastName": "{last_name}",
      "state": "{state}",
      "email": "{primary_email}"
    },
    "requires_email_verification": true,
    "requires_id_verification": false,
    "manual_instructions": null
  },
  {
    "id": "checkpeople",
    "name": "CheckPeople",
    "category": "address_lookup",
    "opt_out_url": "https://checkpeople.com/opt-out",
    "submission_method": "manual",
    "form_fields": {},
    "requires_email_verification": false,
    "requires_id_verification": false,
    "manual_instructions": "1. Go to https://checkpeople.com/opt-out\n2. Search for your name and state.\n3. Select your record and click 'Remove This Record'.\n4. Enter your email and submit."
  },
  {
    "id": "mugshotlook",
    "name": "MugshotLook",
    "category": "mugshot_arrest",
    "opt_out_url": "https://mugshotlook.com/removal-request",
    "submission_method": "manual",
    "form_fields": {},
    "requires_email_verification": false,
    "requires_id_verification": true,
    "manual_instructions": "1. Go to https://mugshotlook.com/removal-request\n2. Enter the URL of your mugshot page.\n3. Provide your full name and email address.\n4. Upload a copy of a government-issued photo ID.\n5. Submit. Processing takes 3–7 business days."
  },
  {
    "id": "arrests_org",
    "name": "Arrests.org",
    "category": "mugshot_arrest",
    "opt_out_url": "https://arrests.org/remove.php",
    "submission_method": "manual",
    "form_fields": {},
    "requires_email_verification": false,
    "requires_id_verification": true,
    "manual_instructions": "1. Go to https://arrests.org/remove.php\n2. Enter the URL of your listing on arrests.org.\n3. Provide your full name and contact email.\n4. Upload a government-issued photo ID.\n5. Submit. Removal takes up to 10 business days."
  },
  {
    "id": "staterecords_org",
    "name": "StateRecords.org",
    "category": "mugshot_arrest",
    "opt_out_url": "https://staterecords.org/removal-request.php",
    "submission_method": "manual",
    "form_fields": {},
    "requires_email_verification": false,
    "requires_id_verification": false,
    "manual_instructions": "1. Go to https://staterecords.org/removal-request.php\n2. Enter the URL of your record page.\n3. Provide your email address.\n4. Submit the request."
  },
  {
    "id": "courtcasefinder",
    "name": "CourtCaseFinder",
    "category": "mugshot_arrest",
    "opt_out_url": "https://www.courtcasefinder.com/remove",
    "submission_method": "manual",
    "form_fields": {},
    "requires_email_verification": false,
    "requires_id_verification": false,
    "manual_instructions": "1. Go to https://www.courtcasefinder.com/remove\n2. Search for your name.\n3. Click 'Remove This Record' next to your listing.\n4. Provide your email address to confirm removal."
  },
  {
    "id": "justmugshots",
    "name": "JustMugshots",
    "category": "mugshot_arrest",
    "opt_out_url": "https://justmugshots.com/removal",
    "submission_method": "manual",
    "form_fields": {},
    "requires_email_verification": false,
    "requires_id_verification": true,
    "manual_instructions": "1. Go to https://justmugshots.com/removal\n2. Search for your listing.\n3. Click 'Request Removal' on your record.\n4. Upload a government-issued photo ID.\n5. Submit. Processing takes 5–10 business days."
  },
  {
    "id": "bustedmugshots",
    "name": "BustedMugshots",
    "category": "mugshot_arrest",
    "opt_out_url": "https://bustedmugshots.com/removal",
    "submission_method": "manual",
    "form_fields": {},
    "requires_email_verification": false,
    "requires_id_verification": true,
    "manual_instructions": "1. Go to https://bustedmugshots.com/removal\n2. Find your listing by searching your name.\n3. Click 'Remove This Record'.\n4. Complete identity verification with a government ID.\n5. Submit. Processing takes 5–7 business days."
  },
  {
    "id": "mugshotzone",
    "name": "MugshotZone",
    "category": "mugshot_arrest",
    "opt_out_url": "https://mugshotzone.com/opt-out",
    "submission_method": "manual",
    "form_fields": {},
    "requires_email_verification": false,
    "requires_id_verification": false,
    "manual_instructions": "1. Go to https://mugshotzone.com/opt-out\n2. Enter the URL of your listing.\n3. Provide your name and email.\n4. Submit the removal request."
  }
```

- [ ] **Step 2: Verify the JSON is valid**

```bash
python -c "import json; data=json.load(open('data/brokers.json')); print(f'{len(data)} entries')"
```

Expected output: `79 entries` (44 original + 35 new)

- [ ] **Step 3: Commit**

```bash
git add data/brokers.json
git commit -m "feat: expand brokers.json with marketing, phone, address, mugshot categories"
```

---

## Task 2: Update scanner.py — social platforms, ad_networks, progress callback

**Files:**
- Modify: `privguard/scanner.py`
- Create: `tests/test_scanner_v2.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_scanner_v2.py`:

```python
"""Tests for scanner.py v2 additions: new social sites, ad_networks source, progress_cb."""
from __future__ import annotations

import json
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
         patch("privguard.scanner.requests.head") as mock_head:
        mock_head.return_value = MagicMock(status_code=200)
        scan_user(profile, api_keys={}, source="brokers", db_path=db,
                  progress_cb=events.append)

    progress_events = [e for e in events if e["type"] == "progress"]
    assert len(progress_events) == 2
    assert progress_events[0]["source"] == "brokers"
    assert progress_events[0]["site"] in ("TestBroker1", "TestBroker2")
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_scanner_v2.py -v
```

Expected: multiple FAILED (ImportError on `_scan_ad_networks`, assertions fail on social sites)

- [ ] **Step 3: Add 5 new social platforms to `_SOCIAL_SITES` in `privguard/scanner.py`**

Find the `_SOCIAL_SITES` list (currently ends with `twitter_x` entry) and add these entries:

```python
    {
        "id": "instagram",
        "name": "Instagram",
        "search_url": "https://www.instagram.com/{name_slug}/",
    },
    {
        "id": "tiktok",
        "name": "TikTok",
        "search_url": "https://www.tiktok.com/@{name_slug}",
    },
    {
        "id": "reddit",
        "name": "Reddit",
        "search_url": "https://www.reddit.com/search/?q={full_name}&type=user",
    },
    {
        "id": "youtube",
        "name": "YouTube",
        "search_url": "https://www.youtube.com/results?search_query={full_name}",
    },
    {
        "id": "pinterest",
        "name": "Pinterest",
        "search_url": "https://www.pinterest.com/search/users/?q={full_name}",
    },
```

- [ ] **Step 4: Add `_scan_ad_networks()` function to `privguard/scanner.py`**

Add after `_scan_search_engines()` function:

```python
_AD_NETWORK_SITES = [
    {
        "id": "nai_optout",
        "name": "NAI (Network Advertising Initiative)",
        "opt_out_url": "https://optout.networkadvertising.org/",
        "instructions": (
            "1. Go to https://optout.networkadvertising.org/\n"
            "2. Click 'Opt Out of All' to opt out of all NAI member ad networks at once.\n"
            "3. Note: this opt-out is cookie-based. Repeat in each browser you use.\n"
            "4. Do not clear cookies after opting out or the opt-out will be lost."
        ),
    },
    {
        "id": "daa_optout",
        "name": "DAA (Digital Advertising Alliance)",
        "opt_out_url": "https://optout.aboutads.info/",
        "instructions": (
            "1. Go to https://optout.aboutads.info/\n"
            "2. Wait for the page to scan your browser for participating companies.\n"
            "3. Click 'Opt Out of All' to opt out of all DAA member ad targeting.\n"
            "4. Note: cookie-based opt-out. Repeat in each browser you use."
        ),
    },
    {
        "id": "google_ads",
        "name": "Google Ad Personalization",
        "opt_out_url": "https://adssettings.google.com/",
        "instructions": (
            "1. Sign in to your Google account and go to https://adssettings.google.com/\n"
            "2. Toggle 'Ad personalization' to OFF.\n"
            "3. Also visit https://www.google.com/settings/ads/anonymous to opt out when "
            "not signed in.\n"
            "4. For YouTube: go to youtube.com > Settings > Privacy > turn off ad personalization."
        ),
    },
    {
        "id": "facebook_offsite",
        "name": "Facebook Off-Facebook Activity",
        "opt_out_url": "https://www.facebook.com/off_facebook_activity/",
        "instructions": (
            "1. Log in to Facebook and go to https://www.facebook.com/off_facebook_activity/\n"
            "2. Click 'More Options' then 'Manage Future Activity'.\n"
            "3. Toggle 'Future Off-Facebook Activity' to OFF.\n"
            "4. Click 'Turn Off' to confirm.\n"
            "5. Optionally click 'Clear History' to disconnect past data from your account."
        ),
    },
]


def _scan_ad_networks(
    profile: dict,
    force: bool,
    db_path: Path,
) -> None:
    display_name = profile["display_name"]

    existing: dict[str, str] = {
        f["site_id"]: f["status"]
        for f in get_findings(user_display_name=display_name, db_path=db_path)
        if f.get("source") == "ad_networks"
    }

    for site in _AD_NETWORK_SITES:
        if not force and existing.get(site["id"]) in _SKIP_STATUSES:
            continue

        upsert_finding(
            user_display_name=display_name,
            source="ad_networks",
            site_id=site["id"],
            site_name=site["name"],
            status="manual_required",
            opt_out_url=site["opt_out_url"],
            manual_instructions=site["instructions"],
            db_path=db_path,
        )
```

- [ ] **Step 5: Add `progress_cb` parameter to `scan_user()` and `_scan_brokers()` in `privguard/scanner.py`**

Change `scan_user` signature:

```python
def scan_user(
    profile: dict,
    api_keys: dict,
    source: Optional[str] = None,
    force: bool = False,
    db_path: Path = DB_PATH,
    progress_cb=None,
) -> None:
    brokers = load_brokers()

    if source is None or source == "brokers":
        _scan_brokers(profile, brokers, force=force, db_path=db_path, progress_cb=progress_cb)
    if source is None or source == "hibp":
        _scan_hibp(profile, api_key=api_keys.get("hibp"), force=force, db_path=db_path)
    if source is None or source == "social":
        _scan_social(profile, force=force, db_path=db_path)
    if source is None or source == "search_engines":
        _scan_search_engines(profile, force=force, db_path=db_path)
    if source is None or source == "ad_networks":
        _scan_ad_networks(profile, force=force, db_path=db_path)
```

Change `_scan_brokers` signature and add callback call after `upsert_finding`:

```python
def _scan_brokers(
    profile: dict,
    brokers: list[dict],
    force: bool,
    db_path: Path,
    progress_cb=None,
) -> None:
    display_name = profile["display_name"]

    existing: dict[str, str] = {
        f["site_id"]: f["status"]
        for f in get_findings(user_display_name=display_name, db_path=db_path)
        if f.get("source") == "brokers"
    }

    total = len(brokers)
    for count, broker in enumerate(brokers, start=1):
        site_id = broker["id"]
        if not force and existing.get(site_id) in _SKIP_STATUSES:
            if progress_cb:
                progress_cb({"type": "progress", "source": "brokers",
                             "site": broker["name"], "status": "skipped",
                             "count": count, "total": total})
            continue

        url = broker.get("opt_out_url", "")
        try:
            resp = requests.head(url, timeout=10, allow_redirects=True)
            status = "found" if resp.status_code == 200 else "not_found"
        except Exception:
            status = "not_found"

        upsert_finding(
            user_display_name=display_name,
            source="brokers",
            site_id=site_id,
            site_name=broker["name"],
            status=status,
            opt_out_url=url,
            manual_instructions=broker.get("manual_instructions"),
            db_path=db_path,
        )

        if progress_cb:
            progress_cb({"type": "progress", "source": "brokers",
                         "site": broker["name"], "status": status,
                         "count": count, "total": total})

        time.sleep(random.uniform(0.5, 1.5))
```

- [ ] **Step 6: Run tests**

```bash
pytest tests/test_scanner_v2.py -v
```

Expected: all PASSED

- [ ] **Step 7: Run full test suite to check nothing is broken**

```bash
pytest -v
```

Expected: all existing tests still pass (new tests pass too)

- [ ] **Step 8: Commit**

```bash
git add privguard/scanner.py tests/test_scanner_v2.py
git commit -m "feat: add 5 social platforms, ad_networks source, progress_cb to scanner"
```

---

## Task 3: FastAPI scaffold — pyproject.toml + api/ structure

**Files:**
- Modify: `pyproject.toml`
- Create: `api/__init__.py`, `api/routes/__init__.py`

- [ ] **Step 1: Update `pyproject.toml`** — add FastAPI dependencies and replace the entry point:

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "privguard"
version = "2.0.0"
description = "PrivGuard v2 — web dashboard for PII exposure tracking and opt-out automation."
requires-python = ">=3.11"
dependencies = [
    "click>=8.1",
    "cryptography>=41.0",
    "playwright>=1.40",
    "requests>=2.31",
    "openpyxl>=3.1",
    "fastapi>=0.110",
    "uvicorn[standard]>=0.29",
    "python-multipart>=0.0.9",
]

[project.scripts]
privguard = "api.serve:main"

[tool.setuptools.packages.find]
where = ["."]
include = ["privguard*", "api*"]
```

- [ ] **Step 2: Create empty package markers**

Create `api/__init__.py` (empty file):
```python
```

Create `api/routes/__init__.py` (empty file):
```python
```

- [ ] **Step 3: Install updated package**

```bash
pip install -e .
```

Expected: installs without error

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml api/__init__.py api/routes/__init__.py
git commit -m "chore: add FastAPI deps, restructure entry point for v2"
```

---

## Task 4: Session auth — `api/auth.py`

**Files:**
- Create: `api/auth.py`
- Create: `tests/test_api_auth.py`
- Create: `tests/conftest_api.py` (shared fixtures for API tests)

- [ ] **Step 1: Create shared API test fixtures at `tests/conftest_api.py`**

```python
"""Shared fixtures for FastAPI endpoint tests."""
from __future__ import annotations

import json
from pathlib import Path

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
def tmp_vault(tmp_path: Path) -> Path:
    vault_path = tmp_path / "vault.enc"
    save_vault(MASTER_PASSWORD, VAULT_DATA, vault_path=vault_path)
    return vault_path


@pytest.fixture()
def tmp_db(tmp_path: Path) -> Path:
    from privguard.db import init_db
    db_path = tmp_path / "test.db"
    init_db(db_path=db_path)
    return db_path


@pytest.fixture()
def client(tmp_vault: Path, tmp_db: Path, monkeypatch):
    monkeypatch.setenv("PRIVGUARD_VAULT_PATH", str(tmp_vault))
    monkeypatch.setenv("PRIVGUARD_DB_PATH", str(tmp_db))
    from api.app import app
    return TestClient(app, raise_server_exceptions=True)


@pytest.fixture()
def auth_client(client: TestClient):
    resp = client.post("/api/auth/unlock", json={"password": MASTER_PASSWORD})
    assert resp.status_code == 200
    return client
```

- [ ] **Step 2: Write failing auth tests at `tests/test_api_auth.py`**

```python
"""Tests for POST /api/auth/unlock and POST /api/auth/lock."""
from __future__ import annotations

from fastapi.testclient import TestClient


def test_unlock_valid_password_returns_200(client: TestClient):
    resp = client.post("/api/auth/unlock", json={"password": "test-master-password"})
    assert resp.status_code == 200


def test_unlock_sets_session_cookie(client: TestClient):
    resp = client.post("/api/auth/unlock", json={"password": "test-master-password"})
    assert "session" in resp.cookies


def test_unlock_wrong_password_returns_401(client: TestClient):
    resp = client.post("/api/auth/unlock", json={"password": "wrong-password"})
    assert resp.status_code == 401


def test_unlock_empty_password_returns_401(client: TestClient):
    resp = client.post("/api/auth/unlock", json={"password": ""})
    assert resp.status_code == 401


def test_lock_clears_session(auth_client: TestClient):
    resp = auth_client.post("/api/auth/lock")
    assert resp.status_code == 200
    resp2 = auth_client.get("/api/users")
    assert resp2.status_code == 401


def test_protected_route_without_cookie_returns_401(client: TestClient):
    resp = client.get("/api/users")
    assert resp.status_code == 401
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
pytest tests/test_api_auth.py -v
```

Expected: ImportError or connection errors (app doesn't exist yet)

- [ ] **Step 4: Create `api/auth.py`**

```python
"""In-memory session store for PrivGuard API.

Sessions are keyed by a random URL-safe token stored in an httpOnly cookie.
Each session stores the decrypted vault dict and the master password (needed
to re-encrypt on vault writes). Sessions last until server restart or explicit
/api/auth/lock call.
"""
from __future__ import annotations

import secrets
from typing import Optional

from fastapi import Cookie, HTTPException


_sessions: dict[str, dict] = {}


def create_session(vault: dict, password: str) -> str:
    """Store vault + password, return a new session token."""
    token = secrets.token_urlsafe(32)
    _sessions[token] = {"vault": vault, "password": password}
    return token


def get_session(session: Optional[str] = Cookie(default=None)) -> dict:
    """FastAPI dependency — resolves the session or raises 401."""
    if session is None or session not in _sessions:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    return _sessions[session]


def destroy_session(token: str) -> None:
    _sessions.pop(token, None)
```

- [ ] **Step 5: Create minimal `api/app.py` so tests can import it (full version in Task 9)**

```python
"""FastAPI application — assembled in full in Task 9."""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, Response
from pydantic import BaseModel

from api.auth import create_session, destroy_session, get_session
from privguard.vault import VAULT_PATH, load_vault

app = FastAPI(title="PrivGuard API")


def _vault_path() -> Path:
    env = os.environ.get("PRIVGUARD_VAULT_PATH")
    return Path(env) if env else VAULT_PATH


class UnlockRequest(BaseModel):
    password: str


@app.post("/api/auth/unlock")
def unlock(body: UnlockRequest, response: Response):
    try:
        vault = load_vault(body.password, vault_path=_vault_path())
    except (ValueError, FileNotFoundError) as exc:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail=str(exc))
    token = create_session(vault, body.password)
    response.set_cookie("session", token, httponly=True, samesite="strict")
    return {"status": "unlocked"}


@app.post("/api/auth/lock")
def lock(response: Response, session: str | None = None):
    from fastapi import Cookie as FCookie
    # read cookie manually since we need the raw token to destroy it
    return {"status": "locked"}
```

Wait — the lock endpoint needs to read the raw cookie value to call `destroy_session`. Let me write it properly:

```python
"""FastAPI application — assembled in full in Task 9."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from fastapi import Cookie, FastAPI, HTTPException, Response
from pydantic import BaseModel

from api.auth import create_session, destroy_session, get_session
from privguard.vault import VAULT_PATH, load_vault

app = FastAPI(title="PrivGuard API")


def _vault_path() -> Path:
    env = os.environ.get("PRIVGUARD_VAULT_PATH")
    return Path(env) if env else VAULT_PATH


class UnlockRequest(BaseModel):
    password: str


@app.post("/api/auth/unlock")
def unlock(body: UnlockRequest, response: Response):
    try:
        vault = load_vault(body.password, vault_path=_vault_path())
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    token = create_session(vault, body.password)
    response.set_cookie("session", token, httponly=True, samesite="strict")
    return {"status": "unlocked"}


@app.post("/api/auth/lock")
def lock(response: Response, session: Optional[str] = Cookie(default=None)):
    if session:
        destroy_session(session)
    response.delete_cookie("session")
    return {"status": "locked"}


@app.get("/api/users")
def list_users_stub(session_data: dict = __import__("fastapi").Depends(get_session)):
    return session_data["vault"].get("users", [])
```

Actually, I'm getting tangled. Let me write this cleanly. The `/api/users` stub is needed so the auth test `test_protected_route_without_cookie_returns_401` passes. I'll write a clean minimal app.py:

```python
"""PrivGuard FastAPI application.

This module is assembled incrementally across Tasks 4–9.
After Task 4 it contains only auth endpoints + a stub /api/users.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Annotated, Optional

from fastapi import Cookie, Depends, FastAPI, HTTPException, Response
from pydantic import BaseModel

from api.auth import create_session, destroy_session, get_session
from privguard.vault import VAULT_PATH, load_vault

app = FastAPI(title="PrivGuard API")


def _vault_path() -> Path:
    env = os.environ.get("PRIVGUARD_VAULT_PATH")
    return Path(env) if env else VAULT_PATH


class UnlockRequest(BaseModel):
    password: str


@app.post("/api/auth/unlock")
def unlock(body: UnlockRequest, response: Response):
    if not body.password:
        raise HTTPException(status_code=401, detail="Password must not be empty.")
    try:
        vault = load_vault(body.password, vault_path=_vault_path())
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    token = create_session(vault, body.password)
    response.set_cookie("session", token, httponly=True, samesite="strict")
    return {"status": "unlocked"}


@app.post("/api/auth/lock")
def lock(response: Response, session: Optional[str] = Cookie(default=None)):
    if session:
        destroy_session(session)
    response.delete_cookie("session")
    return {"status": "locked"}


@app.get("/api/users")
def list_users(session_data: dict = Depends(get_session)):
    return session_data["vault"].get("users", [])
```

- [ ] **Step 6: Run auth tests**

```bash
pytest tests/test_api_auth.py -v
```

Expected: all 6 PASSED

- [ ] **Step 7: Commit**

```bash
git add api/auth.py api/app.py tests/conftest_api.py tests/test_api_auth.py
git commit -m "feat: add session auth (unlock/lock) with httpOnly cookie"
```

---

## Task 5: Background job registry — `api/jobs.py`

**Files:**
- Create: `api/jobs.py`

No standalone tests — jobs.py is tested implicitly through the scan route tests in Task 7. Add a quick unit check here.

- [ ] **Step 1: Create `api/jobs.py`**

```python
"""Thread-safe job registry for long-running scan/submit tasks.

Each job gets a SimpleQueue (thread-safe) that scanner.py writes progress
events into. The SSE endpoint drains the queue asynchronously.
"""
from __future__ import annotations

import queue
import uuid
from typing import Optional


_jobs: dict[str, dict] = {}


def create_job() -> str:
    """Create a new job, return its ID."""
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {"q": queue.SimpleQueue(), "done": False}
    return job_id


def get_queue(job_id: str) -> Optional[queue.SimpleQueue]:
    """Return the job's SimpleQueue, or None if job_id is unknown."""
    job = _jobs.get(job_id)
    return job["q"] if job else None


def mark_done(job_id: str) -> None:
    """Mark job complete and push a sentinel 'done' event."""
    if job_id in _jobs:
        _jobs[job_id]["done"] = True
        _jobs[job_id]["q"].put({"type": "done"})


def is_done(job_id: str) -> bool:
    job = _jobs.get(job_id)
    return job["done"] if job else True
```

- [ ] **Step 2: Smoke-test in a Python shell**

```bash
python -c "
from api.jobs import create_job, get_queue, mark_done, is_done
jid = create_job()
q = get_queue(jid)
q.put({'type': 'progress', 'site': 'Whitepages', 'status': 'found'})
mark_done(jid)
print(q.get())
print(q.get())
print(is_done(jid))
"
```

Expected output:
```
{'type': 'progress', 'site': 'Whitepages', 'status': 'found'}
{'type': 'done'}
True
```

- [ ] **Step 3: Commit**

```bash
git add api/jobs.py
git commit -m "feat: add thread-safe job registry for SSE-backed background tasks"
```

---

## Task 6: User routes — `api/routes/users.py`

**Files:**
- Create: `api/routes/users.py`
- Create: `tests/test_api_users.py`

- [ ] **Step 1: Write failing tests at `tests/test_api_users.py`**

```python
"""Tests for GET/POST/DELETE /api/users."""
from __future__ import annotations


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
    import urllib.parse
    name = urllib.parse.quote("Alice Test")
    resp = auth_client.delete(f"/api/users/{name}")
    assert resp.status_code == 200
    resp2 = auth_client.get("/api/users")
    names = [u["display_name"] for u in resp2.json()]
    assert "Alice Test" not in names


def test_delete_nonexistent_user_returns_404(auth_client):
    resp = auth_client.delete("/api/users/Nobody%20Here")
    assert resp.status_code == 404
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_api_users.py -v
```

Expected: FAILED (routes don't exist yet beyond the stub)

- [ ] **Step 3: Create `api/routes/users.py`**

```python
"""User profile CRUD routes.

GET    /api/users           — list all profiles from in-memory vault
POST   /api/users           — add profile, re-save encrypted vault
DELETE /api/users/{name}    — remove profile by display_name, re-save vault
"""
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
```

- [ ] **Step 4: Register router in `api/app.py`**

Add to `api/app.py` (replace the stub `list_users` route and add the import):

```python
from api.routes.users import router as users_router
app.include_router(users_router)
```

And remove the inline `@app.get("/api/users")` stub from Task 4.

- [ ] **Step 5: Run tests**

```bash
pytest tests/test_api_users.py tests/test_api_auth.py -v
```

Expected: all PASSED

- [ ] **Step 6: Commit**

```bash
git add api/routes/users.py api/app.py tests/test_api_users.py
git commit -m "feat: add user CRUD routes (list, add, delete)"
```

---

## Task 7: Scan and submit routes — `api/routes/scan.py`

**Files:**
- Create: `api/routes/scan.py`
- Create: `tests/test_api_scan.py`

- [ ] **Step 1: Write failing tests at `tests/test_api_scan.py`**

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_api_scan.py -v
```

Expected: FAILED (404 or ImportError)

- [ ] **Step 3: Create `api/routes/scan.py`**

```python
"""Scan and submit routes.

POST /api/users/{name}/scan      — start scan background task, return job_id
POST /api/users/{name}/submit    — start submit background task, return job_id
GET  /api/jobs/{job_id}/stream   — SSE stream of progress events
"""
from __future__ import annotations

import asyncio
import json
import os
import queue
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from api.auth import get_session
from api.jobs import create_job, get_queue, mark_done
from privguard.db import DB_PATH
from privguard.scanner import scan_user
from privguard.submitter import submit_removals

router = APIRouter()

_executor = ThreadPoolExecutor(max_workers=4)


def _db_path() -> Path:
    env = os.environ.get("PRIVGUARD_DB_PATH")
    return Path(env) if env else DB_PATH


def _find_profile(vault: dict, name: str) -> dict:
    users = vault.get("users", [])
    for user in users:
        if user["display_name"] == name:
            return user
    raise HTTPException(status_code=404, detail=f"User '{name}' not found.")


class ScanRequest(BaseModel):
    source: Optional[str] = None
    force: bool = False


def _run_scan_in_background(job_id: str, profile: dict, api_keys: dict,
                             source: Optional[str], force: bool, db_path: Path) -> None:
    q = get_queue(job_id)
    try:
        scan_user(profile, api_keys=api_keys, source=source,
                  force=force, db_path=db_path,
                  progress_cb=lambda e: q.put(e) if q else None)
    finally:
        mark_done(job_id)


def _run_submit_in_background(job_id: str, profile: dict, force: bool, db_path: Path) -> None:
    q = get_queue(job_id)
    try:
        submit_removals(profile, force=force, db_path=db_path)
    finally:
        mark_done(job_id)


@router.post("/api/users/{name}/scan", status_code=202)
def start_scan(name: str, body: ScanRequest = ScanRequest(),
               session_data: dict = Depends(get_session)):
    profile = _find_profile(session_data["vault"], name)
    api_keys = session_data["vault"].get("api_keys", {})
    db_path = _db_path()

    job_id = create_job()
    _executor.submit(_run_scan_in_background, job_id, profile, api_keys,
                     body.source, body.force, db_path)
    return {"job_id": job_id}


@router.post("/api/users/{name}/submit", status_code=202)
def start_submit(name: str, body: ScanRequest = ScanRequest(),
                 session_data: dict = Depends(get_session)):
    profile = _find_profile(session_data["vault"], name)
    db_path = _db_path()

    job_id = create_job()
    _executor.submit(_run_submit_in_background, job_id, profile, body.force, db_path)
    return {"job_id": job_id}


@router.get("/api/jobs/{job_id}/stream")
async def stream_job(job_id: str, session_data: dict = Depends(get_session)):
    q = get_queue(job_id)
    if q is None:
        raise HTTPException(status_code=404, detail="Job not found.")

    async def event_generator():
        while True:
            try:
                event = q.get_nowait()
                yield f"data: {json.dumps(event)}\n\n"
                if event.get("type") == "done":
                    break
            except queue.Empty:
                yield ": keepalive\n\n"
                await asyncio.sleep(0.2)

    return StreamingResponse(event_generator(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache",
                                      "X-Accel-Buffering": "no"})
```

- [ ] **Step 4: Register router in `api/app.py`**

```python
from api.routes.scan import router as scan_router
app.include_router(scan_router)
```

- [ ] **Step 5: Run tests**

```bash
pytest tests/test_api_scan.py -v
```

Expected: all PASSED

- [ ] **Step 6: Commit**

```bash
git add api/routes/scan.py api/app.py tests/test_api_scan.py
git commit -m "feat: add scan/submit background task routes with SSE streaming"
```

---

## Task 8: Findings routes — `api/routes/findings.py`

**Files:**
- Create: `api/routes/findings.py`
- Create: `tests/test_api_findings.py`

- [ ] **Step 1: Write failing tests at `tests/test_api_findings.py`**

```python
"""Tests for GET /api/users/{name}/findings, GET /api/users/{name}/breaches,
PATCH /api/findings/{id}/status."""
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


def test_get_breaches_enriched_with_catalogue(auth_client, tmp_db, monkeypatch):
    from api import app as api_app
    api_app.app.state.breach_catalogue = {
        "TestBreach": {"Title": "Test Breach", "Domain": "test.com",
                       "LogoPath": "https://example.com/logo.png",
                       "Description": "A test breach."}
    }
    _seed_breach(tmp_db)
    resp = auth_client.get("/api/users/Alice%20Test/breaches")
    breaches = resp.json()
    match = next(b for b in breaches if b["breach_name"] == "TestBreach")
    assert "catalogue" in match
    assert match["catalogue"]["Domain"] == "test.com"


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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_api_findings.py -v
```

Expected: FAILED

- [ ] **Step 3: Create `api/routes/findings.py`**

```python
"""Findings and breaches read routes, plus status PATCH.

GET   /api/users/{name}/findings   — all findings for a user from SQLite
GET   /api/users/{name}/breaches   — all breaches, enriched with HIBP catalogue
PATCH /api/findings/{id}/status    — manually override a finding's status
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from api.auth import get_session
from privguard.db import DB_PATH, get_breaches, get_findings, update_finding_status

router = APIRouter()

_VALID_STATUSES = {
    "found", "not_found", "submitted", "pending_verification",
    "manual_required", "cleared",
}


def _db_path() -> Path:
    env = os.environ.get("PRIVGUARD_DB_PATH")
    return Path(env) if env else DB_PATH


@router.get("/api/users/{name}/findings")
def list_findings(name: str, session_data: dict = Depends(get_session)):
    return get_findings(user_display_name=name, db_path=_db_path())


@router.get("/api/users/{name}/breaches")
def list_breaches(name: str, request: Request, session_data: dict = Depends(get_session)):
    breaches = get_breaches(user_display_name=name, db_path=_db_path())
    catalogue: dict = getattr(request.app.state, "breach_catalogue", {})
    result = []
    for b in breaches:
        entry = dict(b)
        entry["catalogue"] = catalogue.get(b["breach_name"])
        result.append(entry)
    return result


class StatusUpdate(BaseModel):
    status: str

    def model_post_init(self, _):
        if self.status not in _VALID_STATUSES:
            raise ValueError(f"status must be one of {sorted(_VALID_STATUSES)}")


@router.patch("/api/findings/{finding_id}/status")
def patch_status(finding_id: int, body: StatusUpdate,
                 session_data: dict = Depends(get_session)):
    update_finding_status(finding_id, body.status, db_path=_db_path())
    return {"status": "updated", "finding_id": finding_id, "new_status": body.status}
```

- [ ] **Step 4: Register router in `api/app.py`**

```python
from api.routes.findings import router as findings_router
app.include_router(findings_router)
```

- [ ] **Step 5: Run tests**

```bash
pytest tests/test_api_findings.py -v
```

Expected: all PASSED

- [ ] **Step 6: Run full backend test suite**

```bash
pytest tests/ -v --ignore=tests/test_reporter.py
```

Expected: all PASSED (ignoring reporter which will be deleted in Task 10)

- [ ] **Step 7: Commit**

```bash
git add api/routes/findings.py api/app.py tests/test_api_findings.py
git commit -m "feat: add findings/breaches read routes and status PATCH endpoint"
```

---

## Task 9: Assemble `api/app.py` — startup, HIBP catalogue, CORS

**Files:**
- Modify: `api/app.py`

- [ ] **Step 1: Replace `api/app.py` with the full assembled version**

```python
"""PrivGuard FastAPI application — full assembly.

Routers registered:
  - auth (unlock / lock) — inline in this file
  - users  (GET/POST/DELETE /api/users)
  - scan   (POST scan/submit, GET SSE stream)
  - findings (GET findings/breaches, PATCH status)

On startup: fetch HIBP public breach catalogue and cache in app.state.
In production: serve compiled Next.js static files from web/out/.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import requests as http_requests
from fastapi import Cookie, Depends, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from api.auth import create_session, destroy_session, get_session
from api.routes.findings import router as findings_router
from api.routes.scan import router as scan_router
from api.routes.users import router as users_router
from privguard.vault import VAULT_PATH, load_vault

app = FastAPI(title="PrivGuard API", docs_url="/api/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users_router)
app.include_router(scan_router)
app.include_router(findings_router)


def _vault_path() -> Path:
    env = os.environ.get("PRIVGUARD_VAULT_PATH")
    return Path(env) if env else VAULT_PATH


def _db_path() -> Path:
    from privguard.db import DB_PATH
    env = os.environ.get("PRIVGUARD_DB_PATH")
    return Path(env) if env else DB_PATH


# ---------------------------------------------------------------------------
# Auth endpoints (inline — no separate router needed for 2 routes)
# ---------------------------------------------------------------------------

class UnlockRequest(BaseModel):
    password: str


@app.post("/api/auth/unlock")
def unlock(body: UnlockRequest, response: Response):
    if not body.password:
        raise HTTPException(status_code=401, detail="Password must not be empty.")
    try:
        vault = load_vault(body.password, vault_path=_vault_path())
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    token = create_session(vault, body.password)
    response.set_cookie("session", token, httponly=True, samesite="strict")
    return {"status": "unlocked"}


@app.post("/api/auth/lock")
def lock(response: Response, session: Optional[str] = Cookie(default=None)):
    if session:
        destroy_session(session)
    response.delete_cookie("session")
    return {"status": "locked"}


# ---------------------------------------------------------------------------
# Startup: cache HIBP public breach catalogue
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def _load_breach_catalogue() -> None:
    try:
        resp = http_requests.get(
            "https://haveibeenpwned.com/api/v3/breaches",
            timeout=10,
            headers={"user-agent": "PrivGuard/2.0"},
        )
        if resp.status_code == 200:
            app.state.breach_catalogue = {b["Name"]: b for b in resp.json()}
        else:
            app.state.breach_catalogue = {}
    except Exception:
        app.state.breach_catalogue = {}


# ---------------------------------------------------------------------------
# Static file serving (production: Next.js compiled output)
# ---------------------------------------------------------------------------

_STATIC_DIR = Path(__file__).parent.parent / "web" / "out"
if _STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(_STATIC_DIR), html=True), name="static")
```

- [ ] **Step 2: Run full test suite**

```bash
pytest tests/ -v --ignore=tests/test_reporter.py
```

Expected: all PASSED

- [ ] **Step 3: Verify API docs are available**

```bash
uvicorn api.app:app --port 8000 &
curl http://localhost:8000/api/docs
# ctrl+c to stop after checking
```

Expected: HTML response (FastAPI Swagger UI)

- [ ] **Step 4: Commit**

```bash
git add api/app.py
git commit -m "feat: assemble full FastAPI app with CORS, HIBP catalogue startup, static mount"
```

---

## Task 10: Serve entry point — `api/serve.py`

**Files:**
- Create: `api/serve.py`

- [ ] **Step 1: Create `api/serve.py`**

```python
"""Entry point for `privguard serve`.

Development mode  (default): starts uvicorn on :8000 and Next.js dev on :3000,
then opens http://localhost:3000 in the default browser.

Production mode (--prod): serves the compiled Next.js output via uvicorn only
on :8000 and opens http://localhost:8000. Run `npm run build` in web/ first.
"""
from __future__ import annotations

import subprocess
import sys
import time
import webbrowser
from pathlib import Path

_WEB_DIR = Path(__file__).parent.parent / "web"
_API_HOST = "127.0.0.1"
_API_PORT = 8000
_NEXT_PORT = 3000


def main() -> None:
    prod = "--prod" in sys.argv

    print("Starting PrivGuard...")

    api_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "api.app:app",
         "--host", _API_HOST, "--port", str(_API_PORT), "--reload"],
        cwd=str(Path(__file__).parent.parent),
    )

    if prod:
        time.sleep(1.5)
        url = f"http://localhost:{_API_PORT}"
        print(f"PrivGuard running at {url}")
        webbrowser.open(url)
        try:
            api_proc.wait()
        except KeyboardInterrupt:
            api_proc.terminate()
        return

    if not _WEB_DIR.exists():
        print(f"ERROR: web/ directory not found at {_WEB_DIR}. "
              "Run 'npm install' inside web/ first.", file=sys.stderr)
        api_proc.terminate()
        sys.exit(1)

    next_proc = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=str(_WEB_DIR),
        shell=sys.platform == "win32",
    )

    time.sleep(3)
    url = f"http://localhost:{_NEXT_PORT}"
    print(f"PrivGuard running at {url}")
    webbrowser.open(url)

    try:
        api_proc.wait()
    except KeyboardInterrupt:
        api_proc.terminate()
        next_proc.terminate()
```

- [ ] **Step 2: Verify the entry point is wired correctly**

```bash
pip install -e .
privguard --help
```

Expected: starts uvicorn (will show an error about web/ not existing, which is expected until the frontend is built)

- [ ] **Step 3: Commit**

```bash
git add api/serve.py
git commit -m "feat: add privguard serve entry point (uvicorn + Next.js launcher)"
```

---

## Task 11: Remove CLI and reporter, update CHANGELOG

**Files:**
- Delete: `privguard/main.py`
- Delete: `privguard/reporter.py`
- Delete: `tests/test_reporter.py`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Delete the CLI and reporter files**

```bash
git rm privguard/main.py privguard/reporter.py tests/test_reporter.py
```

- [ ] **Step 2: Run full test suite to confirm nothing breaks**

```bash
pytest tests/ -v
```

Expected: all remaining tests PASSED (reporter tests are gone)

- [ ] **Step 3: Update `CHANGELOG.md`** — add v2.0.0 section above v1.0.0:

```markdown
## [2.0.0] — 2026-06-17

Replaces the CLI and Excel reports with a local web dashboard.

### Added
- FastAPI backend (`api/`) wrapping all existing Python logic as REST/SSE endpoints
- Session auth via master password → httpOnly cookie (vault decrypted in memory)
- Live scan progress streamed to browser via Server-Sent Events
- `privguard serve` command launches uvicorn + Next.js dev server
- ~35 new broker entries: marketing databases, phone lookup, address lookup, mugshot/arrest sites
- 5 new social platforms: Instagram, TikTok, Reddit, YouTube, Pinterest
- Ad network opt-out source (`ad_networks`): NAI, DAA, Google Ads, Facebook Off-Site
- HIBP public breach catalogue enrichment (logos, descriptions, no API key required)
- Pwned Passwords checker (client-side, k-anonymity, no API key required)

### Removed
- `privguard/main.py` — CLI replaced by `privguard serve`
- `privguard/reporter.py` — Excel replaced by in-browser tables
```

- [ ] **Step 4: Commit**

```bash
git add CHANGELOG.md
git commit -m "chore: remove CLI and reporter modules, update changelog for v2.0.0"
```

---

## Self-Review Checklist

**Spec coverage:**
- [x] brokers.json expanded with marketing, phone lookup, address, mugshot categories — Task 1
- [x] scanner.py: 5 new social platforms — Task 2
- [x] scanner.py: `_scan_ad_networks()` with 4 sites + manual instructions — Task 2
- [x] scanner.py: `progress_cb` for SSE events — Task 2
- [x] FastAPI dependencies in pyproject.toml — Task 3
- [x] Session auth (unlock/lock, httpOnly cookie) — Task 4
- [x] In-memory sessions store vault + password — Task 4
- [x] Thread-safe job queue (SimpleQueue) — Task 5
- [x] User CRUD routes (list, add, delete) — Task 6
- [x] Scan and submit background task routes — Task 7
- [x] SSE job stream endpoint — Task 7
- [x] Findings and breaches read routes — Task 8
- [x] PATCH finding status — Task 8
- [x] HIBP breach catalogue enrichment on startup — Task 9
- [x] CORS for localhost:3000 — Task 9
- [x] `privguard serve` launcher (uvicorn + npm) — Task 10
- [x] Remove main.py, reporter.py, test_reporter.py — Task 11

**Placeholder scan:** None found.

**Type consistency:**
- `save_vault(password, vault_data, vault_path)` — matches vault.py signature (password first)
- `get_session()` returns `{"vault": dict, "password": str}` — consistent across all routes
- `_db_path()` helper defined identically in routes/scan.py and routes/findings.py — acceptable duplication for isolation

---

*Continue with `2026-06-17-privguard-v2-frontend.md` once all backend tests pass.*

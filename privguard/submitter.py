from __future__ import annotations

import random
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover
    sync_playwright = None  # type: ignore[assignment]

from privguard.db import (
    DB_PATH,
    get_findings,
    update_finding_status,
)
from privguard.scanner import load_brokers

SCREENSHOTS_DIR = Path.home() / ".privguard" / "screenshots"

_SKIP_STATUSES = {"submitted", "pending_verification", "cleared", "manual_required", "not_found"}
_SUCCESS_CODES = {200, 201, 302}


def submit_removals(
    profile: dict,
    force: bool = False,
    db_path: Path = DB_PATH,
) -> None:
    display_name = profile["display_name"]
    brokers_by_id: dict[str, dict] = {b["id"]: b for b in load_brokers()}

    findings = get_findings(user_display_name=display_name, db_path=db_path)

    for finding in findings:
        if not force and finding["status"] in _SKIP_STATUSES:
            continue

        site_id = finding.get("site_id", "")
        broker = brokers_by_id.get(site_id)
        if broker is None:
            continue

        method = broker.get("submission_method", "manual")

        if method == "post":
            _submit_post(finding, broker, profile, db_path=db_path)
        elif method == "playwright":
            _submit_playwright(finding, broker, profile, db_path=db_path)
        else:
            if finding["status"] != "manual_required":
                update_finding_status(finding["id"], "manual_required", db_path=db_path)

        time.sleep(random.uniform(2.0, 5.0))


def _replace_tokens(value: str, replacements: dict) -> str:
    def _sub(match: re.Match) -> str:
        key = match.group(1)
        return replacements.get(key, "")

    return re.sub(r"\{(\w+)\}", _sub, value)


def _build_form_data(broker: dict, profile: dict) -> dict:
    full_name = profile.get("full_name", profile.get("display_name", ""))
    name_parts = full_name.strip().split()
    first_name = name_parts[0] if name_parts else ""
    last_name = name_parts[-1] if len(name_parts) > 1 else ""

    emails = profile.get("emails", [])
    primary_email = emails[0] if emails else ""

    phones = profile.get("phone_numbers", [])
    phone = phones[0] if phones else ""

    addresses = profile.get("addresses", [])
    primary_address = next((a for a in addresses if a.get("current")), None)
    if primary_address is None and addresses:
        primary_address = addresses[0]

    street = primary_address["street"] if primary_address else ""
    city = primary_address["city"] if primary_address else ""
    state = primary_address["state"] if primary_address else ""
    zip_code = primary_address["zip"] if primary_address else ""

    replacements = {
        "first_name": first_name,
        "last_name": last_name,
        "full_name": full_name,
        "primary_email": primary_email,
        "street": street,
        "city": city,
        "state": state,
        "zip": zip_code,
        "dob": profile.get("date_of_birth", ""),
        "phone": phone,
    }

    return {
        field: _replace_tokens(template, replacements)
        for field, template in broker.get("form_fields", {}).items()
    }


def _submit_post(
    finding: dict,
    broker: dict,
    profile: dict,
    db_path: Path,
) -> None:
    url = broker.get("opt_out_url", "")
    form_data = _build_form_data(broker, profile)

    try:
        resp = requests.post(url, data=form_data, timeout=30)
        if resp.status_code in _SUCCESS_CODES:
            if broker.get("requires_email_verification"):
                new_status = "pending_verification"
            else:
                new_status = "submitted"
            update_finding_status(finding["id"], new_status, db_path=db_path)
    except Exception:
        pass


def _submit_playwright(
    finding: dict,
    broker: dict,
    profile: dict,
    db_path: Path,
) -> None:
    url = broker.get("opt_out_url", "")
    form_data = _build_form_data(broker, profile)

    safe_username = re.sub(r"[^\w]", "_", finding.get("user_display_name", "user"))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    screenshot_path = SCREENSHOTS_DIR / f"{broker['id']}_{safe_username}_{timestamp}.png"

    try:
        SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=30000)

            for field_name, value in form_data.items():
                try:
                    page.fill(f'[name="{field_name}"]', value)
                except Exception:
                    pass

            page.screenshot(path=str(screenshot_path))

            try:
                page.click('button[type="submit"]', timeout=5000)
            except Exception:
                try:
                    page.click('input[type="submit"]', timeout=5000)
                except Exception:
                    pass

            if broker.get("requires_email_verification"):
                new_status = "pending_verification"
            else:
                new_status = "submitted"

            update_finding_status(
                finding["id"],
                new_status,
                screenshot_path=str(screenshot_path),
                db_path=db_path,
            )
    except Exception:
        pass

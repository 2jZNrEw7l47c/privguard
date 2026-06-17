from __future__ import annotations

import json
import random
import re
import time
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
    upsert_breach,
    upsert_finding,
)

BROKERS_PATH = Path(__file__).parent.parent / "data" / "brokers.json"

_SKIP_STATUSES = {"submitted", "cleared", "pending_verification"}

_SOCIAL_SITES = [
    {
        "id": "facebook",
        "name": "Facebook",
        "search_url": "https://www.facebook.com/public/{name_slug}",
    },
    {
        "id": "linkedin",
        "name": "LinkedIn",
        "search_url": "https://www.linkedin.com/pub/dir/{first}/{last}",
    },
    {
        "id": "twitter_x",
        "name": "X (Twitter)",
        "search_url": "https://twitter.com/search?q={full_name}&f=user",
    },
]


def load_brokers() -> list[dict]:
    if not BROKERS_PATH.exists():
        raise FileNotFoundError(
            f"Broker list not found at {BROKERS_PATH}. "
            "Ensure data/brokers.json is present in the project directory."
        )
    with open(BROKERS_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


def scan_user(
    profile: dict,
    api_keys: dict,
    source: Optional[str] = None,
    force: bool = False,
    db_path: Path = DB_PATH,
) -> None:
    brokers = load_brokers()

    if source is None or source == "brokers":
        _scan_brokers(profile, brokers, force=force, db_path=db_path)
    if source is None or source == "hibp":
        _scan_hibp(profile, api_key=api_keys.get("hibp"), force=force, db_path=db_path)
    if source is None or source == "social":
        _scan_social(profile, force=force, db_path=db_path)
    if source is None or source == "search_engines":
        _scan_search_engines(profile, force=force, db_path=db_path)


def _scan_brokers(
    profile: dict,
    brokers: list[dict],
    force: bool,
    db_path: Path,
) -> None:
    display_name = profile["display_name"]

    existing: dict[str, str] = {
        f["site_id"]: f["status"]
        for f in get_findings(user_display_name=display_name, db_path=db_path)
        if f.get("source") == "brokers"
    }

    for broker in brokers:
        site_id = broker["id"]
        if not force and existing.get(site_id) in _SKIP_STATUSES:
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

        time.sleep(random.uniform(0.5, 1.5))


def _scan_hibp(
    profile: dict,
    api_key: Optional[str],
    force: bool,
    db_path: Path,
) -> None:
    if api_key is None:
        print("[PrivGuard] Skipping HIBP scan — no API key provided.")
        return

    display_name = profile["display_name"]

    for email in profile.get("emails", []):
        url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}"
        headers = {
            "hibp-api-key": api_key,
            "user-agent": "PrivGuard-CLI/1.0",
        }

        resp = requests.get(url, headers=headers, timeout=15)

        if resp.status_code == 429:
            time.sleep(6)
            resp = requests.get(url, headers=headers, timeout=15)

        if resp.status_code == 401:
            print("[PrivGuard] HIBP API key is invalid (401). Check your API key.")
            return

        if resp.status_code == 200:
            for breach in resp.json():
                upsert_breach(
                    user_display_name=display_name,
                    email=email,
                    breach_name=breach["Name"],
                    breach_date=breach.get("BreachDate", ""),
                    exposed_fields=", ".join(breach.get("DataClasses", [])),
                    hibp_url=f"https://haveibeenpwned.com/account/{email}",
                    db_path=db_path,
                )

        time.sleep(6)


def _scan_social(
    profile: dict,
    force: bool,
    db_path: Path,
) -> None:
    display_name = profile["display_name"]
    full_name = profile.get("full_name", display_name)
    parts = full_name.strip().split()
    first = parts[0] if parts else ""
    last = parts[-1] if len(parts) > 1 else ""
    name_slug = re.sub(r"\s+", "-", full_name.lower())

    existing: dict[str, str] = {
        f["site_id"]: f["status"]
        for f in get_findings(user_display_name=display_name, db_path=db_path)
        if f.get("source") == "social"
    }

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            page = browser.new_page()

            for site in _SOCIAL_SITES:
                site_id = site["id"]
                if not force and existing.get(site_id) in _SKIP_STATUSES:
                    continue

                url = (
                    site["search_url"]
                    .replace("{name_slug}", name_slug)
                    .replace("{first}", first)
                    .replace("{last}", last)
                    .replace("{full_name}", requests.utils.quote(full_name))
                )

                try:
                    page.goto(url, timeout=15000)
                    content = page.content()
                    status = "found" if full_name.lower() in content.lower() else "not_found"
                except Exception:
                    status = "not_found"

                upsert_finding(
                    user_display_name=display_name,
                    source="social",
                    site_id=site_id,
                    site_name=site["name"],
                    status=status,
                    opt_out_url=url,
                    db_path=db_path,
                )

                time.sleep(random.uniform(2.0, 4.0))
        finally:
            browser.close()


def _scan_search_engines(
    profile: dict,
    force: bool,
    db_path: Path,
) -> None:
    display_name = profile["display_name"]

    manual_sites = [
        {
            "id": "google_results_about_you",
            "name": "Google (Results About You)",
            "opt_out_url": "https://myaccount.google.com/personal-info",
            "instructions": (
                "1. Sign in to your Google account.\n"
                "2. Go to https://myaccount.google.com/personal-info\n"
                "3. Select 'Results about you' from the left sidebar.\n"
                "4. Review results and click 'Request removal' for any listings "
                "that contain your personal information.\n"
                "5. Follow on-screen prompts to complete each removal request."
            ),
        },
        {
            "id": "bing_content_removal",
            "name": "Bing (Content Removal)",
            "opt_out_url": "https://www.bing.com/webmaster/tools/contentremoval",
            "instructions": (
                "1. Sign in with a Microsoft account at "
                "https://www.bing.com/webmaster/tools/contentremoval\n"
                "2. Click 'Submit URL' and enter URLs that display your personal info.\n"
                "3. Select the removal reason 'Outdated cache' or 'Personal information'.\n"
                "4. Submit the request and monitor via the Bing Webmaster dashboard."
            ),
        },
    ]

    existing: dict[str, str] = {
        f["site_id"]: f["status"]
        for f in get_findings(user_display_name=display_name, db_path=db_path)
        if f.get("source") == "search_engines"
    }

    for site in manual_sites:
        if not force and existing.get(site["id"]) in _SKIP_STATUSES:
            continue

        upsert_finding(
            user_display_name=display_name,
            source="search_engines",
            site_id=site["id"],
            site_name=site["name"],
            status="manual_required",
            opt_out_url=site["opt_out_url"],
            manual_instructions=site["instructions"],
            db_path=db_path,
        )

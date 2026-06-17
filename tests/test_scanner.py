# tests/test_scanner.py
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, call
from privguard.db import init_db, get_findings, get_breaches
from privguard import scanner


SAMPLE_PROFILE = {
    "display_name": "John Smith",
    "full_name": "John Robert Smith",
    "aliases": ["Johnny Smith"],
    "date_of_birth": "1985-04-12",
    "emails": ["john@gmail.com", "jsmith@work.com"],
    "phone_numbers": ["+15555550101"],
    "addresses": [
        {"street": "123 Main St", "city": "Austin", "state": "TX", "zip": "78701", "current": True}
    ],
    "ssn_last4": "1234",
}

SAMPLE_BROKERS = [
    {
        "id": "whitepages",
        "name": "Whitepages",
        "category": "data_broker",
        "opt_out_url": "https://www.whitepages.com/suppression_requests/new",
        "submission_method": "playwright",
        "form_fields": {
            "first_name": "{first_name}",
            "last_name": "{last_name}",
            "state": "{state}",
            "email": "{primary_email}",
        },
        "requires_email_verification": True,
        "requires_id_verification": False,
        "manual_instructions": None,
    },
    {
        "id": "spokeo",
        "name": "Spokeo",
        "category": "data_broker",
        "opt_out_url": "https://www.spokeo.com/optout",
        "submission_method": "post",
        "form_fields": {"email": "{primary_email}", "first": "{first_name}", "last": "{last_name}"},
        "requires_email_verification": False,
        "requires_id_verification": False,
        "manual_instructions": None,
    },
]

SAMPLE_HIBP_RESPONSE = [
    {
        "Name": "Adobe",
        "BreachDate": "2013-10-04",
        "DataClasses": ["Email addresses", "Password hints", "Passwords", "Usernames"],
        "Domain": "adobe.com",
    }
]


class TestScanBrokers:
    def test_marks_found_when_head_returns_200(self, tmp_path):
        db = tmp_path / "test.db"
        init_db(db)
        mock_response = MagicMock()
        mock_response.status_code = 200
        with patch("privguard.scanner.requests.head", return_value=mock_response) as mock_head:
            with patch("privguard.scanner.time.sleep"):
                scanner._scan_brokers(SAMPLE_PROFILE, SAMPLE_BROKERS[:1], force=False, db_path=db)
        mock_head.assert_called_once_with(
            "https://www.whitepages.com/suppression_requests/new", timeout=10, allow_redirects=True
        )
        findings = get_findings(user_display_name="John Smith", db_path=db)
        assert len(findings) == 1
        assert findings[0]["status"] == "found"
        assert findings[0]["site_id"] == "whitepages"

    def test_marks_not_found_when_head_raises_exception(self, tmp_path):
        db = tmp_path / "test.db"
        init_db(db)
        with patch("privguard.scanner.requests.head", side_effect=Exception("connection error")):
            with patch("privguard.scanner.time.sleep"):
                scanner._scan_brokers(SAMPLE_PROFILE, SAMPLE_BROKERS[:1], force=False, db_path=db)
        findings = get_findings(user_display_name="John Smith", db_path=db)
        assert len(findings) == 1
        assert findings[0]["status"] == "not_found"

    def test_marks_not_found_when_head_returns_500(self, tmp_path):
        db = tmp_path / "test.db"
        init_db(db)
        mock_response = MagicMock()
        mock_response.status_code = 500
        with patch("privguard.scanner.requests.head", return_value=mock_response):
            with patch("privguard.scanner.time.sleep"):
                scanner._scan_brokers(SAMPLE_PROFILE, SAMPLE_BROKERS[:1], force=False, db_path=db)
        findings = get_findings(user_display_name="John Smith", db_path=db)
        assert findings[0]["status"] == "not_found"

    def test_skips_already_submitted_sites(self, tmp_path):
        db = tmp_path / "test.db"
        init_db(db)
        from privguard.db import upsert_finding
        upsert_finding(
            user_display_name="John Smith",
            source="brokers",
            site_id="whitepages",
            site_name="Whitepages",
            status="submitted",
            opt_out_url="https://www.whitepages.com/suppression_requests/new",
            db_path=db,
        )
        with patch("privguard.scanner.requests.head") as mock_head:
            with patch("privguard.scanner.time.sleep"):
                scanner._scan_brokers(SAMPLE_PROFILE, SAMPLE_BROKERS[:1], force=False, db_path=db)
        mock_head.assert_not_called()

    def test_force_rescans_submitted_sites(self, tmp_path):
        db = tmp_path / "test.db"
        init_db(db)
        from privguard.db import upsert_finding
        upsert_finding(
            user_display_name="John Smith",
            source="brokers",
            site_id="whitepages",
            site_name="Whitepages",
            status="submitted",
            opt_out_url="https://www.whitepages.com/suppression_requests/new",
            db_path=db,
        )
        mock_response = MagicMock()
        mock_response.status_code = 200
        with patch("privguard.scanner.requests.head", return_value=mock_response) as mock_head:
            with patch("privguard.scanner.time.sleep"):
                scanner._scan_brokers(SAMPLE_PROFILE, SAMPLE_BROKERS[:1], force=True, db_path=db)
        mock_head.assert_called_once()

    def test_marks_not_found_when_head_returns_404(self, tmp_path):
        db = tmp_path / "test.db"
        init_db(db)
        mock_response = MagicMock()
        mock_response.status_code = 404
        with patch("privguard.scanner.requests.head", return_value=mock_response):
            with patch("privguard.scanner.time.sleep"):
                scanner._scan_brokers(SAMPLE_PROFILE, SAMPLE_BROKERS[:1], force=False, db_path=db)
        findings = get_findings(user_display_name="John Smith", db_path=db)
        assert findings[0]["status"] == "not_found"


class TestScanHibp:
    def test_saves_breach_when_hibp_returns_200(self, tmp_path):
        db = tmp_path / "test.db"
        init_db(db)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = SAMPLE_HIBP_RESPONSE
        with patch("privguard.scanner.requests.get", return_value=mock_response):
            with patch("privguard.scanner.time.sleep"):
                scanner._scan_hibp(SAMPLE_PROFILE, api_key="test-key", force=False, db_path=db)
        breaches = get_breaches(user_display_name="John Smith", db_path=db)
        assert len(breaches) >= 1
        breach_names = [b["breach_name"] for b in breaches]
        assert "Adobe" in breach_names

    def test_saves_nothing_when_hibp_returns_404(self, tmp_path):
        db = tmp_path / "test.db"
        init_db(db)
        mock_response = MagicMock()
        mock_response.status_code = 404
        with patch("privguard.scanner.requests.get", return_value=mock_response):
            with patch("privguard.scanner.time.sleep"):
                scanner._scan_hibp(SAMPLE_PROFILE, api_key="test-key", force=False, db_path=db)
        breaches = get_breaches(user_display_name="John Smith", db_path=db)
        assert breaches == []

    def test_skips_gracefully_when_api_key_is_none(self, tmp_path, capsys):
        db = tmp_path / "test.db"
        init_db(db)
        with patch("privguard.scanner.requests.get") as mock_get:
            scanner._scan_hibp(SAMPLE_PROFILE, api_key=None, force=False, db_path=db)
        mock_get.assert_not_called()
        breaches = get_breaches(user_display_name="John Smith", db_path=db)
        assert breaches == []
        captured = capsys.readouterr()
        assert "skip" in captured.out.lower() or "hibp" in captured.out.lower()

    def test_retries_on_429(self, tmp_path):
        db = tmp_path / "test.db"
        init_db(db)
        rate_limit_response = MagicMock()
        rate_limit_response.status_code = 429
        ok_response = MagicMock()
        ok_response.status_code = 200
        ok_response.json.return_value = SAMPLE_HIBP_RESPONSE
        with patch(
            "privguard.scanner.requests.get", side_effect=[rate_limit_response, ok_response]
        ) as mock_get:
            with patch("privguard.scanner.time.sleep") as mock_sleep:
                scanner._scan_hibp(
                    {**SAMPLE_PROFILE, "emails": ["john@gmail.com"]},
                    api_key="test-key",
                    force=False,
                    db_path=db,
                )
        assert mock_get.call_count == 2
        mock_sleep.assert_any_call(6)

    def test_prints_warning_when_hibp_returns_401(self, tmp_path, capsys):
        db = tmp_path / "test.db"
        init_db(db)
        mock_response = MagicMock()
        mock_response.status_code = 401
        with patch("privguard.scanner.requests.get", return_value=mock_response):
            with patch("privguard.scanner.time.sleep"):
                scanner._scan_hibp(SAMPLE_PROFILE, api_key="bad-key", force=False, db_path=db)
        captured = capsys.readouterr()
        assert "401" in captured.out or "invalid" in captured.out.lower()


class TestScanSocial:
    def _make_playwright_mock(self, page_content: str):
        mock_page = MagicMock()
        mock_page.content.return_value = page_content
        mock_page.goto.return_value = None

        mock_browser = MagicMock()
        mock_browser.new_page.return_value = mock_page

        mock_pw = MagicMock()
        mock_pw.chromium.launch.return_value = mock_browser

        mock_context = MagicMock()
        mock_context.__enter__ = MagicMock(return_value=mock_pw)
        mock_context.__exit__ = MagicMock(return_value=False)

        return mock_context, mock_page, mock_browser

    def test_marks_found_when_name_in_page_content(self, tmp_path):
        db = tmp_path / "test.db"
        init_db(db)
        page_content = "<html><body>John Robert Smith profile page</body></html>"
        mock_ctx, _, _ = self._make_playwright_mock(page_content)

        with patch("privguard.scanner.sync_playwright", return_value=mock_ctx):
            with patch("privguard.scanner.time.sleep"):
                scanner._scan_social(SAMPLE_PROFILE, force=False, db_path=db)

        findings = get_findings(user_display_name="John Smith", db_path=db)
        social_findings = [f for f in findings if f["source"] == "social"]
        assert any(f["status"] == "found" for f in social_findings)

    def test_marks_not_found_when_name_not_in_page_content(self, tmp_path):
        db = tmp_path / "test.db"
        init_db(db)
        page_content = "<html><body>No results found</body></html>"
        mock_ctx, _, _ = self._make_playwright_mock(page_content)

        with patch("privguard.scanner.sync_playwright", return_value=mock_ctx):
            with patch("privguard.scanner.time.sleep"):
                scanner._scan_social(SAMPLE_PROFILE, force=False, db_path=db)

        findings = get_findings(user_display_name="John Smith", db_path=db)
        social_findings = [f for f in findings if f["source"] == "social"]
        assert all(f["status"] == "not_found" for f in social_findings)
        assert len(social_findings) == 3  # facebook, linkedin, twitter_x

    def test_marks_not_found_when_playwright_raises(self, tmp_path):
        db = tmp_path / "test.db"
        init_db(db)
        mock_page = MagicMock()
        mock_page.goto.side_effect = Exception("Timeout")

        mock_browser = MagicMock()
        mock_browser.new_page.return_value = mock_page

        mock_pw = MagicMock()
        mock_pw.chromium.launch.return_value = mock_browser

        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=mock_pw)
        mock_ctx.__exit__ = MagicMock(return_value=False)

        with patch("privguard.scanner.sync_playwright", return_value=mock_ctx):
            with patch("privguard.scanner.time.sleep"):
                scanner._scan_social(SAMPLE_PROFILE, force=False, db_path=db)

        findings = get_findings(user_display_name="John Smith", db_path=db)
        social_findings = [f for f in findings if f["source"] == "social"]
        assert all(f["status"] == "not_found" for f in social_findings)


class TestScanSearchEngines:
    def test_always_inserts_manual_required_for_google_and_bing(self, tmp_path):
        db = tmp_path / "test.db"
        init_db(db)
        scanner._scan_search_engines(SAMPLE_PROFILE, force=False, db_path=db)
        findings = get_findings(user_display_name="John Smith", db_path=db)
        se_findings = [f for f in findings if f["source"] == "search_engines"]
        assert len(se_findings) == 2
        assert all(f["status"] == "manual_required" for f in se_findings)
        site_ids = {f["site_id"] for f in se_findings}
        assert "google_results_about_you" in site_ids
        assert "bing_content_removal" in site_ids

    def test_manual_findings_include_instructions(self, tmp_path):
        db = tmp_path / "test.db"
        init_db(db)
        scanner._scan_search_engines(SAMPLE_PROFILE, force=False, db_path=db)
        findings = get_findings(user_display_name="John Smith", db_path=db)
        se_findings = {f["site_id"]: f for f in findings if f["source"] == "search_engines"}
        assert se_findings["google_results_about_you"]["manual_instructions"] is not None
        assert se_findings["bing_content_removal"]["manual_instructions"] is not None

    def test_search_engines_called_repeatedly_are_idempotent(self, tmp_path):
        db = tmp_path / "test.db"
        init_db(db)
        scanner._scan_search_engines(SAMPLE_PROFILE, force=False, db_path=db)
        scanner._scan_search_engines(SAMPLE_PROFILE, force=False, db_path=db)
        findings = get_findings(user_display_name="John Smith", db_path=db)
        se_findings = [f for f in findings if f["source"] == "search_engines"]
        assert len(se_findings) == 2


class TestLoadBrokers:
    def test_raises_friendly_error_when_brokers_json_missing(self, tmp_path):
        with patch("privguard.scanner.BROKERS_PATH", tmp_path / "nonexistent.json"):
            with pytest.raises(FileNotFoundError, match="Broker list not found"):
                scanner.load_brokers()

    def test_loads_all_44_brokers_from_real_file(self):
        brokers = scanner.load_brokers()
        assert len(brokers) == 44
        assert all("id" in b and "opt_out_url" in b for b in brokers)


class TestScanUser:
    def _patch_all_scans(self):
        return {
            "brokers": patch("privguard.scanner._scan_brokers"),
            "hibp": patch("privguard.scanner._scan_hibp"),
            "social": patch("privguard.scanner._scan_social"),
            "search": patch("privguard.scanner._scan_search_engines"),
        }

    def test_calls_all_four_scan_functions_when_source_is_none(self, tmp_path):
        db = tmp_path / "test.db"
        init_db(db)
        patches = self._patch_all_scans()
        with patch("privguard.scanner.load_brokers", return_value=SAMPLE_BROKERS):
            with patches["brokers"] as mb, patches["hibp"] as mh, \
                 patches["social"] as ms, patches["search"] as me:
                scanner.scan_user(
                    SAMPLE_PROFILE,
                    api_keys={"hibp": "test-key"},
                    source=None,
                    force=False,
                    db_path=db,
                )
        mb.assert_called_once()
        mh.assert_called_once()
        ms.assert_called_once()
        me.assert_called_once()

    def test_calls_only_scan_brokers_when_source_is_brokers(self, tmp_path):
        db = tmp_path / "test.db"
        init_db(db)
        patches = self._patch_all_scans()
        with patch("privguard.scanner.load_brokers", return_value=SAMPLE_BROKERS):
            with patches["brokers"] as mb, patches["hibp"] as mh, \
                 patches["social"] as ms, patches["search"] as me:
                scanner.scan_user(
                    SAMPLE_PROFILE,
                    api_keys={},
                    source="brokers",
                    force=False,
                    db_path=db,
                )
        mb.assert_called_once()
        mh.assert_not_called()
        ms.assert_not_called()
        me.assert_not_called()

    def test_calls_only_scan_hibp_when_source_is_hibp(self, tmp_path):
        db = tmp_path / "test.db"
        init_db(db)
        patches = self._patch_all_scans()
        with patch("privguard.scanner.load_brokers", return_value=SAMPLE_BROKERS):
            with patches["brokers"] as mb, patches["hibp"] as mh, \
                 patches["social"] as ms, patches["search"] as me:
                scanner.scan_user(
                    SAMPLE_PROFILE,
                    api_keys={"hibp": "key"},
                    source="hibp",
                    force=False,
                    db_path=db,
                )
        mb.assert_not_called()
        mh.assert_called_once()
        ms.assert_not_called()
        me.assert_not_called()

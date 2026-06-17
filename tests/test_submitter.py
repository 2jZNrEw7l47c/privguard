# tests/test_submitter.py
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, call
from privguard.db import init_db, get_findings, upsert_finding, update_finding_status
from privguard import submitter


SAMPLE_PROFILE = {
    "display_name": "Jane Doe",
    "full_name": "Jane Marie Doe",
    "aliases": [],
    "date_of_birth": "1990-07-22",
    "emails": ["jane@gmail.com", "jane@work.com"],
    "phone_numbers": ["+15559870101"],
    "addresses": [
        {"street": "456 Oak Ave", "city": "Denver", "state": "CO", "zip": "80201", "current": True},
        {"street": "789 Pine Rd", "city": "Boulder", "state": "CO", "zip": "80301", "current": False},
    ],
    "ssn_last4": "5678",
}

SAMPLE_BROKER_POST = {
    "id": "spokeo",
    "name": "Spokeo",
    "category": "data_broker",
    "opt_out_url": "https://www.spokeo.com/optout",
    "submission_method": "post",
    "form_fields": {
        "email": "{primary_email}",
        "first": "{first_name}",
        "last": "{last_name}",
        "state": "{state}",
        "address": "{street}",
        "city": "{city}",
        "zip": "{zip}",
        "dob": "{dob}",
        "phone": "{phone}",
        "full_name": "{full_name}",
    },
    "requires_email_verification": False,
    "requires_id_verification": False,
    "manual_instructions": None,
}

SAMPLE_BROKER_POST_EMAIL_VERIFY = {
    **SAMPLE_BROKER_POST,
    "id": "intelius",
    "name": "Intelius",
    "opt_out_url": "https://www.intelius.com/opt-out",
    "requires_email_verification": True,
}

SAMPLE_BROKER_PLAYWRIGHT = {
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
}


def _seed_finding(db, broker, status="found"):
    upsert_finding(
        user_display_name=SAMPLE_PROFILE["display_name"],
        source="brokers",
        site_id=broker["id"],
        site_name=broker["name"],
        status=status,
        opt_out_url=broker["opt_out_url"],
        db_path=db,
    )
    findings = get_findings(user_display_name=SAMPLE_PROFILE["display_name"], db_path=db)
    return next(f for f in findings if f["site_id"] == broker["id"])


class TestBuildFormData:
    def test_replaces_all_tokens_correctly(self):
        form_data = submitter._build_form_data(SAMPLE_BROKER_POST, SAMPLE_PROFILE)
        assert form_data["email"] == "jane@gmail.com"
        assert form_data["first"] == "Jane"
        assert form_data["last"] == "Doe"
        assert form_data["state"] == "CO"
        assert form_data["address"] == "456 Oak Ave"
        assert form_data["city"] == "Denver"
        assert form_data["zip"] == "80201"
        assert form_data["dob"] == "1990-07-22"
        assert form_data["phone"] == "+15559870101"
        assert form_data["full_name"] == "Jane Marie Doe"

    def test_uses_first_email_as_primary_email(self):
        form_data = submitter._build_form_data(SAMPLE_BROKER_POST, SAMPLE_PROFILE)
        assert form_data["email"] == "jane@gmail.com"

    def test_uses_current_address(self):
        form_data = submitter._build_form_data(SAMPLE_BROKER_POST, SAMPLE_PROFILE)
        assert form_data["address"] == "456 Oak Ave"
        assert form_data["city"] == "Denver"
        assert form_data["state"] == "CO"
        assert form_data["zip"] == "80201"

    def test_falls_back_to_first_address_when_no_current(self):
        profile_no_current = {
            **SAMPLE_PROFILE,
            "addresses": [
                {"street": "1 First St", "city": "Chicago", "state": "IL", "zip": "60601", "current": False},
                {"street": "2 Second St", "city": "Miami", "state": "FL", "zip": "33101", "current": False},
            ],
        }
        form_data = submitter._build_form_data(SAMPLE_BROKER_POST, profile_no_current)
        assert form_data["address"] == "1 First St"
        assert form_data["city"] == "Chicago"

    def test_empty_string_for_missing_token_data(self):
        profile_minimal = {
            "display_name": "Jane Doe",
            "full_name": "Jane Doe",
            "aliases": [],
            "date_of_birth": "",
            "emails": [],
            "phone_numbers": [],
            "addresses": [],
            "ssn_last4": "",
        }
        form_data = submitter._build_form_data(SAMPLE_BROKER_POST, profile_minimal)
        assert form_data["email"] == ""
        assert form_data["phone"] == ""
        assert form_data["address"] == ""


class TestReplaceTokens:
    def test_replaces_single_token(self):
        result = submitter._replace_tokens("{first_name}", {"first_name": "Alice"})
        assert result == "Alice"

    def test_replaces_multiple_tokens_in_one_value(self):
        result = submitter._replace_tokens(
            "{first_name} {last_name}", {"first_name": "Alice", "last_name": "Wonder"}
        )
        assert result == "Alice Wonder"

    def test_leaves_unknown_tokens_as_empty_string(self):
        result = submitter._replace_tokens("{unknown_token}", {"first_name": "Alice"})
        assert result == ""

    def test_passthrough_for_non_token_string(self):
        result = submitter._replace_tokens("plain value", {"first_name": "Alice"})
        assert result == "plain value"


class TestSubmitPost:
    def test_marks_submitted_on_200_without_email_verification(self, tmp_path):
        db = tmp_path / "test.db"
        init_db(db)
        finding = _seed_finding(db, SAMPLE_BROKER_POST)

        mock_response = MagicMock()
        mock_response.status_code = 200
        with patch("privguard.submitter.requests.post", return_value=mock_response):
            submitter._submit_post(finding, SAMPLE_BROKER_POST, SAMPLE_PROFILE, db_path=db)

        findings = get_findings(user_display_name="Jane Doe", db_path=db)
        updated = next(f for f in findings if f["site_id"] == "spokeo")
        assert updated["status"] == "submitted"

    def test_marks_pending_verification_on_200_with_email_verification(self, tmp_path):
        db = tmp_path / "test.db"
        init_db(db)
        finding = _seed_finding(db, SAMPLE_BROKER_POST_EMAIL_VERIFY)

        mock_response = MagicMock()
        mock_response.status_code = 200
        with patch("privguard.submitter.requests.post", return_value=mock_response):
            submitter._submit_post(
                finding, SAMPLE_BROKER_POST_EMAIL_VERIFY, SAMPLE_PROFILE, db_path=db
            )

        findings = get_findings(user_display_name="Jane Doe", db_path=db)
        updated = next(f for f in findings if f["site_id"] == "intelius")
        assert updated["status"] == "pending_verification"

    def test_marks_submitted_on_201(self, tmp_path):
        db = tmp_path / "test.db"
        init_db(db)
        finding = _seed_finding(db, SAMPLE_BROKER_POST)

        mock_response = MagicMock()
        mock_response.status_code = 201
        with patch("privguard.submitter.requests.post", return_value=mock_response):
            submitter._submit_post(finding, SAMPLE_BROKER_POST, SAMPLE_PROFILE, db_path=db)

        findings = get_findings(user_display_name="Jane Doe", db_path=db)
        updated = next(f for f in findings if f["site_id"] == "spokeo")
        assert updated["status"] == "submitted"

    def test_marks_submitted_on_302(self, tmp_path):
        db = tmp_path / "test.db"
        init_db(db)
        finding = _seed_finding(db, SAMPLE_BROKER_POST)

        mock_response = MagicMock()
        mock_response.status_code = 302
        with patch("privguard.submitter.requests.post", return_value=mock_response):
            submitter._submit_post(finding, SAMPLE_BROKER_POST, SAMPLE_PROFILE, db_path=db)

        findings = get_findings(user_display_name="Jane Doe", db_path=db)
        updated = next(f for f in findings if f["site_id"] == "spokeo")
        assert updated["status"] == "submitted"

    def test_leaves_status_as_found_when_request_raises_exception(self, tmp_path):
        db = tmp_path / "test.db"
        init_db(db)
        finding = _seed_finding(db, SAMPLE_BROKER_POST)

        with patch("privguard.submitter.requests.post", side_effect=Exception("Network error")):
            submitter._submit_post(finding, SAMPLE_BROKER_POST, SAMPLE_PROFILE, db_path=db)

        findings = get_findings(user_display_name="Jane Doe", db_path=db)
        updated = next(f for f in findings if f["site_id"] == "spokeo")
        assert updated["status"] == "found"

    def test_leaves_status_as_found_on_non_success_http_status(self, tmp_path):
        db = tmp_path / "test.db"
        init_db(db)
        finding = _seed_finding(db, SAMPLE_BROKER_POST)

        mock_response = MagicMock()
        mock_response.status_code = 500
        with patch("privguard.submitter.requests.post", return_value=mock_response):
            submitter._submit_post(finding, SAMPLE_BROKER_POST, SAMPLE_PROFILE, db_path=db)

        findings = get_findings(user_display_name="Jane Doe", db_path=db)
        updated = next(f for f in findings if f["site_id"] == "spokeo")
        assert updated["status"] == "found"


class TestSubmitPlaywright:
    def _make_playwright_mock(self):
        mock_page = MagicMock()
        mock_page.goto.return_value = None
        mock_page.fill.return_value = None
        mock_page.screenshot.return_value = None
        mock_page.click.return_value = None

        mock_browser = MagicMock()
        mock_browser.new_page.return_value = mock_page

        mock_pw = MagicMock()
        mock_pw.chromium.launch.return_value = mock_browser

        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=mock_pw)
        mock_ctx.__exit__ = MagicMock(return_value=False)

        return mock_ctx, mock_page, mock_browser

    def test_marks_submitted_and_saves_screenshot_path_on_success(self, tmp_path):
        db = tmp_path / "test.db"
        init_db(db)
        finding = _seed_finding(db, SAMPLE_BROKER_PLAYWRIGHT)

        mock_ctx, mock_page, _ = self._make_playwright_mock()

        screenshots_dir = tmp_path / "screenshots"
        with patch("privguard.submitter.sync_playwright", return_value=mock_ctx):
            with patch("privguard.submitter.SCREENSHOTS_DIR", screenshots_dir):
                submitter._submit_playwright(
                    finding, SAMPLE_BROKER_PLAYWRIGHT, SAMPLE_PROFILE, db_path=db
                )

        findings = get_findings(user_display_name="Jane Doe", db_path=db)
        updated = next(f for f in findings if f["site_id"] == "whitepages")
        assert updated["status"] == "pending_verification"
        assert updated["screenshot_path"] is not None
        assert "whitepages" in updated["screenshot_path"]

    def test_marks_submitted_when_no_email_verification_required(self, tmp_path):
        db = tmp_path / "test.db"
        init_db(db)
        broker_no_verify = {**SAMPLE_BROKER_PLAYWRIGHT, "requires_email_verification": False}
        finding = _seed_finding(db, broker_no_verify)

        mock_ctx, _, _ = self._make_playwright_mock()
        screenshots_dir = tmp_path / "screenshots"

        with patch("privguard.submitter.sync_playwright", return_value=mock_ctx):
            with patch("privguard.submitter.SCREENSHOTS_DIR", screenshots_dir):
                submitter._submit_playwright(
                    finding, broker_no_verify, SAMPLE_PROFILE, db_path=db
                )

        findings = get_findings(user_display_name="Jane Doe", db_path=db)
        updated = next(f for f in findings if f["site_id"] == "whitepages")
        assert updated["status"] == "submitted"

    def test_leaves_status_as_found_when_playwright_raises(self, tmp_path):
        db = tmp_path / "test.db"
        init_db(db)
        finding = _seed_finding(db, SAMPLE_BROKER_PLAYWRIGHT)

        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(side_effect=Exception("Browser launch failed"))
        mock_ctx.__exit__ = MagicMock(return_value=False)

        screenshots_dir = tmp_path / "screenshots"
        with patch("privguard.submitter.sync_playwright", return_value=mock_ctx):
            with patch("privguard.submitter.SCREENSHOTS_DIR", screenshots_dir):
                submitter._submit_playwright(
                    finding, SAMPLE_BROKER_PLAYWRIGHT, SAMPLE_PROFILE, db_path=db
                )

        findings = get_findings(user_display_name="Jane Doe", db_path=db)
        updated = next(f for f in findings if f["site_id"] == "whitepages")
        assert updated["status"] == "found"

    def test_leaves_status_as_found_when_goto_raises(self, tmp_path):
        db = tmp_path / "test.db"
        init_db(db)
        finding = _seed_finding(db, SAMPLE_BROKER_PLAYWRIGHT)

        mock_page = MagicMock()
        mock_page.goto.side_effect = Exception("Navigation timeout")

        mock_browser = MagicMock()
        mock_browser.new_page.return_value = mock_page

        mock_pw = MagicMock()
        mock_pw.chromium.launch.return_value = mock_browser

        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=mock_pw)
        mock_ctx.__exit__ = MagicMock(return_value=False)

        screenshots_dir = tmp_path / "screenshots"
        with patch("privguard.submitter.sync_playwright", return_value=mock_ctx):
            with patch("privguard.submitter.SCREENSHOTS_DIR", screenshots_dir):
                submitter._submit_playwright(
                    finding, SAMPLE_BROKER_PLAYWRIGHT, SAMPLE_PROFILE, db_path=db
                )

        findings = get_findings(user_display_name="Jane Doe", db_path=db)
        updated = next(f for f in findings if f["site_id"] == "whitepages")
        assert updated["status"] == "found"

    def test_screenshot_filename_contains_broker_id_and_timestamp(self, tmp_path):
        db = tmp_path / "test.db"
        init_db(db)
        finding = _seed_finding(db, SAMPLE_BROKER_PLAYWRIGHT)

        mock_ctx, mock_page, _ = self._make_playwright_mock()
        captured_path: list[str] = []

        def capture_screenshot(**kwargs):
            captured_path.append(kwargs.get("path", ""))
            return None

        mock_page.screenshot.side_effect = capture_screenshot
        screenshots_dir = tmp_path / "screenshots"

        with patch("privguard.submitter.sync_playwright", return_value=mock_ctx):
            with patch("privguard.submitter.SCREENSHOTS_DIR", screenshots_dir):
                submitter._submit_playwright(
                    finding, SAMPLE_BROKER_PLAYWRIGHT, SAMPLE_PROFILE, db_path=db
                )

        assert len(captured_path) == 1
        assert "whitepages" in captured_path[0]
        assert ".png" in captured_path[0]


class TestSubmitRemovals:
    def test_skips_findings_with_submitted_status_by_default(self, tmp_path):
        db = tmp_path / "test.db"
        init_db(db)
        _seed_finding(db, SAMPLE_BROKER_POST, status="submitted")

        with patch("privguard.submitter.load_brokers", return_value=[SAMPLE_BROKER_POST]):
            with patch("privguard.submitter._submit_post") as mock_post:
                with patch("privguard.submitter._submit_playwright") as mock_pw:
                    with patch("privguard.submitter.time.sleep"):
                        submitter.submit_removals(SAMPLE_PROFILE, force=False, db_path=db)

        mock_post.assert_not_called()
        mock_pw.assert_not_called()

    def test_skips_pending_verification_by_default(self, tmp_path):
        db = tmp_path / "test.db"
        init_db(db)
        _seed_finding(db, SAMPLE_BROKER_POST, status="pending_verification")

        with patch("privguard.submitter.load_brokers", return_value=[SAMPLE_BROKER_POST]):
            with patch("privguard.submitter._submit_post") as mock_post:
                with patch("privguard.submitter.time.sleep"):
                    submitter.submit_removals(SAMPLE_PROFILE, force=False, db_path=db)

        mock_post.assert_not_called()

    def test_skips_manual_required_by_default(self, tmp_path):
        db = tmp_path / "test.db"
        init_db(db)
        _seed_finding(db, SAMPLE_BROKER_POST, status="manual_required")

        with patch("privguard.submitter.load_brokers", return_value=[SAMPLE_BROKER_POST]):
            with patch("privguard.submitter._submit_post") as mock_post:
                with patch("privguard.submitter.time.sleep"):
                    submitter.submit_removals(SAMPLE_PROFILE, force=False, db_path=db)

        mock_post.assert_not_called()

    def test_skips_not_found_by_default(self, tmp_path):
        db = tmp_path / "test.db"
        init_db(db)
        _seed_finding(db, SAMPLE_BROKER_POST, status="not_found")

        with patch("privguard.submitter.load_brokers", return_value=[SAMPLE_BROKER_POST]):
            with patch("privguard.submitter._submit_post") as mock_post:
                with patch("privguard.submitter.time.sleep"):
                    submitter.submit_removals(SAMPLE_PROFILE, force=False, db_path=db)

        mock_post.assert_not_called()

    def test_processes_skipped_statuses_when_force_is_true(self, tmp_path):
        db = tmp_path / "test.db"
        init_db(db)
        _seed_finding(db, SAMPLE_BROKER_POST, status="submitted")

        with patch("privguard.submitter.load_brokers", return_value=[SAMPLE_BROKER_POST]):
            with patch("privguard.submitter._submit_post") as mock_post:
                with patch("privguard.submitter.time.sleep"):
                    submitter.submit_removals(SAMPLE_PROFILE, force=True, db_path=db)

        mock_post.assert_called_once()

    def test_dispatches_post_method_to_submit_post(self, tmp_path):
        db = tmp_path / "test.db"
        init_db(db)
        _seed_finding(db, SAMPLE_BROKER_POST, status="found")

        with patch("privguard.submitter.load_brokers", return_value=[SAMPLE_BROKER_POST]):
            with patch("privguard.submitter._submit_post") as mock_post:
                with patch("privguard.submitter.time.sleep"):
                    submitter.submit_removals(SAMPLE_PROFILE, force=False, db_path=db)

        mock_post.assert_called_once()

    def test_dispatches_playwright_method_to_submit_playwright(self, tmp_path):
        db = tmp_path / "test.db"
        init_db(db)
        _seed_finding(db, SAMPLE_BROKER_PLAYWRIGHT, status="found")

        with patch("privguard.submitter.load_brokers", return_value=[SAMPLE_BROKER_PLAYWRIGHT]):
            with patch("privguard.submitter._submit_playwright") as mock_pw:
                with patch("privguard.submitter.time.sleep"):
                    submitter.submit_removals(SAMPLE_PROFILE, force=False, db_path=db)

        mock_pw.assert_called_once()

    def test_marks_manual_required_for_manual_submission_method(self, tmp_path):
        db = tmp_path / "test.db"
        init_db(db)
        manual_broker = {
            **SAMPLE_BROKER_POST,
            "id": "manual_site",
            "name": "Manual Site",
            "submission_method": "manual",
            "manual_instructions": "Call 1-800-555-0100 to opt out.",
        }
        _seed_finding(db, manual_broker, status="found")

        with patch("privguard.submitter.load_brokers", return_value=[manual_broker]):
            with patch("privguard.submitter.time.sleep"):
                submitter.submit_removals(SAMPLE_PROFILE, force=False, db_path=db)

        findings = get_findings(user_display_name="Jane Doe", db_path=db)
        updated = next(f for f in findings if f["site_id"] == "manual_site")
        assert updated["status"] == "manual_required"

    def test_skips_findings_with_no_broker_config(self, tmp_path):
        db = tmp_path / "test.db"
        init_db(db)
        _seed_finding(db, SAMPLE_BROKER_POST, status="found")

        with patch("privguard.submitter.load_brokers", return_value=[]):
            with patch("privguard.submitter._submit_post") as mock_post:
                with patch("privguard.submitter.time.sleep"):
                    submitter.submit_removals(SAMPLE_PROFILE, force=False, db_path=db)

        mock_post.assert_not_called()

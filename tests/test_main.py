# tests/test_main.py
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from privguard.main import cli

EMPTY_VAULT = {"users": [], "api_keys": {}}

ONE_USER_VAULT = {
    "users": [
        {
            "display_name": "Alice Doe",
            "full_name": "Alice Marie Doe",
            "aliases": [],
            "date_of_birth": "1990-01-15",
            "emails": ["alice@example.com"],
            "phone_numbers": ["+15550001111"],
            "addresses": [
                {
                    "street": "1 Test Ave",
                    "city": "Austin",
                    "state": "TX",
                    "zip": "78701",
                    "current": True,
                }
            ],
            "ssn_last4": None,
        }
    ],
    "api_keys": {"hibp": "test-hibp-key"},
}

TWO_USER_VAULT = {
    "users": [
        {
            "display_name": "Alice Doe",
            "full_name": "Alice Marie Doe",
            "aliases": [],
            "date_of_birth": "1990-01-15",
            "emails": ["alice@example.com"],
            "phone_numbers": [],
            "addresses": [],
            "ssn_last4": None,
        },
        {
            "display_name": "Bob Smith",
            "full_name": "Robert Smith",
            "aliases": ["Bobby"],
            "date_of_birth": "1985-06-20",
            "emails": ["bob@example.com", "bob.work@example.com"],
            "phone_numbers": ["+15559998888"],
            "addresses": [
                {
                    "street": "99 Elm St",
                    "city": "Dallas",
                    "state": "TX",
                    "zip": "75201",
                    "current": True,
                }
            ],
            "ssn_last4": "5678",
        },
    ],
    "api_keys": {"hibp": "test-hibp-key"},
}


class TestInit:
    def test_init_creates_vault_file(self, tmp_path):
        vault_path = tmp_path / ".privguard" / "vault.enc"
        db_path = tmp_path / ".privguard" / "privguard.db"

        with (
            patch("privguard.main.VAULT_PATH", vault_path),
            patch("privguard.main.DB_PATH", db_path),
            patch("privguard.main.save_vault") as mock_save,
            patch("privguard.main.init_db") as mock_init_db,
        ):
            runner = CliRunner()
            result = runner.invoke(cli, ["init"], input="secret\nsecret\n")

        assert result.exit_code == 0, result.output
        mock_save.assert_called_once_with("secret", EMPTY_VAULT, vault_path)
        mock_init_db.assert_called_once_with(db_path)
        assert "privguard initialized" in result.output.lower()
        assert "privguard user add" in result.output

    def test_init_when_vault_exists_prints_error_and_does_not_overwrite(self, tmp_path):
        vault_path = tmp_path / ".privguard" / "vault.enc"
        vault_path.parent.mkdir(parents=True)
        vault_path.touch()

        with (
            patch("privguard.main.VAULT_PATH", vault_path),
            patch("privguard.main.save_vault") as mock_save,
            patch("privguard.main.init_db") as mock_init_db,
        ):
            runner = CliRunner()
            result = runner.invoke(cli, ["init"], input="secret\nsecret\n")

        assert result.exit_code != 0 or "already exists" in result.output.lower()
        mock_save.assert_not_called()
        mock_init_db.assert_not_called()

    def test_init_mismatched_passwords_fails(self, tmp_path):
        vault_path = tmp_path / ".privguard" / "vault.enc"

        with (
            patch("privguard.main.VAULT_PATH", vault_path),
            patch("privguard.main.save_vault") as mock_save,
        ):
            runner = CliRunner()
            result = runner.invoke(
                cli,
                ["init"],
                input="secret1\nsecret2\nsecret1\nsecret2\nsecret1\nsecret2\n",
            )

        assert result.exit_code != 0 or "error" in result.output.lower()
        mock_save.assert_not_called()


class TestUserAdd:
    def _invoke_user_add(self, tmp_path, initial_vault=None, extra_input=""):
        vault_path = tmp_path / "vault.enc"

        if initial_vault is None:
            initial_vault = dict(EMPTY_VAULT)

        saved = {}

        def fake_load(password, path):
            if password != "secret":
                raise ValueError("wrong password")
            return json.loads(json.dumps(initial_vault))

        def fake_save(password, data, path):
            saved["data"] = json.loads(json.dumps(data))

        user_input = (
            "secret\n"
            "Alice Doe\n"
            "Alice Marie Doe\n"
            "1990-01-15\n"
            "alice@example.com\n"
            "\n"
            "+15550001111\n"
            "\n"
            "1 Test Ave\n"
            "Austin\n"
            "TX\n"
            "78701\n"
            "y\n"
            "\n"
            "\n"
            "\n"
            "test-hibp-key\n"
            + extra_input
        )

        with (
            patch("privguard.main.VAULT_PATH", vault_path),
            patch("privguard.main.load_vault", side_effect=fake_load),
            patch("privguard.main.save_vault", side_effect=fake_save),
        ):
            runner = CliRunner()
            result = runner.invoke(cli, ["user", "add"], input=user_input)

        return result, saved

    def test_user_add_appends_profile_to_vault(self, tmp_path):
        result, saved = self._invoke_user_add(tmp_path)

        assert result.exit_code == 0, result.output
        assert len(saved["data"]["users"]) == 1
        user = saved["data"]["users"][0]
        assert user["display_name"] == "Alice Doe"
        assert user["full_name"] == "Alice Marie Doe"
        assert user["date_of_birth"] == "1990-01-15"
        assert "alice@example.com" in user["emails"]
        assert "+15550001111" in user["phone_numbers"]
        assert user["addresses"][0]["street"] == "1 Test Ave"
        assert user["ssn_last4"] is None

    def test_user_add_stores_hibp_key_when_not_present(self, tmp_path):
        result, saved = self._invoke_user_add(tmp_path, initial_vault=EMPTY_VAULT)

        assert result.exit_code == 0, result.output
        assert saved["data"]["api_keys"].get("hibp") == "test-hibp-key"

    def test_user_add_does_not_overwrite_existing_hibp_key(self, tmp_path):
        vault_with_key = {
            "users": [],
            "api_keys": {"hibp": "existing-key"},
        }
        user_input = (
            "secret\n"
            "Alice Doe\n"
            "Alice Marie Doe\n"
            "1990-01-15\n"
            "alice@example.com\n"
            "\n"
            "+15550001111\n"
            "\n"
            "1 Test Ave\n"
            "Austin\n"
            "TX\n"
            "78701\n"
            "y\n"
            "\n"
            "\n"
            "\n"
        )
        vault_path = tmp_path / "vault.enc"
        saved = {}

        def fake_save(password, data, path):
            saved["data"] = json.loads(json.dumps(data))

        with (
            patch("privguard.main.VAULT_PATH", vault_path),
            patch("privguard.main.load_vault", return_value=json.loads(json.dumps(vault_with_key))),
            patch("privguard.main.save_vault", side_effect=fake_save),
        ):
            runner = CliRunner()
            result = runner.invoke(cli, ["user", "add"], input=user_input)

        assert result.exit_code == 0, result.output
        assert saved["data"]["api_keys"]["hibp"] == "existing-key"


class TestUserList:
    def test_user_list_prints_all_display_names(self, tmp_path):
        vault_path = tmp_path / "vault.enc"
        with (
            patch("privguard.main.VAULT_PATH", vault_path),
            patch("privguard.main.load_vault", return_value=json.loads(json.dumps(TWO_USER_VAULT))),
        ):
            runner = CliRunner()
            result = runner.invoke(cli, ["user", "list"], input="secret\n")

        assert result.exit_code == 0, result.output
        assert "Alice Doe" in result.output
        assert "Bob Smith" in result.output

    def test_user_list_shows_email_and_address_counts(self, tmp_path):
        vault_path = tmp_path / "vault.enc"
        with (
            patch("privguard.main.VAULT_PATH", vault_path),
            patch("privguard.main.load_vault", return_value=json.loads(json.dumps(TWO_USER_VAULT))),
        ):
            runner = CliRunner()
            result = runner.invoke(cli, ["user", "list"], input="secret\n")

        assert "2" in result.output
        assert "1" in result.output

    def test_user_list_empty_vault_shows_no_profiles(self, tmp_path):
        vault_path = tmp_path / "vault.enc"
        with (
            patch("privguard.main.VAULT_PATH", vault_path),
            patch("privguard.main.load_vault", return_value=json.loads(json.dumps(EMPTY_VAULT))),
        ):
            runner = CliRunner()
            result = runner.invoke(cli, ["user", "list"], input="secret\n")

        assert result.exit_code == 0, result.output
        assert "no profiles" in result.output.lower()


class TestUserRemove:
    def test_user_remove_deletes_profile_by_display_name(self, tmp_path):
        vault_path = tmp_path / "vault.enc"
        saved = {}

        def fake_save(password, data, path):
            saved["data"] = json.loads(json.dumps(data))

        with (
            patch("privguard.main.VAULT_PATH", vault_path),
            patch("privguard.main.load_vault", return_value=json.loads(json.dumps(TWO_USER_VAULT))),
            patch("privguard.main.save_vault", side_effect=fake_save),
        ):
            runner = CliRunner()
            result = runner.invoke(cli, ["user", "remove", "--user", "Alice Doe"], input="secret\n")

        assert result.exit_code == 0, result.output
        names = [u["display_name"] for u in saved["data"]["users"]]
        assert "Alice Doe" not in names
        assert "Bob Smith" in names

    def test_user_remove_unknown_name_prints_error(self, tmp_path):
        vault_path = tmp_path / "vault.enc"

        with (
            patch("privguard.main.VAULT_PATH", vault_path),
            patch("privguard.main.load_vault", return_value=json.loads(json.dumps(TWO_USER_VAULT))),
            patch("privguard.main.save_vault") as mock_save,
        ):
            runner = CliRunner()
            result = runner.invoke(cli, ["user", "remove", "--user", "Nobody Here"], input="secret\n")

        assert "not found" in result.output.lower() or result.exit_code != 0
        mock_save.assert_not_called()


class TestScan:
    def _invoke_scan(self, tmp_path, vault, args=None, password="secret"):
        vault_path = tmp_path / "vault.enc"
        args = args or []

        with (
            patch("privguard.main.VAULT_PATH", vault_path),
            patch("privguard.main.load_vault", return_value=json.loads(json.dumps(vault))),
            patch("privguard.main.scan_user") as mock_scan,
        ):
            runner = CliRunner()
            result = runner.invoke(cli, ["scan"] + args, input=f"{password}\n")
            return result, mock_scan

    def test_scan_calls_scan_user_for_all_users(self, tmp_path):
        result, mock_scan = self._invoke_scan(tmp_path, TWO_USER_VAULT)

        assert result.exit_code == 0, result.output
        assert mock_scan.call_count == 2

    def test_scan_user_flag_calls_only_that_user(self, tmp_path):
        result, mock_scan = self._invoke_scan(tmp_path, TWO_USER_VAULT, args=["--user", "Alice Doe"])

        assert result.exit_code == 0, result.output
        assert mock_scan.call_count == 1
        called_profile = mock_scan.call_args[0][0]
        assert called_profile["display_name"] == "Alice Doe"

    def test_scan_unknown_user_prints_error_and_does_not_call_scan(self, tmp_path):
        result, mock_scan = self._invoke_scan(tmp_path, TWO_USER_VAULT, args=["--user", "Ghost User"])

        assert "not found" in result.output.lower() or result.exit_code != 0
        mock_scan.assert_not_called()

    def test_scan_source_flag_passes_source_to_scan_user(self, tmp_path):
        result, mock_scan = self._invoke_scan(tmp_path, ONE_USER_VAULT, args=["--source", "brokers"])

        assert result.exit_code == 0, result.output
        _, kwargs = mock_scan.call_args
        assert kwargs.get("source") == "brokers"

    def test_scan_force_flag_passes_force_true_to_scan_user(self, tmp_path):
        result, mock_scan = self._invoke_scan(tmp_path, ONE_USER_VAULT, args=["--force"])

        assert result.exit_code == 0, result.output
        call_kwargs = mock_scan.call_args[1]
        assert call_kwargs.get("force") is True

    def test_scan_prints_scanning_message_per_user(self, tmp_path):
        result, _ = self._invoke_scan(tmp_path, TWO_USER_VAULT)

        assert "Scanning: Alice Doe" in result.output
        assert "Scanning: Bob Smith" in result.output

    def test_scan_prints_scan_complete(self, tmp_path):
        result, _ = self._invoke_scan(tmp_path, ONE_USER_VAULT)

        assert "Scan complete" in result.output

    def test_scan_empty_vault_prints_error(self, tmp_path):
        result, mock_scan = self._invoke_scan(tmp_path, EMPTY_VAULT)
        assert result.exit_code != 0 or "no profiles" in result.output.lower()
        mock_scan.assert_not_called()


class TestSubmit:
    def _invoke_submit(self, tmp_path, vault, args=None, password="secret"):
        vault_path = tmp_path / "vault.enc"
        args = args or []

        with (
            patch("privguard.main.VAULT_PATH", vault_path),
            patch("privguard.main.load_vault", return_value=json.loads(json.dumps(vault))),
            patch("privguard.main.submit_removals") as mock_submit,
        ):
            runner = CliRunner()
            result = runner.invoke(cli, ["submit"] + args, input=f"{password}\n")
            return result, mock_submit

    def test_submit_calls_submit_removals_for_all_users(self, tmp_path):
        result, mock_submit = self._invoke_submit(tmp_path, TWO_USER_VAULT)

        assert result.exit_code == 0, result.output
        assert mock_submit.call_count == 2

    def test_submit_force_flag_passes_force_true(self, tmp_path):
        result, mock_submit = self._invoke_submit(tmp_path, ONE_USER_VAULT, args=["--force"])

        assert result.exit_code == 0, result.output
        call_kwargs = mock_submit.call_args[1]
        assert call_kwargs.get("force") is True

    def test_submit_user_flag_calls_only_that_user(self, tmp_path):
        result, mock_submit = self._invoke_submit(tmp_path, TWO_USER_VAULT, args=["--user", "Bob Smith"])

        assert result.exit_code == 0, result.output
        assert mock_submit.call_count == 1
        called_profile = mock_submit.call_args[0][0]
        assert called_profile["display_name"] == "Bob Smith"

    def test_submit_prints_submitting_message_per_user(self, tmp_path):
        result, _ = self._invoke_submit(tmp_path, TWO_USER_VAULT)

        assert "Submitting removals for: Alice Doe" in result.output
        assert "Submitting removals for: Bob Smith" in result.output

    def test_submit_prints_submissions_complete(self, tmp_path):
        result, _ = self._invoke_submit(tmp_path, ONE_USER_VAULT)

        assert "Submissions complete" in result.output


class TestReport:
    def _invoke_report(self, tmp_path, vault, args=None, password="secret"):
        vault_path = tmp_path / "vault.enc"
        args = args or []
        fake_report_path = tmp_path / "report.xlsx"

        with (
            patch("privguard.main.VAULT_PATH", vault_path),
            patch("privguard.main.load_vault", return_value=json.loads(json.dumps(vault))),
            patch("privguard.main.generate_report", return_value=fake_report_path) as mock_report,
        ):
            runner = CliRunner()
            result = runner.invoke(cli, ["report"] + args, input=f"{password}\n")
            return result, mock_report, fake_report_path

    def test_report_calls_generate_report_for_all_users(self, tmp_path):
        result, mock_report, _ = self._invoke_report(tmp_path, TWO_USER_VAULT)

        assert result.exit_code == 0, result.output
        assert mock_report.call_count == 2

    def test_report_prints_saved_path(self, tmp_path):
        result, _, fake_path = self._invoke_report(tmp_path, ONE_USER_VAULT)

        assert str(fake_path) in result.output

    def test_report_user_flag_calls_only_that_user(self, tmp_path):
        result, mock_report, _ = self._invoke_report(tmp_path, TWO_USER_VAULT, args=["--user", "Alice Doe"])

        assert result.exit_code == 0, result.output
        assert mock_report.call_count == 1
        called_profile = mock_report.call_args[0][0]
        assert called_profile["display_name"] == "Alice Doe"

    def test_report_output_flag_passes_custom_output_dir(self, tmp_path):
        custom_dir = tmp_path / "custom_reports"
        result, mock_report, _ = self._invoke_report(
            tmp_path, ONE_USER_VAULT, args=["--output", str(custom_dir)]
        )

        assert result.exit_code == 0, result.output
        called_output_dir = mock_report.call_args[0][1]
        assert Path(called_output_dir) == custom_dir

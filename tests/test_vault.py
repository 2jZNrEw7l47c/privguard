"""Tests for privguard/vault.py — encrypted PII storage."""
import re
from pathlib import Path

import pytest

from privguard.vault import load_vault, save_vault

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_VAULT = {
    "users": [
        {
            "display_name": "John Smith",
            "full_name": "John Robert Smith",
            "aliases": ["Johnny Smith"],
            "date_of_birth": "1985-04-12",
            "emails": ["john@gmail.com"],
            "phone_numbers": ["+15555550101"],
            "addresses": [
                {
                    "street": "123 Main St",
                    "city": "Austin",
                    "state": "TX",
                    "zip": "78701",
                    "current": True,
                }
            ],
            "ssn_last4": "1234",
        }
    ],
    "api_keys": {"hibp": "test-hibp-key-abc123"},
}


# ---------------------------------------------------------------------------
# Round-trip
# ---------------------------------------------------------------------------

def test_save_and_load_round_trip(tmp_path):
    """save_vault followed by load_vault must return an identical dict."""
    vault_file = tmp_path / "vault.enc"
    password = "correct-horse-battery-staple"

    save_vault(password=password, vault_data=SAMPLE_VAULT, vault_path=vault_file)
    loaded = load_vault(password=password, vault_path=vault_file)

    assert loaded == SAMPLE_VAULT


def test_round_trip_preserves_nested_structure(tmp_path):
    """Nested lists and dicts must survive the round-trip intact."""
    vault_file = tmp_path / "vault.enc"
    password = "s3cr3t!"

    save_vault(password=password, vault_data=SAMPLE_VAULT, vault_path=vault_file)
    loaded = load_vault(password=password, vault_path=vault_file)

    user = loaded["users"][0]
    assert user["aliases"] == ["Johnny Smith"]
    assert user["addresses"][0]["city"] == "Austin"
    assert loaded["api_keys"]["hibp"] == "test-hibp-key-abc123"


# ---------------------------------------------------------------------------
# Wrong password
# ---------------------------------------------------------------------------

def test_wrong_password_raises_value_error(tmp_path):
    """load_vault with a wrong password must raise ValueError."""
    vault_file = tmp_path / "vault.enc"
    save_vault(password="correct", vault_data=SAMPLE_VAULT, vault_path=vault_file)

    with pytest.raises(ValueError):
        load_vault(password="wrong", vault_path=vault_file)


def test_wrong_password_error_message(tmp_path):
    """The ValueError message must match the documented string exactly."""
    vault_file = tmp_path / "vault.enc"
    save_vault(password="correct", vault_data=SAMPLE_VAULT, vault_path=vault_file)

    with pytest.raises(ValueError, match=re.escape("Invalid master password or corrupted vault.")):
        load_vault(password="wrong", vault_path=vault_file)


# ---------------------------------------------------------------------------
# Empty password validation
# ---------------------------------------------------------------------------

def test_save_vault_empty_password_raises(tmp_path):
    """save_vault must raise ValueError when password is empty."""
    vault_file = tmp_path / "vault.enc"

    with pytest.raises(ValueError, match="Master password must not be empty"):
        save_vault(password="", vault_data={"users": []}, vault_path=vault_file)


def test_load_vault_empty_password_raises(tmp_path):
    """load_vault must raise ValueError when password is empty."""
    vault_file = tmp_path / "vault.enc"
    save_vault(password="real-password", vault_data={"users": []}, vault_path=vault_file)

    with pytest.raises(ValueError, match="Master password must not be empty"):
        load_vault(password="", vault_path=vault_file)


# ---------------------------------------------------------------------------
# Truncated file detection
# ---------------------------------------------------------------------------

def test_truncated_file_raises_corruption_error(tmp_path):
    """load_vault must raise ValueError for a file that is too short to be valid."""
    vault_file = tmp_path / "vault.enc"
    # Write fewer bytes than _SALT_SIZE (16) so the truncation guard fires.
    vault_file.write_bytes(b"\x00" * 10)

    with pytest.raises(ValueError, match=re.escape("Vault file is truncated or empty")):
        load_vault(password="any-password", vault_path=vault_file)


def test_exactly_salt_size_file_raises_corruption_error(tmp_path):
    """load_vault must reject a file that is exactly _SALT_SIZE bytes (no ciphertext)."""
    vault_file = tmp_path / "vault.enc"
    vault_file.write_bytes(b"\x00" * 16)

    with pytest.raises(ValueError, match=re.escape("Vault file is truncated or empty")):
        load_vault(password="any-password", vault_path=vault_file)


# ---------------------------------------------------------------------------
# No plaintext PII in vault file
# ---------------------------------------------------------------------------

def test_vault_file_does_not_contain_plaintext_name(tmp_path):
    """Raw bytes of the vault file must not contain the user's full name."""
    vault_file = tmp_path / "vault.enc"
    password = "my-master-password"

    save_vault(password=password, vault_data=SAMPLE_VAULT, vault_path=vault_file)
    raw_bytes = vault_file.read_bytes()

    assert b"John Robert Smith" not in raw_bytes, (
        "Full name found in plaintext inside vault file"
    )


def test_vault_file_does_not_contain_plaintext_email(tmp_path):
    """Raw bytes of the vault file must not contain the user's email."""
    vault_file = tmp_path / "vault.enc"
    password = "my-master-password"

    save_vault(password=password, vault_data=SAMPLE_VAULT, vault_path=vault_file)
    raw_bytes = vault_file.read_bytes()

    assert b"john@gmail.com" not in raw_bytes, (
        "Email found in plaintext inside vault file"
    )


def test_vault_file_does_not_contain_plaintext_ssn(tmp_path):
    """Raw bytes of the vault file must not contain the SSN last-4."""
    vault_file = tmp_path / "vault.enc"
    password = "my-master-password"

    save_vault(password=password, vault_data=SAMPLE_VAULT, vault_path=vault_file)
    raw_bytes = vault_file.read_bytes()

    assert b"1234" not in raw_bytes, (
        "SSN last-4 found in plaintext inside vault file"
    )


# ---------------------------------------------------------------------------
# Random salt — two saves produce different ciphertext
# ---------------------------------------------------------------------------

def test_two_saves_produce_different_ciphertext(tmp_path):
    """Each save must use a fresh random salt, so blobs differ even for same input."""
    vault_file_a = tmp_path / "vault_a.enc"
    vault_file_b = tmp_path / "vault_b.enc"
    password = "same-password-both-times"

    save_vault(password=password, vault_data=SAMPLE_VAULT, vault_path=vault_file_a)
    save_vault(password=password, vault_data=SAMPLE_VAULT, vault_path=vault_file_b)

    bytes_a = vault_file_a.read_bytes()
    bytes_b = vault_file_b.read_bytes()

    assert bytes_a != bytes_b, (
        "Two saves with the same password produced identical ciphertext — salt is not random"
    )


def test_vault_file_minimum_size(tmp_path):
    """Vault file must be at least 16 bytes (salt) + 1 byte (ciphertext overhead)."""
    vault_file = tmp_path / "vault.enc"
    save_vault(password="pw", vault_data={"users": []}, vault_path=vault_file)
    assert vault_file.stat().st_size > 16


# ---------------------------------------------------------------------------
# Vault file creation
# ---------------------------------------------------------------------------

def test_save_vault_creates_parent_directories(tmp_path):
    """save_vault must create intermediate directories if they do not exist."""
    vault_file = tmp_path / "nested" / "dir" / "vault.enc"
    save_vault(password="pw", vault_data={"users": []}, vault_path=vault_file)
    assert vault_file.exists()

"""Encrypted PII vault for PrivGuard.

Encryption scheme
-----------------
1. Generate a 16-byte random salt.
2. Derive a 32-byte key with PBKDF2-HMAC-SHA256 (100 000 iterations).
3. Encrypt the JSON-serialised vault dict with Fernet (AES-128-CBC + HMAC-SHA256).
4. Write: salt (16 bytes) | Fernet token (variable length).

Decryption
----------
1. Read the first 16 bytes as the salt.
2. Re-derive the key from the supplied password + salt.
3. Decrypt with Fernet; an invalid password causes an InvalidToken exception,
   which is translated to a ValueError with the documented message.
"""
from __future__ import annotations

import json
import os
from base64 import urlsafe_b64encode
from hashlib import pbkdf2_hmac
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

VAULT_PATH = Path.home() / ".privguard" / "vault.enc"

_SALT_SIZE = 16
_KEY_SIZE = 32
_ITERATIONS = 100_000
_HASH_ALGO = "sha256"
_WRONG_PASSWORD_MSG = "Invalid master password or corrupted vault."


def _derive_key(password: str, salt: bytes) -> bytes:
    """Return a URL-safe base64-encoded 32-byte Fernet key."""
    raw_key = pbkdf2_hmac(
        hash_name=_HASH_ALGO,
        password=password.encode("utf-8"),
        salt=salt,
        iterations=_ITERATIONS,
        dklen=_KEY_SIZE,
    )
    return urlsafe_b64encode(raw_key)


def save_vault(password: str, vault_data: dict, vault_path: Path = VAULT_PATH) -> None:
    """Encrypt *vault_data* with *password* and write it to *vault_path*.

    A fresh 16-byte random salt is generated on every call so that two saves
    with the same password produce different ciphertext.
    """
    vault_path = Path(vault_path)
    vault_path.parent.mkdir(parents=True, exist_ok=True)

    salt = os.urandom(_SALT_SIZE)
    key = _derive_key(password, salt)
    fernet = Fernet(key)

    plaintext = json.dumps(vault_data, ensure_ascii=False).encode("utf-8")
    token = fernet.encrypt(plaintext)

    vault_path.write_bytes(salt + token)


def load_vault(password: str, vault_path: Path = VAULT_PATH) -> dict:
    """Decrypt and return the vault dict stored at *vault_path*.

    Raises
    ------
    ValueError
        If *password* is wrong or the vault file is corrupted.
    FileNotFoundError
        If *vault_path* does not exist.
    """
    vault_path = Path(vault_path)
    raw = vault_path.read_bytes()

    salt = raw[:_SALT_SIZE]
    token = raw[_SALT_SIZE:]

    key = _derive_key(password, salt)
    fernet = Fernet(key)

    try:
        plaintext = fernet.decrypt(token)
    except InvalidToken as exc:
        raise ValueError(_WRONG_PASSWORD_MSG) from exc

    return json.loads(plaintext.decode("utf-8"))

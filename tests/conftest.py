"""Shared pytest configuration and fixtures."""
import pytest
import privguard.vault as _vault_module


@pytest.fixture(autouse=True)
def _fast_kdf(monkeypatch):
    """Monkeypatch PBKDF2 iterations to 1 during tests.

    The production value (600_000) is correct for security but makes every
    KDF call take ~0.5 s, turning the test suite into a multi-minute slog.
    This fixture drops iterations to 1 for all vault tests while leaving the
    module-level constant unchanged so production code is unaffected.
    """
    monkeypatch.setattr(_vault_module, "_ITERATIONS", 1)

import os
import subprocess
import sys
from pathlib import Path

import pytest
from lms_api.core.security import (
    MAX_PASSWORD_LEN,
    hash_password,
    password_needs_rehash,
    verify_password,
)


def test_password_hash_verifies() -> None:
    password_hash = hash_password("correct horse battery staple")

    assert password_hash != "correct horse battery staple"
    assert verify_password("correct horse battery staple", password_hash)


def test_wrong_password_does_not_verify() -> None:
    password_hash = hash_password("correct horse battery staple")

    assert not verify_password("wrong password", password_hash)


def test_hash_uses_argon2id_and_current_cost_parameters() -> None:
    password_hash = hash_password("correct horse battery staple")

    assert password_hash.startswith("$argon2id$")
    assert not password_needs_rehash(password_hash)


def test_hash_rejects_empty_or_overlong_passwords() -> None:
    with pytest.raises(ValueError, match="invalid password length"):
        hash_password("")
    with pytest.raises(ValueError, match="invalid password length"):
        hash_password("x" * (MAX_PASSWORD_LEN + 1))


def test_import_fails_without_jwt_secret() -> None:
    environment = os.environ.copy()
    environment.pop("JWT_SECRET_KEY", None)
    result = subprocess.run(
        [sys.executable, "-c", "import lms_api.core.security"],
        cwd=Path(__file__).parents[1],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "JWT_SECRET_KEY must be set" in result.stderr

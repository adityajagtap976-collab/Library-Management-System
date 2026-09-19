import pytest

from backend.src.lms_api.core.security import (
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

import jwt
import pytest

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_password_round_trip():
    hashed = hash_password("correct horse battery staple")
    assert verify_password("correct horse battery staple", hashed)
    assert not verify_password("wrong password", hashed)


def test_hash_password_does_not_store_plaintext():
    hashed = hash_password("secret123")
    assert "secret123" not in hashed


def test_access_token_round_trip():
    token = create_access_token(subject="user-123", extra_claims={"role": "admin"})
    payload = decode_access_token(token)
    assert payload["sub"] == "user-123"
    assert payload["role"] == "admin"


def test_decode_rejects_tampered_token():
    token = create_access_token(subject="user-123")
    # Flip 4 consecutive base64url characters, not 1 — a single trailing
    # character of a base64 signature can fall on padding bits that don't
    # change the decoded bytes at all, making a one-character tamper
    # nondeterministic (flaky) rather than reliably invalid.
    suffix = "XXXX" if token[-4:] != "XXXX" else "YYYY"
    tampered = token[:-4] + suffix
    with pytest.raises(jwt.PyJWTError):
        decode_access_token(tampered)

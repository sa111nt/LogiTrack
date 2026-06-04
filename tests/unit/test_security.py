import jwt
import pytest

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_hashing():
    password = "super_secret_password"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrong_password", hashed) is False


def test_jwt_access_token_creation_and_decoding():
    data = {"sub": "test@example.com"}
    token = create_access_token(data)

    assert isinstance(token, str)

    payload = decode_token(token, expected_type="access")
    assert payload["sub"] == "test@example.com"
    assert payload["type"] == "access"
    assert "exp" in payload


def test_jwt_refresh_token_creation_and_decoding():
    data = {"sub": "test@example.com"}
    token = create_refresh_token(data)

    assert isinstance(token, str)

    payload = decode_token(token, expected_type="refresh")
    assert payload["sub"] == "test@example.com"
    assert payload["type"] == "refresh"


def test_jwt_invalid_type_raises_error():
    data = {"sub": "test@example.com"}
    access_token = create_access_token(data)

    with pytest.raises(jwt.InvalidTokenError):
        decode_token(access_token, expected_type="refresh")

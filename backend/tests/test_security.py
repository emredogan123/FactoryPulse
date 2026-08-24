from datetime import timedelta
from uuid import uuid4

import jwt
import pytest

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_password_does_not_store_plain_text() -> None:
    plain_password = "SecurePassword123!"

    hashed_password = hash_password(plain_password)

    assert hashed_password != plain_password
    assert plain_password not in hashed_password


def test_verify_password_accepts_correct_password() -> None:
    plain_password = "SecurePassword123!"
    hashed_password = hash_password(plain_password)

    assert verify_password(
        plain_password,
        hashed_password,
    ) is True


def test_verify_password_rejects_incorrect_password() -> None:
    hashed_password = hash_password(
        "CorrectPassword123!"
    )

    assert verify_password(
        "IncorrectPassword123!",
        hashed_password,
    ) is False


def test_access_token_contains_user_subject() -> None:
    user_id = uuid4()

    token = create_access_token(user_id)
    decoded_subject = decode_access_token(token)

    assert decoded_subject == str(user_id)


def test_expired_access_token_is_rejected() -> None:
    token = create_access_token(
        uuid4(),
        expires_delta=timedelta(seconds=-1),
    )

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(token)
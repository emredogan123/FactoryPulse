from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash

from app.core.config import settings


JWT_ALGORITHM = "HS256"

password_hash = PasswordHash.recommended()


def hash_password(
    plain_password: str,
) -> str:
    return password_hash.hash(plain_password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    return password_hash.verify(
        plain_password,
        hashed_password,
    )


def create_access_token(
    subject: UUID | str,
    expires_delta: timedelta | None = None,
) -> str:
    now = datetime.now(timezone.utc)

    if expires_delta is None:
        expires_delta = timedelta(
            minutes=settings.access_token_expire_minutes
        )

    payload = {
        "sub": str(subject),
        "iat": now,
        "exp": now + expires_delta,
    }

    return jwt.encode(
        payload,
        settings.app_secret_key,
        algorithm=JWT_ALGORITHM,
    )


def decode_access_token(
    token: str,
) -> str:
    payload = jwt.decode(
        token,
        settings.app_secret_key,
        algorithms=[JWT_ALGORITHM],
    )

    subject = payload.get("sub")

    if not isinstance(subject, str) or not subject:
        raise InvalidTokenError(
            "Token subject is missing"
        )

    return subject
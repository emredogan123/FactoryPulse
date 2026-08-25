from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.schemas import UserCreate
from app.core.security import (
    hash_password,
    verify_password,
)
from app.models.user import User


class UserAlreadyExistsError(Exception):
    pass


def normalize_email(
    email: str,
) -> str:
    return email.strip().lower()


def get_user_by_email(
    db: Session,
    email: str,
) -> User | None:
    normalized_email = normalize_email(email)

    statement = select(User).where(
        User.email == normalized_email
    )

    return db.scalar(statement)


def create_user(
    db: Session,
    user_data: UserCreate,
) -> User:
    normalized_email = normalize_email(
        user_data.email
    )

    existing_user = get_user_by_email(
        db,
        normalized_email,
    )

    if existing_user is not None:
        raise UserAlreadyExistsError(
            f"User with email '{normalized_email}' "
            "already exists"
        )

    user = User(
        email=normalized_email,
        full_name=user_data.full_name.strip(),
        password_hash=hash_password(
            user_data.password
        ),
        role=user_data.role,
        is_active=True,
    )

    db.add(user)
    db.flush()
    db.refresh(user)

    return user


def authenticate_user(
    db: Session,
    email: str,
    password: str,
) -> User | None:
    user = get_user_by_email(
        db,
        email,
    )

    if user is None:
        return None

    if not user.is_active:
        return None

    if not verify_password(
        password,
        user.password_hash,
    ):
        return None

    return user

def get_users(
    db: Session,
) -> list[User]:
    statement = select(User).order_by(
        User.created_at.asc()
    )

    return list(
        db.scalars(statement).all()
    )
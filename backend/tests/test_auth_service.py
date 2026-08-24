import pytest
from sqlalchemy.orm import Session

from app.auth.schemas import UserCreate
from app.auth.service import (
    UserAlreadyExistsError,
    authenticate_user,
    create_user,
)
from app.core.security import verify_password
from app.models.user import UserRole


def create_test_user(
    database_session: Session,
):
    return create_user(
        database_session,
        UserCreate(
            email="Engineer@FactoryPulse.dev",
            full_name="Quality Engineer",
            password="SecurePassword123!",
            role=UserRole.QUALITY_ENGINEER,
        ),
    )


def test_create_user_hashes_password(
    database_session: Session,
) -> None:
    user = create_test_user(database_session)

    assert user.email == "engineer@factorypulse.dev"
    assert user.full_name == "Quality Engineer"
    assert user.role == UserRole.QUALITY_ENGINEER
    assert user.password_hash != "SecurePassword123!"
    assert verify_password(
        "SecurePassword123!",
        user.password_hash,
    )


def test_duplicate_email_is_rejected(
    database_session: Session,
) -> None:
    create_test_user(database_session)

    with pytest.raises(UserAlreadyExistsError):
        create_user(
            database_session,
            UserCreate(
                email="ENGINEER@FACTORYPULSE.DEV",
                full_name="Another Engineer",
                password="AnotherPassword123!",
            ),
        )


def test_authenticate_user_accepts_valid_credentials(
    database_session: Session,
) -> None:
    created_user = create_test_user(
        database_session
    )

    authenticated_user = authenticate_user(
        database_session,
        email="ENGINEER@FACTORYPULSE.DEV",
        password="SecurePassword123!",
    )

    assert authenticated_user is not None
    assert authenticated_user.id == created_user.id


def test_authenticate_user_rejects_wrong_password(
    database_session: Session,
) -> None:
    create_test_user(database_session)

    authenticated_user = authenticate_user(
        database_session,
        email="engineer@factorypulse.dev",
        password="WrongPassword123!",
    )

    assert authenticated_user is None


def test_inactive_user_cannot_authenticate(
    database_session: Session,
) -> None:
    user = create_test_user(database_session)
    user.is_active = False
    database_session.flush()

    authenticated_user = authenticate_user(
        database_session,
        email=user.email,
        password="SecurePassword123!",
    )

    assert authenticated_user is None
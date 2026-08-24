from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth.schemas import UserCreate
from app.auth.service import create_user
from app.models.user import User, UserRole


TEST_EMAIL = "admin@factorypulse.dev"
TEST_PASSWORD = "SecureAdminPassword123!"


def create_test_admin(
    database_session: Session,
) -> User:
    return create_user(
        database_session,
        UserCreate(
            email=TEST_EMAIL,
            full_name="FactoryPulse Admin",
            password=TEST_PASSWORD,
            role=UserRole.ADMIN,
        ),
    )


def login(
    client: TestClient,
) -> object:
    return client.post(
        "/api/v1/auth/login",
        data={
            "username": TEST_EMAIL,
            "password": TEST_PASSWORD,
        },
    )


def test_login_returns_access_token(
    client: TestClient,
    database_session: Session,
) -> None:
    create_test_admin(database_session)

    response = login(client)

    assert response.status_code == 200

    data = response.json()

    assert isinstance(
        data["access_token"],
        str,
    )
    assert data["access_token"]
    assert data["token_type"] == "bearer"


def test_login_rejects_incorrect_password(
    client: TestClient,
    database_session: Session,
) -> None:
    create_test_admin(database_session)

    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": TEST_EMAIL,
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "Incorrect email or password"
    )


def test_auth_me_returns_current_user(
    client: TestClient,
    database_session: Session,
) -> None:
    created_user = create_test_admin(
        database_session
    )

    login_response = login(client)
    token = login_response.json()["access_token"]

    response = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(created_user.id)
    assert data["email"] == TEST_EMAIL
    assert data["role"] == "ADMIN"
    assert data["is_active"] is True
    assert "password_hash" not in data


def test_auth_me_requires_token(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/v1/auth/me"
    )

    assert response.status_code == 401


def test_inactive_user_cannot_log_in(
    client: TestClient,
    database_session: Session,
) -> None:
    user = create_test_admin(database_session)
    user.is_active = False
    database_session.flush()

    response = login(client)

    assert response.status_code == 401
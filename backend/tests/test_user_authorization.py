from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth.schemas import UserCreate
from app.auth.service import create_user
from app.models.user import UserRole


def create_user_and_get_token(
    client: TestClient,
    database_session: Session,
    email: str,
    role: UserRole,
) -> str:
    password = "SecurePassword123!"

    create_user(
        database_session,
        UserCreate(
            email=email,
            full_name="Test User",
            password=password,
            role=role,
        ),
    )

    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": email,
            "password": password,
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


def test_admin_can_list_users(
    client: TestClient,
    database_session: Session,
) -> None:
    token = create_user_and_get_token(
        client,
        database_session,
        email="admin-rbac@factorypulse.dev",
        role=UserRole.ADMIN,
    )

    response = client.get(
        "/api/v1/users",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    users = response.json()

    assert any(
        user["email"]
        == "admin-rbac@factorypulse.dev"
        for user in users
    )
    assert all(
        "password_hash" not in user
        for user in users
    )


def test_viewer_cannot_list_users(
    client: TestClient,
    database_session: Session,
) -> None:
    token = create_user_and_get_token(
        client,
        database_session,
        email="viewer-rbac@factorypulse.dev",
        role=UserRole.VIEWER,
    )

    response = client.get(
        "/api/v1/users",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Insufficient permissions"
    )


def test_user_list_requires_authentication(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/v1/users"
    )

    assert response.status_code == 401
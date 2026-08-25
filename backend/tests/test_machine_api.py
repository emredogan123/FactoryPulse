from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth.schemas import UserCreate
from app.auth.service import create_user
from app.models.user import UserRole


TEST_PASSWORD = "SecurePassword123!"


def create_payload(
    machine_code: str,
) -> dict[str, str | None]:
    return {
        "machine_code": machine_code,
        "name": "Test Reflow Oven",
        "stage_type": "REFLOW_SOLDERING",
        "status": "ACTIVE",
        "commissioned_at": None,
    }


def create_auth_headers(
    client: TestClient,
    database_session: Session,
    email: str,
    role: UserRole,
) -> dict[str, str]:
    create_user(
        database_session,
        UserCreate(
            email=email,
            full_name="Machine Test User",
            password=TEST_PASSWORD,
            role=role,
        ),
    )

    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": email,
            "password": TEST_PASSWORD,
        },
    )

    assert response.status_code == 200

    token = response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}",
    }


def test_create_list_and_get_machine(
    client: TestClient,
    database_session: Session,
) -> None:
    headers = create_auth_headers(
        client,
        database_session,
        email="admin-machine-crud@factorypulse.dev",
        role=UserRole.ADMIN,
    )

    create_response = client.post(
        "/api/v1/machines",
        json=create_payload("TEST-REFLOW-01"),
        headers=headers,
    )

    assert create_response.status_code == 201

    created_machine = create_response.json()
    machine_id = created_machine["id"]

    assert (
        created_machine["machine_code"]
        == "TEST-REFLOW-01"
    )
    assert created_machine["status"] == "ACTIVE"

    list_response = client.get(
        "/api/v1/machines",
        headers=headers,
    )

    assert list_response.status_code == 200
    assert any(
        machine["id"] == machine_id
        for machine in list_response.json()
    )

    get_response = client.get(
        f"/api/v1/machines/{machine_id}",
        headers=headers,
    )

    assert get_response.status_code == 200
    assert get_response.json()["id"] == machine_id


def test_duplicate_machine_code_returns_conflict(
    client: TestClient,
    database_session: Session,
) -> None:
    headers = create_auth_headers(
        client,
        database_session,
        email="admin-machine-duplicate@factorypulse.dev",
        role=UserRole.ADMIN,
    )

    payload = create_payload("TEST-DUPLICATE-01")

    first_response = client.post(
        "/api/v1/machines",
        json=payload,
        headers=headers,
    )

    second_response = client.post(
        "/api/v1/machines",
        json=payload,
        headers=headers,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_invalid_machine_data_returns_validation_error(
    client: TestClient,
    database_session: Session,
) -> None:
    headers = create_auth_headers(
        client,
        database_session,
        email="admin-machine-validation@factorypulse.dev",
        role=UserRole.ADMIN,
    )

    response = client.post(
        "/api/v1/machines",
        json=create_payload("invalid machine code"),
        headers=headers,
    )

    assert response.status_code == 422


def test_unknown_machine_returns_not_found(
    client: TestClient,
    database_session: Session,
) -> None:
    headers = create_auth_headers(
        client,
        database_session,
        email="engineer-machine-unknown@factorypulse.dev",
        role=UserRole.QUALITY_ENGINEER,
    )

    response = client.get(
        f"/api/v1/machines/{uuid4()}",
        headers=headers,
    )

    assert response.status_code == 404


def test_quality_engineer_can_list_machines(
    client: TestClient,
    database_session: Session,
) -> None:
    headers = create_auth_headers(
        client,
        database_session,
        email="engineer-machine-list@factorypulse.dev",
        role=UserRole.QUALITY_ENGINEER,
    )

    response = client.get(
        "/api/v1/machines",
        headers=headers,
    )

    assert response.status_code == 200


def test_quality_engineer_cannot_create_machine(
    client: TestClient,
    database_session: Session,
) -> None:
    headers = create_auth_headers(
        client,
        database_session,
        email="engineer-machine-create@factorypulse.dev",
        role=UserRole.QUALITY_ENGINEER,
    )

    response = client.post(
        "/api/v1/machines",
        json=create_payload("FORBIDDEN-MACHINE-01"),
        headers=headers,
    )

    assert response.status_code == 403


def test_viewer_cannot_list_machines(
    client: TestClient,
    database_session: Session,
) -> None:
    headers = create_auth_headers(
        client,
        database_session,
        email="viewer-machine-list@factorypulse.dev",
        role=UserRole.VIEWER,
    )

    response = client.get(
        "/api/v1/machines",
        headers=headers,
    )

    assert response.status_code == 403


def test_machine_endpoints_require_authentication(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/v1/machines"
    )

    assert response.status_code == 401
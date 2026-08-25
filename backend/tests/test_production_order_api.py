from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth.schemas import UserCreate
from app.auth.service import create_user
from app.models.user import UserRole

TEST_PASSWORD = "SecurePassword123!"


@pytest.fixture(autouse=True)
def authenticate_as_admin(
    client: TestClient,
    admin_headers: dict[str, str],
) -> None:
    client.headers.update(admin_headers)


def create_role_headers(
    client: TestClient,
    database_session: Session,
    email: str,
    role: UserRole,
) -> dict[str, str]:
    create_user(
        database_session,
        UserCreate(
            email=email,
            full_name="Production Test User",
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

    return {
        "Authorization": (
            f"Bearer {response.json()['access_token']}"
        ),
    }

def create_payload(order_code: str) -> dict[str, object]:
    return {
        "order_code": order_code,
        "product_code": "PCB-CONTROLLER-V1",
        "target_quantity": 1000,
        "planned_start_at": "2026-08-22T08:00:00Z",
        "planned_end_at": "2026-08-22T18:00:00Z",
    }


def test_create_list_and_get_production_order(
    client: TestClient,
) -> None:
    create_response = client.post(
        "/api/v1/production-orders",
        json=create_payload("TEST-PO-0001"),
    )

    assert create_response.status_code == 201

    created_order = create_response.json()
    production_order_id = created_order["id"]

    assert created_order["order_code"] == "TEST-PO-0001"
    assert created_order["product_code"] == "PCB-CONTROLLER-V1"
    assert created_order["target_quantity"] == 1000
    assert created_order["status"] == "PLANNED"

    list_response = client.get(
        "/api/v1/production-orders"
    )

    assert list_response.status_code == 200
    assert any(
        order["id"] == production_order_id
        for order in list_response.json()
    )

    get_response = client.get(
        f"/api/v1/production-orders/{production_order_id}"
    )

    assert get_response.status_code == 200
    assert get_response.json()["id"] == production_order_id


def test_duplicate_order_code_returns_conflict(
    client: TestClient,
) -> None:
    payload = create_payload("TEST-PO-DUPLICATE")

    first_response = client.post(
        "/api/v1/production-orders",
        json=payload,
    )

    second_response = client.post(
        "/api/v1/production-orders",
        json=payload,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_invalid_production_order_returns_validation_error(
    client: TestClient,
) -> None:
    payload = create_payload("TEST-PO-INVALID")
    payload["target_quantity"] = 0

    response = client.post(
        "/api/v1/production-orders",
        json=payload,
    )

    assert response.status_code == 422


def test_invalid_planned_period_returns_validation_error(
    client: TestClient,
) -> None:
    payload = create_payload("TEST-PO-DATES")
    payload["planned_start_at"] = "2026-08-22T18:00:00Z"
    payload["planned_end_at"] = "2026-08-22T08:00:00Z"

    response = client.post(
        "/api/v1/production-orders",
        json=payload,
    )

    assert response.status_code == 422


def test_unknown_production_order_returns_not_found(
    client: TestClient,
) -> None:
    unknown_id = uuid4()

    response = client.get(
        f"/api/v1/production-orders/{unknown_id}"
    )

    assert response.status_code == 404

def test_quality_engineer_can_list_orders(
    client: TestClient,
    database_session: Session,
) -> None:
    headers = create_role_headers(
        client,
        database_session,
        email="engineer-order-list@factorypulse.dev",
        role=UserRole.QUALITY_ENGINEER,
    )

    response = client.get(
        "/api/v1/production-orders",
        headers=headers,
    )

    assert response.status_code == 200


def test_quality_engineer_cannot_create_order(
    client: TestClient,
    database_session: Session,
) -> None:
    headers = create_role_headers(
        client,
        database_session,
        email="engineer-order-create@factorypulse.dev",
        role=UserRole.QUALITY_ENGINEER,
    )

    response = client.post(
        "/api/v1/production-orders",
        json=create_payload("FORBIDDEN-PO-01"),
        headers=headers,
    )

    assert response.status_code == 403


def test_viewer_cannot_list_orders(
    client: TestClient,
    database_session: Session,
) -> None:
    headers = create_role_headers(
        client,
        database_session,
        email="viewer-order-list@factorypulse.dev",
        role=UserRole.VIEWER,
    )

    response = client.get(
        "/api/v1/production-orders",
        headers=headers,
    )

    assert response.status_code == 403


def test_production_order_endpoints_require_authentication(
    client: TestClient,
) -> None:
    client.headers.pop(
        "Authorization",
        None,
    )

    response = client.get(
        "/api/v1/production-orders"
    )

    assert response.status_code == 401
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth.schemas import UserCreate
from app.auth.service import create_user
from app.models.user import UserRole

@pytest.fixture(autouse=True)
def authenticate_as_admin(
    client: TestClient,
    admin_headers: dict[str, str],
) -> None:
    client.headers.update(admin_headers)

TEST_PASSWORD = "SecurePassword123!"


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
            full_name="PCB Test User",
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

def create_production_order(
    client: TestClient,
    order_code: str,
) -> str:
    response = client.post(
        "/api/v1/production-orders",
        json={
            "order_code": order_code,
            "product_code": "PCB-CONTROLLER-V1",
            "target_quantity": 100,
            "planned_start_at": None,
            "planned_end_at": None,
        },
    )

    assert response.status_code == 201

    return response.json()["id"]


def create_pcb_payload(
    serial_number: str,
    production_order_id: str,
) -> dict[str, str]:
    return {
        "serial_number": serial_number,
        "production_order_id": production_order_id,
    }


def test_create_list_filter_and_get_pcb_unit(
    client: TestClient,
) -> None:
    production_order_id = create_production_order(
        client,
        "TEST-ORDER-PCB-01",
    )

    create_response = client.post(
        "/api/v1/pcb-units",
        json=create_pcb_payload(
            "TEST-PCB-000001",
            production_order_id,
        ),
    )

    assert create_response.status_code == 201

    created_pcb = create_response.json()
    pcb_unit_id = created_pcb["id"]

    assert created_pcb["serial_number"] == "TEST-PCB-000001"
    assert created_pcb["production_order_id"] == production_order_id
    assert created_pcb["status"] == "QUEUED"

    list_response = client.get("/api/v1/pcb-units")

    assert list_response.status_code == 200
    assert any(
        pcb["id"] == pcb_unit_id
        for pcb in list_response.json()
    )

    filtered_response = client.get(
        "/api/v1/pcb-units",
        params={
            "production_order_id": production_order_id,
        },
    )

    assert filtered_response.status_code == 200
    assert any(
        pcb["id"] == pcb_unit_id
        for pcb in filtered_response.json()
    )

    get_response = client.get(
        f"/api/v1/pcb-units/{pcb_unit_id}"
    )

    assert get_response.status_code == 200
    assert get_response.json()["id"] == pcb_unit_id


def test_duplicate_serial_number_returns_conflict(
    client: TestClient,
) -> None:
    production_order_id = create_production_order(
        client,
        "TEST-ORDER-PCB-02",
    )

    payload = create_pcb_payload(
        "TEST-PCB-DUPLICATE",
        production_order_id,
    )

    first_response = client.post(
        "/api/v1/pcb-units",
        json=payload,
    )

    second_response = client.post(
        "/api/v1/pcb-units",
        json=payload,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_unknown_production_order_returns_not_found(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/pcb-units",
        json=create_pcb_payload(
            "TEST-PCB-UNKNOWN-ORDER",
            str(uuid4()),
        ),
    )

    assert response.status_code == 404


def test_invalid_serial_number_returns_validation_error(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/pcb-units",
        json=create_pcb_payload(
            "invalid serial number",
            str(uuid4()),
        ),
    )

    assert response.status_code == 422


def test_unknown_pcb_unit_returns_not_found(
    client: TestClient,
) -> None:
    response = client.get(
        f"/api/v1/pcb-units/{uuid4()}"
    )

    assert response.status_code == 404

def test_quality_engineer_can_list_pcb_units(
    client: TestClient,
    database_session: Session,
) -> None:
    headers = create_role_headers(
        client,
        database_session,
        email="engineer-pcb-list@factorypulse.dev",
        role=UserRole.QUALITY_ENGINEER,
    )

    response = client.get(
        "/api/v1/pcb-units",
        headers=headers,
    )

    assert response.status_code == 200


def test_quality_engineer_cannot_create_pcb_unit(
    client: TestClient,
    database_session: Session,
) -> None:
    headers = create_role_headers(
        client,
        database_session,
        email="engineer-pcb-create@factorypulse.dev",
        role=UserRole.QUALITY_ENGINEER,
    )

    response = client.post(
        "/api/v1/pcb-units",
        json=create_pcb_payload(
            "FORBIDDEN-PCB-0001",
            str(uuid4()),
        ),
        headers=headers,
    )

    assert response.status_code == 403


def test_viewer_cannot_list_pcb_units(
    client: TestClient,
    database_session: Session,
) -> None:
    headers = create_role_headers(
        client,
        database_session,
        email="viewer-pcb-list@factorypulse.dev",
        role=UserRole.VIEWER,
    )

    response = client.get(
        "/api/v1/pcb-units",
        headers=headers,
    )

    assert response.status_code == 403


def test_pcb_unit_endpoints_require_authentication(
    client: TestClient,
) -> None:
    client.headers.pop(
        "Authorization",
        None,
    )

    response = client.get(
        "/api/v1/pcb-units"
    )

    assert response.status_code == 401
    
def test_unknown_material_lot_returns_not_found(
    client: TestClient,
) -> None:
    production_order_id = create_production_order(
        client,
        "TEST-ORDER-PCB-LOT-01",
    )

    payload = create_pcb_payload(
        "TEST-PCB-UNKNOWN-LOT",
        production_order_id,
    )
    payload["material_lot_id"] = str(
        uuid4()
    )
    payload["shift"] = "NIGHT"

    response = client.post(
        "/api/v1/pcb-units",
        json=payload,
    )

    assert response.status_code == 404
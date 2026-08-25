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
            full_name="Quality Test User",
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

def create_process_event(
    client: TestClient,
    suffix: str,
) -> str:
    machine_response = client.post(
        "/api/v1/machines",
        json={
            "machine_code": f"TEST-QM-MACHINE-{suffix}",
            "name": "Quality Test Machine",
            "stage_type": "AOI_INSPECTION",
            "status": "ACTIVE",
            "commissioned_at": None,
        },
    )
    assert machine_response.status_code == 201
    machine_id = machine_response.json()["id"]

    order_response = client.post(
        "/api/v1/production-orders",
        json={
            "order_code": f"TEST-QM-ORDER-{suffix}",
            "product_code": "PCB-CONTROLLER-V1",
            "target_quantity": 100,
            "planned_start_at": None,
            "planned_end_at": None,
        },
    )
    assert order_response.status_code == 201
    production_order_id = order_response.json()["id"]

    pcb_response = client.post(
        "/api/v1/pcb-units",
        json={
            "serial_number": f"TEST-QM-PCB-{suffix}",
            "production_order_id": production_order_id,
        },
    )
    assert pcb_response.status_code == 201
    pcb_unit_id = pcb_response.json()["id"]

    event_response = client.post(
        "/api/v1/process-events",
        json={
            "pcb_unit_id": pcb_unit_id,
            "machine_id": machine_id,
            "result": "PENDING",
            "process_parameters": {},
            "notes": "Quality measurement integration test",
            "started_at": None,
            "completed_at": None,
        },
    )
    assert event_response.status_code == 201

    return event_response.json()["id"]


def measurement_payload(
    process_event_id: str,
    metric_code: str = "PEAK_TEMPERATURE",
    value: float = 245.5,
) -> dict[str, object]:
    return {
        "process_event_id": process_event_id,
        "metric_code": metric_code,
        "value": value,
        "unit": "CELSIUS",
        "lower_spec_limit": 235.0,
        "upper_spec_limit": 250.0,
        "measured_at": "2026-08-24T08:05:00Z",
    }


def test_create_list_filter_and_get_measurement(
    client: TestClient,
) -> None:
    process_event_id = create_process_event(
        client,
        "01",
    )

    create_response = client.post(
        "/api/v1/quality-measurements",
        json=measurement_payload(process_event_id),
    )

    assert create_response.status_code == 201

    created_measurement = create_response.json()
    measurement_id = created_measurement["id"]

    assert created_measurement["is_within_spec"] is True
    assert created_measurement["metric_code"] == "PEAK_TEMPERATURE"

    list_response = client.get(
        "/api/v1/quality-measurements",
        params={
            "process_event_id": process_event_id,
            "metric_code": "PEAK_TEMPERATURE",
        },
    )

    assert list_response.status_code == 200
    assert any(
        item["id"] == measurement_id
        for item in list_response.json()
    )

    get_response = client.get(
        f"/api/v1/quality-measurements/{measurement_id}"
    )

    assert get_response.status_code == 200
    assert get_response.json()["id"] == measurement_id


def test_out_of_spec_measurement_returns_false(
    client: TestClient,
) -> None:
    process_event_id = create_process_event(
        client,
        "02",
    )

    response = client.post(
        "/api/v1/quality-measurements",
        json=measurement_payload(
            process_event_id,
            metric_code="PEAK_TEMPERATURE",
            value=260.0,
        ),
    )

    assert response.status_code == 201
    assert response.json()["is_within_spec"] is False


def test_measurement_without_limits_returns_null(
    client: TestClient,
) -> None:
    process_event_id = create_process_event(
        client,
        "03",
    )

    response = client.post(
        "/api/v1/quality-measurements",
        json={
            "process_event_id": process_event_id,
            "metric_code": "MEASURED_VOLTAGE",
            "value": 12.2,
            "unit": "VOLT",
            "lower_spec_limit": None,
            "upper_spec_limit": None,
            "measured_at": None,
        },
    )

    assert response.status_code == 201
    assert response.json()["is_within_spec"] is None


def test_duplicate_metric_returns_conflict(
    client: TestClient,
) -> None:
    process_event_id = create_process_event(
        client,
        "04",
    )
    payload = measurement_payload(process_event_id)

    first_response = client.post(
        "/api/v1/quality-measurements",
        json=payload,
    )
    second_response = client.post(
        "/api/v1/quality-measurements",
        json=payload,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_unknown_process_event_returns_not_found(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/quality-measurements",
        json=measurement_payload(str(uuid4())),
    )

    assert response.status_code == 404


def test_invalid_spec_limits_return_validation_error(
    client: TestClient,
) -> None:
    payload = measurement_payload(str(uuid4()))
    payload["lower_spec_limit"] = 260.0
    payload["upper_spec_limit"] = 250.0

    response = client.post(
        "/api/v1/quality-measurements",
        json=payload,
    )

    assert response.status_code == 422

def test_quality_engineer_can_list_measurements(
    client: TestClient,
    database_session: Session,
) -> None:
    headers = create_role_headers(
        client,
        database_session,
        email="engineer-measurement-list@factorypulse.dev",
        role=UserRole.QUALITY_ENGINEER,
    )

    response = client.get(
        "/api/v1/quality-measurements",
        headers=headers,
    )

    assert response.status_code == 200


def test_quality_engineer_cannot_create_measurement(
    client: TestClient,
    database_session: Session,
) -> None:
    headers = create_role_headers(
        client,
        database_session,
        email="engineer-measurement-create@factorypulse.dev",
        role=UserRole.QUALITY_ENGINEER,
    )

    response = client.post(
        "/api/v1/quality-measurements",
        json=measurement_payload(
            str(uuid4())
        ),
        headers=headers,
    )

    assert response.status_code == 403


def test_viewer_cannot_list_measurements(
    client: TestClient,
    database_session: Session,
) -> None:
    headers = create_role_headers(
        client,
        database_session,
        email="viewer-measurement-list@factorypulse.dev",
        role=UserRole.VIEWER,
    )

    response = client.get(
        "/api/v1/quality-measurements",
        headers=headers,
    )

    assert response.status_code == 403


def test_quality_measurement_endpoints_require_authentication(
    client: TestClient,
) -> None:
    client.headers.pop(
        "Authorization",
        None,
    )

    response = client.get(
        "/api/v1/quality-measurements"
    )

    assert response.status_code == 401
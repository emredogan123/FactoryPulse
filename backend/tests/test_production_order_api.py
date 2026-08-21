from uuid import uuid4

from fastapi.testclient import TestClient


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
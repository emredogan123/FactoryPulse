from uuid import uuid4

from fastapi.testclient import TestClient


def create_payload(machine_code: str) -> dict[str, str | None]:
    return {
        "machine_code": machine_code,
        "name": "Test Reflow Oven",
        "stage_type": "REFLOW_SOLDERING",
        "status": "ACTIVE",
        "commissioned_at": None,
    }


def test_create_list_and_get_machine(
    client: TestClient,
) -> None:
    create_response = client.post(
        "/api/v1/machines",
        json=create_payload("TEST-REFLOW-01"),
    )

    assert create_response.status_code == 201

    created_machine = create_response.json()
    machine_id = created_machine["id"]

    assert created_machine["machine_code"] == "TEST-REFLOW-01"
    assert created_machine["status"] == "ACTIVE"

    list_response = client.get("/api/v1/machines")

    assert list_response.status_code == 200
    assert any(
        machine["id"] == machine_id
        for machine in list_response.json()
    )

    get_response = client.get(
        f"/api/v1/machines/{machine_id}"
    )

    assert get_response.status_code == 200
    assert get_response.json()["id"] == machine_id


def test_duplicate_machine_code_returns_conflict(
    client: TestClient,
) -> None:
    payload = create_payload("TEST-DUPLICATE-01")

    first_response = client.post(
        "/api/v1/machines",
        json=payload,
    )

    second_response = client.post(
        "/api/v1/machines",
        json=payload,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_invalid_machine_data_returns_validation_error(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/machines",
        json=create_payload("invalid machine code"),
    )

    assert response.status_code == 422


def test_unknown_machine_returns_not_found(
    client: TestClient,
) -> None:
    unknown_id = uuid4()

    response = client.get(
        f"/api/v1/machines/{unknown_id}"
    )

    assert response.status_code == 404
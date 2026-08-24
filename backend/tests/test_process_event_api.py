from uuid import uuid4

from fastapi.testclient import TestClient


def create_machine(
    client: TestClient,
    machine_code: str,
    stage_type: str = "REFLOW_SOLDERING",
    machine_status: str = "ACTIVE",
) -> str:
    response = client.post(
        "/api/v1/machines",
        json={
            "machine_code": machine_code,
            "name": "Test Process Machine",
            "stage_type": stage_type,
            "status": machine_status,
            "commissioned_at": None,
        },
    )

    assert response.status_code == 201
    return response.json()["id"]


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


def create_pcb_unit(
    client: TestClient,
    serial_number: str,
    order_code: str,
) -> str:
    production_order_id = create_production_order(
        client,
        order_code,
    )

    response = client.post(
        "/api/v1/pcb-units",
        json={
            "serial_number": serial_number,
            "production_order_id": production_order_id,
        },
    )

    assert response.status_code == 201
    return response.json()["id"]


def completed_event_payload(
    pcb_unit_id: str,
    machine_id: str,
    result: str = "PASSED",
) -> dict[str, object]:
    return {
        "pcb_unit_id": pcb_unit_id,
        "machine_id": machine_id,
        "result": result,
        "process_parameters": {
            "temperature_c": 245.5,
            "conveyor_speed_m_min": 0.9,
        },
        "notes": "Integration test event",
        "started_at": "2026-08-24T08:00:00Z",
        "completed_at": "2026-08-24T08:05:00Z",
    }


def test_create_list_filter_and_get_process_event(
    client: TestClient,
) -> None:
    machine_id = create_machine(
        client,
        "TEST-MACHINE-PE-01",
    )
    pcb_unit_id = create_pcb_unit(
        client,
        "TEST-PCB-PE-0001",
        "TEST-ORDER-PE-01",
    )

    create_response = client.post(
        "/api/v1/process-events",
        json=completed_event_payload(
            pcb_unit_id,
            machine_id,
        ),
    )

    assert create_response.status_code == 201

    created_event = create_response.json()
    process_event_id = created_event["id"]

    assert created_event["result"] == "PASSED"
    assert created_event["pcb_unit_id"] == pcb_unit_id
    assert created_event["machine_id"] == machine_id

    list_response = client.get(
        "/api/v1/process-events",
        params={
            "pcb_unit_id": pcb_unit_id,
            "machine_id": machine_id,
        },
    )

    assert list_response.status_code == 200
    assert any(
        event["id"] == process_event_id
        for event in list_response.json()
    )

    get_response = client.get(
        f"/api/v1/process-events/{process_event_id}"
    )

    assert get_response.status_code == 200
    assert get_response.json()["id"] == process_event_id

    pcb_response = client.get(
        f"/api/v1/pcb-units/{pcb_unit_id}"
    )

    assert pcb_response.json()["status"] == "IN_PRODUCTION"


def test_functional_test_pass_marks_pcb_as_passed(
    client: TestClient,
) -> None:
    machine_id = create_machine(
        client,
        "TEST-MACHINE-PE-02",
        stage_type="FUNCTIONAL_TESTING",
    )
    pcb_unit_id = create_pcb_unit(
        client,
        "TEST-PCB-PE-0002",
        "TEST-ORDER-PE-02",
    )

    response = client.post(
        "/api/v1/process-events",
        json=completed_event_payload(
            pcb_unit_id,
            machine_id,
        ),
    )

    assert response.status_code == 201

    pcb_response = client.get(
        f"/api/v1/pcb-units/{pcb_unit_id}"
    )

    assert pcb_response.json()["status"] == "PASSED"


def test_failed_event_marks_pcb_as_failed(
    client: TestClient,
) -> None:
    machine_id = create_machine(
        client,
        "TEST-MACHINE-PE-03",
    )
    pcb_unit_id = create_pcb_unit(
        client,
        "TEST-PCB-PE-0003",
        "TEST-ORDER-PE-03",
    )

    first_response = client.post(
        "/api/v1/process-events",
        json=completed_event_payload(
            pcb_unit_id,
            machine_id,
            result="FAILED",
        ),
    )

    assert first_response.status_code == 201

    pcb_response = client.get(
        f"/api/v1/pcb-units/{pcb_unit_id}"
    )

    assert pcb_response.json()["status"] == "FAILED"

    second_response = client.post(
        "/api/v1/process-events",
        json=completed_event_payload(
            pcb_unit_id,
            machine_id,
        ),
    )

    assert second_response.status_code == 409


def test_warning_event_marks_pcb_for_rework(
    client: TestClient,
) -> None:
    machine_id = create_machine(
        client,
        "TEST-MACHINE-PE-04",
    )
    pcb_unit_id = create_pcb_unit(
        client,
        "TEST-PCB-PE-0004",
        "TEST-ORDER-PE-04",
    )

    response = client.post(
        "/api/v1/process-events",
        json=completed_event_payload(
            pcb_unit_id,
            machine_id,
            result="WARNING",
        ),
    )

    assert response.status_code == 201

    pcb_response = client.get(
        f"/api/v1/pcb-units/{pcb_unit_id}"
    )

    assert pcb_response.json()["status"] == "REWORK"


def test_inactive_machine_returns_conflict(
    client: TestClient,
) -> None:
    machine_id = create_machine(
        client,
        "TEST-MACHINE-PE-05",
        machine_status="MAINTENANCE",
    )
    pcb_unit_id = create_pcb_unit(
        client,
        "TEST-PCB-PE-0005",
        "TEST-ORDER-PE-05",
    )

    response = client.post(
        "/api/v1/process-events",
        json=completed_event_payload(
            pcb_unit_id,
            machine_id,
        ),
    )

    assert response.status_code == 409


def test_unknown_references_return_not_found(
    client: TestClient,
) -> None:
    unknown_pcb_response = client.post(
        "/api/v1/process-events",
        json=completed_event_payload(
            str(uuid4()),
            str(uuid4()),
        ),
    )

    assert unknown_pcb_response.status_code == 404

    pcb_unit_id = create_pcb_unit(
        client,
        "TEST-PCB-PE-0006",
        "TEST-ORDER-PE-06",
    )

    unknown_machine_response = client.post(
        "/api/v1/process-events",
        json=completed_event_payload(
            pcb_unit_id,
            str(uuid4()),
        ),
    )

    assert unknown_machine_response.status_code == 404


def test_invalid_event_data_returns_validation_error(
    client: TestClient,
) -> None:
    payload = {
        "pcb_unit_id": str(uuid4()),
        "machine_id": str(uuid4()),
        "result": "PENDING",
        "process_parameters": {},
        "completed_at": "2026-08-24T08:05:00Z",
    }

    response = client.post(
        "/api/v1/process-events",
        json=payload,
    )

    assert response.status_code == 422
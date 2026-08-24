from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.analytics.service import calculate_rate
from app.simulation.config import SimulationConfig
from app.simulation.seeder import seed_demo_data


def test_calculate_rate() -> None:
    assert calculate_rate(75, 100) == 75.0
    assert calculate_rate(1, 3) == 33.33
    assert calculate_rate(0, 0) == 0.0


def test_analytics_overview_returns_expected_structure(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/analytics/overview")

    assert response.status_code == 200

    data = response.json()

    assert "production_order_count" in data
    assert "pcb_count" in data
    assert "pcb_status_counts" in data
    assert "pass_rate" in data
    assert "failure_rate" in data
    assert "rework_rate" in data
    assert "process_event_count" in data
    assert "quality_measurement_count" in data
    assert "out_of_spec_measurement_count" in data

    assert set(data["pcb_status_counts"]) == {
        "passed",
        "failed",
        "rework",
        "queued",
    }


def test_analytics_overview_reflects_seeded_data(
    client: TestClient,
    database_session: Session,
) -> None:
    before_response = client.get(
        "/api/v1/analytics/overview"
    )

    assert before_response.status_code == 200

    before = before_response.json()

    config = SimulationConfig(
        data_prefix="TEST-ANALYTICS",
        random_seed=42,
        order_count=1,
        pcb_per_order=4,
        anomaly_probability=0.0,
    )

    seed_demo_data(
        database_session,
        config,
    )

    after_response = client.get(
        "/api/v1/analytics/overview"
    )

    assert after_response.status_code == 200

    after = after_response.json()

    assert (
        after["production_order_count"]
        == before["production_order_count"] + 1
    )
    assert after["pcb_count"] == before["pcb_count"] + 4
    assert (
        after["pcb_status_counts"]["passed"]
        == before["pcb_status_counts"]["passed"] + 4
    )
    assert (
        after["process_event_count"]
        == before["process_event_count"] + 20
    )
    assert (
        after["quality_measurement_count"]
        == before["quality_measurement_count"] + 40
    )
    assert (
        after["out_of_spec_measurement_count"]
        == before["out_of_spec_measurement_count"]
    )

    expected_pass_rate = round(
        after["pcb_status_counts"]["passed"]
        / after["pcb_count"]
        * 100,
        2,
    )

    assert after["pass_rate"] == expected_pass_rate
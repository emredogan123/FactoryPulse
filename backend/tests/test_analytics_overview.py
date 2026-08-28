from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth.schemas import UserCreate
from app.auth.service import create_user
from app.models.user import UserRole
from app.simulation.config import SimulationConfig
from app.simulation.seeder import seed_demo_data
from uuid import uuid4

from app.analytics.schemas import (
    PCBRiskPredictionResponse,
    RiskLevel,
    ModelPerformanceResponse,
)
from app.analytics.service import (
    calculate_rate,
    determine_risk_level,
)
from app.ml.inference import ModelUnavailableError
from app.models.pcb_unit import PCBUnitStatus
from app.ml.reporting import (
    ModelReportUnavailableError,
)


def create_auth_headers(
    client: TestClient,
    database_session: Session,
    email: str,
) -> dict[str, str]:
    password = "SecurePassword123!"

    create_user(
        database_session,
        UserCreate(
            email=email,
            full_name="Dashboard Viewer",
            password=password,
            role=UserRole.VIEWER,
        ),
    )

    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": email,
            "password": password,
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}",
    }


def test_calculate_rate() -> None:
    assert calculate_rate(75, 100) == 75.0
    assert calculate_rate(1, 3) == 33.33
    assert calculate_rate(0, 0) == 0.0


def test_analytics_overview_requires_authentication(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/v1/analytics/overview"
    )

    assert response.status_code == 401


def test_analytics_overview_returns_expected_structure(
    client: TestClient,
    database_session: Session,
) -> None:
    headers = create_auth_headers(
        client,
        database_session,
        email="viewer-structure@factorypulse.dev",
    )

    response = client.get(
        "/api/v1/analytics/overview",
        headers=headers,
    )

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
    headers = create_auth_headers(
        client,
        database_session,
        email="viewer-seed@factorypulse.dev",
    )

    before_response = client.get(
        "/api/v1/analytics/overview",
        headers=headers,
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
        "/api/v1/analytics/overview",
        headers=headers,
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

def test_determine_risk_level() -> None:
    assert (
        determine_risk_level(0.10, 0.44)
        == RiskLevel.LOW
    )
    assert (
        determine_risk_level(0.30, 0.44)
        == RiskLevel.MEDIUM
    )
    assert (
        determine_risk_level(0.60, 0.44)
        == RiskLevel.HIGH
    )


def test_pcb_risk_requires_authentication(
    client: TestClient,
) -> None:
    response = client.get(
        f"/api/v1/analytics/pcbs/{uuid4()}/risk"
    )

    assert response.status_code == 401


def test_pcb_risk_returns_not_found(
    client: TestClient,
    database_session: Session,
) -> None:
    headers = create_auth_headers(
        client,
        database_session,
        email="risk-not-found@factorypulse.dev",
    )

    response = client.get(
        f"/api/v1/analytics/pcbs/{uuid4()}/risk",
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "PCB unit not found",
    }


def test_pcb_risk_returns_prediction(
    client: TestClient,
    database_session: Session,
    monkeypatch,
) -> None:
    headers = create_auth_headers(
        client,
        database_session,
        email="risk-prediction@factorypulse.dev",
    )

    pcb_id = uuid4()

    def fake_prediction(*args, **kwargs):
        return PCBRiskPredictionResponse(
            pcb_id=pcb_id,
            serial_number="TEST-PCB-000001",
            actual_status=PCBUnitStatus.FAILED,
            issue_probability=0.73,
            decision_threshold=0.44,
            predicted_issue=True,
            risk_level=RiskLevel.HIGH,
            model_type="random_forest",
        )

    monkeypatch.setattr(
        "app.analytics.router."
        "get_pcb_risk_prediction",
        fake_prediction,
    )

    response = client.get(
        f"/api/v1/analytics/pcbs/{pcb_id}/risk",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["pcb_id"] == str(pcb_id)
    assert (
        data["serial_number"]
        == "TEST-PCB-000001"
    )
    assert data["issue_probability"] == 0.73
    assert data["decision_threshold"] == 0.44
    assert data["predicted_issue"] is True
    assert data["risk_level"] == "HIGH"
    assert data["model_type"] == "random_forest"


def test_pcb_risk_returns_service_unavailable(
    client: TestClient,
    database_session: Session,
    monkeypatch,
) -> None:
    headers = create_auth_headers(
        client,
        database_session,
        email="risk-unavailable@factorypulse.dev",
    )

    def unavailable_prediction(*args, **kwargs):
        raise ModelUnavailableError(
            "Model missing"
        )

    monkeypatch.setattr(
        "app.analytics.router."
        "get_pcb_risk_prediction",
        unavailable_prediction,
    )

    response = client.get(
        f"/api/v1/analytics/pcbs/{uuid4()}/risk",
        headers=headers,
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "ML model is unavailable",
    }

def test_model_performance_requires_authentication(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/v1/analytics/model-performance"
    )

    assert response.status_code == 401


def test_model_performance_returns_report(
    client: TestClient,
    database_session: Session,
    monkeypatch,
) -> None:
    headers = create_auth_headers(
        client,
        database_session,
        email="model-report@factorypulse.dev",
    )

    report = ModelPerformanceResponse(
        model_name="FactoryPulse PCB Risk Model",
        model_type="random_forest",
        evaluated_at=(
            "2026-08-28T08:05:32+00:00"
        ),
        dataset={
            "name": "ml_test.csv",
            "row_count": 2000,
            "issue_count": 367,
            "issue_rate": 0.1835,
        },
        decision_threshold=0.44,
        feature_count=21,
        metrics={
            "accuracy": 0.9105,
            "precision": 0.76257,
            "recall": 0.743869,
            "f1_score": 0.753103,
            "roc_auc": 0.913788,
        },
        confusion_matrix={
            "true_negative": 1548,
            "false_positive": 85,
            "false_negative": 94,
            "true_positive": 273,
        },
        feature_importances=[],
    )

    monkeypatch.setattr(
        "app.analytics.router."
        "load_model_performance_report",
        lambda report_path: report,
    )

    response = client.get(
        "/api/v1/analytics/model-performance",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["model_type"] == "random_forest"
    assert data["dataset"]["row_count"] == 2000
    assert data["metrics"]["roc_auc"] == 0.913788
    assert data["decision_threshold"] == 0.44


def test_model_performance_returns_unavailable(
    client: TestClient,
    database_session: Session,
    monkeypatch,
) -> None:
    headers = create_auth_headers(
        client,
        database_session,
        email=(
            "model-report-unavailable"
            "@factorypulse.dev"
        ),
    )

    def unavailable_report(*args, **kwargs):
        raise ModelReportUnavailableError(
            "Report missing"
        )

    monkeypatch.setattr(
        "app.analytics.router."
        "load_model_performance_report",
        unavailable_report,
    )

    response = client.get(
        "/api/v1/analytics/model-performance",
        headers=headers,
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": (
            "ML performance report "
            "is unavailable"
        ),
    }
from datetime import datetime, timezone
from math import inf
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.quality_measurement import (
    QualityMeasurementCreate,
)


def test_valid_quality_measurement() -> None:
    schema = QualityMeasurementCreate(
        process_event_id=uuid4(),
        metric_code="PEAK_TEMPERATURE",
        value=245.5,
        unit="CELSIUS",
        lower_spec_limit=235.0,
        upper_spec_limit=250.0,
        measured_at=datetime(
            2026,
            8,
            24,
            8,
            5,
            tzinfo=timezone.utc,
        ),
    )

    assert schema.metric_code == "PEAK_TEMPERATURE"
    assert schema.value == 245.5


def test_invalid_metric_code_is_rejected() -> None:
    with pytest.raises(ValidationError):
        QualityMeasurementCreate(
            process_event_id=uuid4(),
            metric_code="peak temperature",
            value=245.5,
            unit="CELSIUS",
        )


def test_lower_limit_cannot_exceed_upper_limit() -> None:
    with pytest.raises(ValidationError):
        QualityMeasurementCreate(
            process_event_id=uuid4(),
            metric_code="PEAK_TEMPERATURE",
            value=245.5,
            unit="CELSIUS",
            lower_spec_limit=250.0,
            upper_spec_limit=235.0,
        )


def test_measured_at_requires_timezone() -> None:
    with pytest.raises(ValidationError):
        QualityMeasurementCreate(
            process_event_id=uuid4(),
            metric_code="PEAK_TEMPERATURE",
            value=245.5,
            unit="CELSIUS",
            measured_at=datetime(
                2026,
                8,
                24,
                8,
                5,
            ),
        )


def test_infinite_value_is_rejected() -> None:
    with pytest.raises(ValidationError):
        QualityMeasurementCreate(
            process_event_id=uuid4(),
            metric_code="PEAK_TEMPERATURE",
            value=inf,
            unit="CELSIUS",
        )
import json
from pathlib import Path

from pydantic import ValidationError

from app.analytics.schemas import (
    ModelPerformanceResponse,
)


class ModelReportUnavailableError(
    RuntimeError
):
    pass


def load_model_performance_report(
    report_path: Path,
) -> ModelPerformanceResponse:
    resolved_path = report_path.resolve()

    if not resolved_path.is_file():
        raise ModelReportUnavailableError(
            f"Model report not found: "
            f"{resolved_path}"
        )

    try:
        with resolved_path.open(
            "r",
            encoding="utf-8",
        ) as report_file:
            report_data = json.load(
                report_file
            )

        return (
            ModelPerformanceResponse
            .model_validate(report_data)
        )
    except (
        OSError,
        json.JSONDecodeError,
        ValidationError,
    ) as error:
        raise ModelReportUnavailableError(
            "Model report could not be loaded"
        ) from error
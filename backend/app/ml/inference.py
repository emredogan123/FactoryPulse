from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import pandas as pd


class ModelUnavailableError(RuntimeError):
    pass


@lru_cache(maxsize=4)
def load_model_artifact(
    model_path: str,
) -> dict[str, Any]:
    resolved_path = Path(model_path).resolve()

    if not resolved_path.is_file():
        raise ModelUnavailableError(
            f"ML model not found: {resolved_path}"
        )

    try:
        artifact = joblib.load(resolved_path)
    except Exception as error:
        raise ModelUnavailableError(
            "ML model could not be loaded"
        ) from error

    required_keys = {
        "pipeline",
        "feature_columns",
        "target_column",
    }

    missing_keys = required_keys.difference(
        artifact
    )

    if missing_keys:
        raise ModelUnavailableError(
            "Invalid ML model artifact; "
            "missing keys: "
            + ", ".join(sorted(missing_keys))
        )

    return artifact


def predict_issue_probability(
    feature_row: dict[str, Any],
    model_path: Path,
) -> tuple[float, float, bool, str]:
    artifact = load_model_artifact(
        str(model_path.resolve())
    )

    feature_columns = artifact[
        "feature_columns"
    ]

    dataframe = pd.DataFrame(
        [feature_row]
    ).reindex(
        columns=feature_columns
    )

    pipeline = artifact["pipeline"]

    probability = float(
        pipeline.predict_proba(dataframe)[0, 1]
    )

    decision_threshold = float(
        artifact.get(
            "decision_threshold",
            0.5,
        )
    )

    predicted_issue = (
        probability >= decision_threshold
    )

    model_type = str(
        artifact.get(
            "model_type",
            "unknown",
        )
    )

    return (
        round(probability, 4),
        decision_threshold,
        predicted_issue,
        model_type,
    )

def predict_issue_probabilities(
    feature_rows: list[dict[str, Any]],
    model_path: Path,
) -> list[tuple[float, float, bool, str]]:
    if not feature_rows:
        return []

    artifact = load_model_artifact(
        str(model_path.resolve())
    )

    feature_columns = artifact[
        "feature_columns"
    ]

    dataframe = pd.DataFrame(
        feature_rows
    ).reindex(
        columns=feature_columns
    )

    pipeline = artifact["pipeline"]

    probabilities = pipeline.predict_proba(
        dataframe
    )[:, 1]

    decision_threshold = float(
        artifact.get(
            "decision_threshold",
            0.5,
        )
    )

    model_type = str(
        artifact.get(
            "model_type",
            "unknown",
        )
    )

    return [
        (
            round(float(probability), 4),
            decision_threshold,
            bool(
                probability
                >= decision_threshold
            ),
            model_type,
        )
        for probability in probabilities
    ]
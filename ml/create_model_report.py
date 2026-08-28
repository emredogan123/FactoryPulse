import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


ML_DIRECTORY = Path(__file__).resolve().parent

DEFAULT_MODEL_PATH = (
    ML_DIRECTORY
    / "models"
    / "enhanced_random_forest.joblib"
)

DEFAULT_DATASET_PATH = (
    ML_DIRECTORY
    / "data"
    / "ml_test.csv"
)

DEFAULT_REPORT_PATH = (
    ML_DIRECTORY
    / "reports"
    / "random_forest_evaluation.json"
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Create a FactoryPulse "
            "model evaluation report"
        )
    )

    parser.add_argument(
        "--model",
        type=Path,
        default=DEFAULT_MODEL_PATH,
    )

    parser.add_argument(
        "--dataset",
        type=Path,
        default=DEFAULT_DATASET_PATH,
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_REPORT_PATH,
    )

    return parser


def get_feature_importances(
    artifact: dict[str, Any],
    limit: int = 15,
) -> list[dict[str, Any]]:
    pipeline = artifact["pipeline"]

    preprocessor = pipeline.named_steps[
        "preprocessor"
    ]

    classifier = pipeline.named_steps[
        "classifier"
    ]

    if not hasattr(
        classifier,
        "feature_importances_",
    ):
        return []

    feature_names = (
        preprocessor.get_feature_names_out()
    )

    importances = (
        classifier.feature_importances_
    )

    rows = sorted(
        zip(feature_names, importances),
        key=lambda row: row[1],
        reverse=True,
    )

    return [
        {
            "feature": str(feature),
            "importance": round(
                float(importance),
                6,
            ),
        }
        for feature, importance
        in rows[:limit]
    ]


def main() -> None:
    arguments = build_parser().parse_args()

    artifact = joblib.load(
        arguments.model
    )

    dataframe = pd.read_csv(
        arguments.dataset
    )

    feature_columns = artifact[
        "feature_columns"
    ]

    target_column = artifact[
        "target_column"
    ]

    features = dataframe[
        feature_columns
    ]

    target = dataframe[
        target_column
    ]

    pipeline = artifact["pipeline"]

    probabilities = pipeline.predict_proba(
        features
    )[:, 1]

    decision_threshold = float(
        artifact.get(
            "decision_threshold",
            0.5,
        )
    )

    predictions = (
        probabilities >= decision_threshold
    ).astype(int)

    matrix = confusion_matrix(
        target,
        predictions,
    )

    report = {
        "model_name": (
            "FactoryPulse PCB Risk Model"
        ),
        "model_type": artifact.get(
            "model_type",
            "unknown",
        ),
        "evaluated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "dataset": {
            "name": arguments.dataset.name,
            "row_count": len(dataframe),
            "issue_count": int(
                target.sum()
            ),
            "issue_rate": round(
                float(target.mean()),
                6,
            ),
        },
        "decision_threshold": (
            decision_threshold
        ),
        "feature_count": len(
            feature_columns
        ),
        "metrics": {
            "accuracy": round(
                accuracy_score(
                    target,
                    predictions,
                ),
                6,
            ),
            "precision": round(
                precision_score(
                    target,
                    predictions,
                    zero_division=0,
                ),
                6,
            ),
            "recall": round(
                recall_score(
                    target,
                    predictions,
                    zero_division=0,
                ),
                6,
            ),
            "f1_score": round(
                f1_score(
                    target,
                    predictions,
                    zero_division=0,
                ),
                6,
            ),
            "roc_auc": round(
                roc_auc_score(
                    target,
                    probabilities,
                ),
                6,
            ),
        },
        "confusion_matrix": {
            "true_negative": int(
                matrix[0, 0]
            ),
            "false_positive": int(
                matrix[0, 1]
            ),
            "false_negative": int(
                matrix[1, 0]
            ),
            "true_positive": int(
                matrix[1, 1]
            ),
        },
        "feature_importances": (
            get_feature_importances(
                artifact
            )
        ),
    }

    arguments.output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with arguments.output.open(
        "w",
        encoding="utf-8",
    ) as report_file:
        json.dump(
            report,
            report_file,
            indent=2,
        )

    print("FactoryPulse model report created")
    print(
        f"Model: {report['model_type']}"
    )
    print(
        f"Dataset rows: "
        f"{report['dataset']['row_count']}"
    )
    print(
        f"ROC-AUC: "
        f"{report['metrics']['roc_auc']}"
    )
    print(
        f"Output: "
        f"{arguments.output.resolve()}"
    )


if __name__ == "__main__":
    main()
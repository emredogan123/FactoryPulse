import argparse
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate a FactoryPulse model "
            "on an independent dataset"
        )
    )

    parser.add_argument(
        "--model",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--dataset",
        type=Path,
        required=True,
    )

    return parser


def main() -> None:
    arguments = build_parser().parse_args()

    artifact = joblib.load(arguments.model)
    dataframe = pd.read_csv(arguments.dataset)

    feature_columns = artifact[
        "feature_columns"
    ]

    target_column = artifact[
        "target_column"
    ]

    missing_columns = [
        column
        for column in feature_columns
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise SystemExit(
            "Dataset is missing required columns: "
            + ", ".join(missing_columns)
        )

    features = dataframe[feature_columns]
    target = dataframe[target_column]

    pipeline = artifact["pipeline"]

    probabilities = pipeline.predict_proba(
        features
    )[:, 1]

    decision_threshold = artifact.get(
        "decision_threshold",
        0.5,
    )

    predictions = (
        probabilities >= decision_threshold
    ).astype(int)

    print("FactoryPulse independent evaluation")
    print(f"Model: {arguments.model.name}")
    print(f"Dataset rows: {len(dataframe)}")
    print(
        f"Issue rate: "
        f"{target.mean() * 100:.2f}%"
    )
    print(
        "Decision threshold: "
        f"{decision_threshold:.2f}"
    )
    print("\nMetrics")
    print(
        "Accuracy:  "
        f"{accuracy_score(target, predictions):.4f}"
    )
    print(
        "Precision: "
        f"{precision_score(target, predictions, zero_division=0):.4f}"
    )
    print(
        "Recall:    "
        f"{recall_score(target, predictions, zero_division=0):.4f}"
    )
    print(
        "F1 score:  "
        f"{f1_score(target, predictions, zero_division=0):.4f}"
    )
    print(
        "ROC-AUC:   "
        f"{roc_auc_score(target, probabilities):.4f}"
    )

    print("\nConfusion matrix")
    print(
        confusion_matrix(
            target,
            predictions,
        )
    )

    print("\nClassification report")
    print(
        classification_report(
            target,
            predictions,
            digits=4,
            zero_division=0,
        )
    )


if __name__ == "__main__":
    main()
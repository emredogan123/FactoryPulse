import argparse
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from train_baseline import (
    DEFAULT_DATASET_PATH,
    select_feature_columns,
)
import numpy as np

ML_DIRECTORY = Path(__file__).resolve().parent

DEFAULT_MODEL_PATH = (
    ML_DIRECTORY
    / "models"
    / "enhanced_random_forest.joblib"
)

TARGET_COLUMN = "target_issue"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Train the FactoryPulse "
            "Random Forest model"
        )
    )

    parser.add_argument(
        "--dataset",
        type=Path,
        default=DEFAULT_DATASET_PATH,
    )

    parser.add_argument(
        "--model-output",
        type=Path,
        default=DEFAULT_MODEL_PATH,
    )

    parser.add_argument(
        "--test-size",
        type=float,
        default=0.20,
    )

    parser.add_argument(
        "--random-state",
        type=int,
        default=42,
    )
    parser.add_argument(
        "--minimum-recall",
        type=float,
        default=0.80,
        help=(
            "Minimum validation recall used "
            "for threshold selection"
        ),
    )

    return parser


def build_pipeline(
    categorical_columns: list[str],
    numeric_columns: list[str],
    random_state: int,
) -> Pipeline:
    categorical_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(
                    strategy="most_frequent",
                ),
            ),
            (
                "one_hot_encoder",
                OneHotEncoder(
                    handle_unknown="ignore",
                ),
            ),
        ]
    )

    numeric_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(
                    strategy="median",
                ),
            ),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "categorical",
                categorical_pipeline,
                categorical_columns,
            ),
            (
                "numeric",
                numeric_pipeline,
                numeric_columns,
            ),
        ]
    )

    classifier = RandomForestClassifier(
        n_estimators=500,
        max_depth=14,
        min_samples_leaf=3,
        class_weight="balanced_subsample",
        random_state=random_state,
        n_jobs=-1,
    )

    return Pipeline(
        steps=[
            (
                "preprocessor",
                preprocessor,
            ),
            (
                "classifier",
                classifier,
            ),
        ]
    )

def select_decision_threshold(
    target,
    probabilities,
    minimum_recall: float,
) -> float:
    candidates: list[
        tuple[float, float, float, float]
    ] = []

    for threshold in np.arange(
        0.05,
        0.96,
        0.01,
    ):
        predictions = (
            probabilities >= threshold
        ).astype(int)

        recall = recall_score(
            target,
            predictions,
            zero_division=0,
        )

        if recall < minimum_recall:
            continue

        precision = precision_score(
            target,
            predictions,
            zero_division=0,
        )

        f1 = f1_score(
            target,
            predictions,
            zero_division=0,
        )

        candidates.append(
            (
                precision,
                f1,
                float(threshold),
                recall,
            )
        )

    if not candidates:
        return 0.5

    best_candidate = max(
        candidates,
        key=lambda candidate: (
            candidate[0],
            candidate[1],
            candidate[2],
        ),
    )

    return round(best_candidate[2], 2)

def print_feature_importances(
    pipeline: Pipeline,
) -> None:
    preprocessor = pipeline.named_steps[
        "preprocessor"
    ]

    classifier = pipeline.named_steps[
        "classifier"
    ]

    feature_names = (
        preprocessor.get_feature_names_out()
    )

    importance_table = pd.DataFrame(
        {
            "feature": feature_names,
            "importance": (
                classifier.feature_importances_
            ),
        }
    ).sort_values(
        "importance",
        ascending=False,
    )

    print("\nTop feature importances")

    for row in importance_table.head(15).itertuples():
        print(
            f"{row.feature}: "
            f"{row.importance:.4f}"
        )


def main() -> None:
    arguments = build_parser().parse_args()

    dataframe = pd.read_csv(
        arguments.dataset
    )

    if TARGET_COLUMN not in dataframe.columns:
        raise SystemExit(
            f"Missing target column: {TARGET_COLUMN}"
        )

    categorical_columns, numeric_columns = (
        select_feature_columns(
            dataframe,
            include_engineered_features=True,
        )
    )

    feature_columns = (
        categorical_columns
        + numeric_columns
    )

    features = dataframe[feature_columns]
    target = dataframe[TARGET_COLUMN]

    (
        features_train,
        features_test,
        target_train,
        target_test,
    ) = train_test_split(
        features,
        target,
        test_size=arguments.test_size,
        random_state=arguments.random_state,
        stratify=target,
    )

    pipeline = build_pipeline(
        categorical_columns,
        numeric_columns,
        arguments.random_state,
    )

    pipeline.fit(
        features_train,
        target_train,
    )

    probabilities = pipeline.predict_proba(
        features_test
    )[:, 1]

    decision_threshold = (
        select_decision_threshold(
            target_test,
            probabilities,
            arguments.minimum_recall,
        )
    )

    predictions = (
        probabilities >= decision_threshold
    ).astype(int)

    print("FactoryPulse Random Forest model")
    print(f"Dataset rows: {len(dataframe)}")
    print(
        f"Training rows: {len(features_train)}"
    )
    print(f"Test rows: {len(features_test)}")
    print(f"Features: {len(feature_columns)}")

    print(
        "Decision threshold: "
        f"{decision_threshold:.2f}"
    )
    
    print("\nMetrics")
    print(
        "Accuracy:  "
        f"{accuracy_score(target_test, predictions):.4f}"
    )
    print(
        "Precision: "
        f"{precision_score(target_test, predictions, zero_division=0):.4f}"
    )
    print(
        "Recall:    "
        f"{recall_score(target_test, predictions, zero_division=0):.4f}"
    )
    print(
        "F1 score:  "
        f"{f1_score(target_test, predictions, zero_division=0):.4f}"
    )
    print(
        "ROC-AUC:   "
        f"{roc_auc_score(target_test, probabilities):.4f}"
    )

    print_feature_importances(pipeline)

    print("\nConfusion matrix")
    print(
        confusion_matrix(
            target_test,
            predictions,
        )
    )

    print("\nClassification report")
    print(
        classification_report(
            target_test,
            predictions,
            digits=4,
            zero_division=0,
        )
    )

    arguments.model_output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    artifact = {
        "pipeline": pipeline,
        "feature_columns": feature_columns,
        "categorical_columns": (
            categorical_columns
        ),
        "numeric_columns": numeric_columns,
        "target_column": TARGET_COLUMN,
        "model_type": "random_forest",
        "decision_threshold": (
            decision_threshold
        ),
    }

    joblib.dump(
        artifact,
        arguments.model_output,
    )

    print(
        "\nModel saved: "
        f"{arguments.model_output.resolve()}"
    )


if __name__ == "__main__":
    main()
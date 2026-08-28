import argparse
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
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
from sklearn.preprocessing import (
    OneHotEncoder,
    StandardScaler,
)


ML_DIRECTORY = Path(__file__).resolve().parent

DEFAULT_DATASET_PATH = (
    ML_DIRECTORY
    / "data"
    / "factorypulse_dataset.csv"
)

DEFAULT_MODEL_PATH = (
    ML_DIRECTORY
    / "models"
    / "baseline_logistic_regression.joblib"
)

TARGET_COLUMN = "target_issue"

IDENTIFIER_COLUMNS = {
    "pcb_id",
    "serial_number",
}

CATEGORICAL_COLUMNS = [
    "shift",
    "material_lot_code",
    "material_type",
    "supplier_code",
]
ENGINEERED_FEATURE_SUFFIXES = (
    "__param__drift_score",
    "__param__degradation_score",
    "__param__thermal_stress_index",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Train the FactoryPulse "
            "baseline classification model"
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
        "--include-engineered-features",
        action="store_true",
        help=(
            "Include drift, degradation, "
            "and thermal-stress features"
        ),
    )

    return parser


def select_feature_columns(
    dataframe: pd.DataFrame,
    include_engineered_features: bool,
) -> tuple[list[str], list[str]]:
    available_categorical_columns = [
        column
        for column in CATEGORICAL_COLUMNS
        if column in dataframe.columns
    ]

    numeric_columns = [
        column
        for column in dataframe.columns
        if (
            "__param__" in column
            and column
            not in IDENTIFIER_COLUMNS
            and (
                include_engineered_features
                or not column.endswith(
                    ENGINEERED_FEATURE_SUFFIXES
                )
            )
        )
    ]

    constant_columns = [
        column
        for column in numeric_columns
        if dataframe[column].nunique(
            dropna=True
        ) <= 1
    ]

    numeric_columns = [
        column
        for column in numeric_columns
        if column not in constant_columns
    ]

    if constant_columns:
        print(
            "Dropped constant columns: "
            f"{len(constant_columns)}"
        )

        for column in constant_columns:
            print(f"  - {column}")

    return (
        available_categorical_columns,
        numeric_columns,
    )


def build_pipeline(
    categorical_columns: list[str],
    numeric_columns: list[str],
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
            (
                "scaler",
                StandardScaler(),
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

    classifier = LogisticRegression(
        class_weight="balanced",
        max_iter=2000,
        random_state=42,
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
            arguments.include_engineered_features,
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
    )

    pipeline.fit(
        features_train,
        target_train,
    )

    feature_names = (
        pipeline.named_steps[
            "preprocessor"
        ].get_feature_names_out()
    )

    coefficients = (
        pipeline.named_steps[
            "classifier"
        ].coef_[0]
    )

    coefficient_table = pd.DataFrame(
        {
            "feature": feature_names,
            "coefficient": coefficients,
            "absolute_coefficient": abs(
                coefficients
            ),
        }
    ).sort_values(
        "absolute_coefficient",
        ascending=False,
    )

    predictions = pipeline.predict(
        features_test
    )

    probabilities = pipeline.predict_proba(
        features_test
    )[:, 1]

    accuracy = accuracy_score(
        target_test,
        predictions,
    )

    precision = precision_score(
        target_test,
        predictions,
        zero_division=0,
    )

    recall = recall_score(
        target_test,
        predictions,
        zero_division=0,
    )

    f1 = f1_score(
        target_test,
        predictions,
        zero_division=0,
    )

    roc_auc = roc_auc_score(
        target_test,
        probabilities,
    )

    model_name = (
        "feature-engineered model"
        if arguments.include_engineered_features
        else "raw-process baseline model"
    )

    print(f"FactoryPulse {model_name}")
    print(f"Dataset rows: {len(dataframe)}")
    print(
        f"Training rows: {len(features_train)}"
    )
    print(f"Test rows: {len(features_test)}")
    print(f"Features: {len(feature_columns)}")

    print("\nMetrics")
    print(f"Accuracy:  {accuracy:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall:    {recall:.4f}")
    print(f"F1 score:  {f1:.4f}")
    print(f"ROC-AUC:   {roc_auc:.4f}")

    print("\nTop influential features")

    for row in coefficient_table.head(15).itertuples():
        print(
            f"{row.feature}: "
            f"{row.coefficient:.4f}"
        )

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

    model_artifact = {
        "pipeline": pipeline,
        "feature_columns": feature_columns,
        "categorical_columns": (
            categorical_columns
        ),
        "numeric_columns": numeric_columns,
        "target_column": TARGET_COLUMN,
    }

    joblib.dump(
        model_artifact,
        arguments.model_output,
    )

    print(
        "\nModel saved: "
        f"{arguments.model_output.resolve()}"
    )


if __name__ == "__main__":
    main()
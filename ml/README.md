# FactoryPulse Machine Learning

Machine-learning pipeline for PCB quality-risk prediction using synthetic manufacturing data.

## Objective

The model estimates whether a PCB is likely to experience a quality issue using information available during production.

Prediction inputs include:

- production shift;
- material lot;
- machine degradation;
- process parameters;
- process drift;
- Reflow thermal stress.

Final quality outcomes are used only as the target variable and are not included as prediction inputs.

## Models

Two model families were evaluated:

1. Logistic Regression baseline
2. Random Forest classifier

The selected model is the tuned Random Forest classifier with a decision threshold of `0.44`.

## Independent Evaluation

| Metric | Result |
|---|---:|
| Accuracy | 91.05% |
| Precision | 76.26% |
| Recall | 74.39% |
| F1 Score | 75.31% |
| ROC-AUC | 91.38% |

Evaluation dataset:

- 2,000 PCB records
- 367 issue records
- 18.35% issue rate

## Training

Run the following command from the `ml` directory:

    python .\train_random_forest.py `
        --dataset .\data\ml_train.csv `
        --model-output .\models\enhanced_random_forest.joblib `
        --minimum-recall 0.80

## Evaluation

Run the following command from the `ml` directory:

    python .\evaluate_model.py `
        --model .\models\enhanced_random_forest.joblib `
        --dataset .\data\ml_test.csv

## Artifacts

The ML directories are organized as follows:

    data/       Generated training and test datasets
    models/     Serialized local model files
    reports/    Evaluation reports

Generated CSV and `.joblib` files are not tracked in Git. The evaluation report is retained for reproducibility and dashboard model observability.

## Limitations

- Training and evaluation data are synthetic.
- Metrics do not represent real factory performance.
- Feature importance represents predictive association, not causation.
- Real deployment requires production-data validation and model monitoring.
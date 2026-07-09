# Template: Machine Learning Project

`backend/templates/ml-project.yaml` — for a model training / experiment repo.

| Section | Required |
|---|---|
| Overview | yes |
| Dataset | yes |
| Model Architecture | no |
| Training | yes |
| Evaluation | yes |
| Results | no |
| Reproducing Results | yes |
| Citation | no |
| License | no |

## Example README that passes this template

```markdown
# churn-predictor

A gradient-boosted model that predicts subscription churn 30 days ahead.

## Overview

This repo trains a LightGBM classifier on historical account activity to
flag accounts likely to churn, so the retention team can reach out first.

## Dataset

Trained on `data/accounts_2023_2025.parquet` (1.2M rows, 40 features:
usage frequency, support tickets, plan tier, tenure). Labels are churn
within 30 days, derived from `subscription_events`. See `data/SCHEMA.md`.

## Model Architecture

LightGBM, 400 trees, max depth 6, with a calibration layer (isotonic
regression) on top of the raw churn probability.

## Training

    python train.py --config configs/lgbm_v3.yaml

Training reads `configs/lgbm_v3.yaml` for hyperparameters and writes the
model artifact to `models/lgbm_v3.pkl`.

## Evaluation

    python evaluate.py --model models/lgbm_v3.pkl --split test

Reports AUC, precision@10%, and a calibration plot saved to `reports/`.

## Results

| Model | AUC | Precision@10% |
|---|---|---|
| Baseline (logistic regression) | 0.81 | 0.42 |
| lgbm_v3 | 0.89 | 0.61 |

## Reproducing Results

    pip install -r requirements.txt
    python train.py --config configs/lgbm_v3.yaml --seed 42
    python evaluate.py --model models/lgbm_v3.pkl --split test

Results above use `seed=42` and the `test` split fixed in `data/splits.json`.

## Citation

If you use this model, please cite the internal report `RET-2025-014`.

## License

Internal use only.
```

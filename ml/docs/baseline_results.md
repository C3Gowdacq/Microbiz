# Baseline Model Results — Rossmann Sales Prediction

Comparison of classical ML baselines on processed Rossmann data.
These results serve as the benchmark against which the VAE model will be compared.

| Model | Split | MAE | MSE | RMSE | MAPE (%) | R² | Train Time (s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| LinearRegression | Val | 1,025.44 | 1,876,366.60 | 1,369.81 | 15.73 | 0.797799 | 1.06 |
| LinearRegression | Test | 968.77 | 1,818,544.00 | 1,348.53 | 15.48 | 0.805108 | 1.06 |
| RandomForest | Val | 721.79 | 964,809.92 | 982.25 | 10.73 | 0.896030 | 31.99 |
| RandomForest | Test | 676.89 | 988,513.93 | 994.24 | 10.29 | 0.894062 | 31.99 |
| XGBoost | Val | 736.99 | 1,007,787.62 | 1,003.89 | 11.03 | 0.891399 | 7.70 |
| XGBoost | Test | 718.62 | 1,096,156.38 | 1,046.97 | 10.92 | 0.882526 | 7.70 |
| GradientBoosting | Val | 812.21 | 1,257,952.45 | 1,121.58 | 12.05 | 0.864440 | 479.41 |
| GradientBoosting | Test | 763.93 | 1,231,545.41 | 1,109.75 | 11.72 | 0.868016 | 479.41 |


> RandomForest model file size: 327.4 MB (constrained: max_depth=20, min_samples_leaf=5, compress=3)
> Generated on: 2026-08-11 23:12:18

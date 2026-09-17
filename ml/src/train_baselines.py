"""
train_baselines.py — Baseline regression models on processed Rossmann data.
Trains LinearRegression, RandomForest, XGBoost, and GradientBoosting,
evaluates on val/test splits, saves models and a markdown results table.
"""

import os
import time
import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor


# ── Column groups (must match preprocess_rossmann.py output exactly) ─────────

X_cols = [
    "Promo", "Promo2", "promo_period_length", "SchoolHoliday",
    "day_of_week", "month", "is_weekend",
    "rolling_avg_7", "rolling_avg_30", "sales_growth",
    "StateHoliday_a", "StateHoliday_b", "StateHoliday_c", "StateHoliday_none",
]

A_cols = [
    "StoreType_a", "StoreType_b", "StoreType_c", "StoreType_d",
    "Assortment_a", "Assortment_b", "Assortment_c",
]

B_cols = [
    "CompetitionDistance", "competition_open_days",
    "has_competition_data", "has_promo2_data",
]

FEATURE_COLS = X_cols + A_cols + B_cols
TARGET_COL = "Sales"


# ── Metric helpers ───────────────────────────────────────────────────────────

def compute_metrics(y_true, y_pred):
    """Return dict of MAE, MSE, RMSE, MAPE, R² for given arrays."""
    mae = mean_absolute_error(y_true, y_pred)
    mse = mean_squared_error(y_true, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_true, y_pred)

    # MAPE: skip rows where actual Sales == 0
    nonzero_mask = y_true != 0
    skipped = (~nonzero_mask).sum()
    if nonzero_mask.sum() > 0:
        mape = np.mean(np.abs((y_true[nonzero_mask] - y_pred[nonzero_mask]) / y_true[nonzero_mask])) * 100
    else:
        mape = float("nan")

    return {
        "MAE": mae,
        "MSE": mse,
        "RMSE": rmse,
        "MAPE": mape,
        "R²": r2,
        "MAPE_skipped_rows": int(skipped),
    }


def print_feature_importances(name, importances, feature_names, top_n=15):
    """Print top-N feature importances for tree-based models."""
    indices = np.argsort(importances)[::-1][:top_n]
    print(f"\n{'='*55}")
    print(f"Top {top_n} Feature Importances — {name}")
    print(f"{'='*55}")
    print(f"{'Rank':<6}{'Feature':<30}{'Importance':<12}")
    print("-" * 48)
    for rank, idx in enumerate(indices, 1):
        print(f"{rank:<6}{feature_names[idx]:<30}{importances[idx]:<12.6f}")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    processed_dir = os.path.join("ml", "data", "processed")

    # 1. Load splits
    print("Loading processed parquet splits...")
    train_df = pd.read_parquet(os.path.join(processed_dir, "rossmann_train.parquet"))
    val_df   = pd.read_parquet(os.path.join(processed_dir, "rossmann_val.parquet"))
    test_df  = pd.read_parquet(os.path.join(processed_dir, "rossmann_test.parquet"))

    print(f"  Train rows: {len(train_df):,}")
    print(f"  Val   rows: {len(val_df):,}")
    print(f"  Test  rows: {len(test_df):,}")

    # 2. Build flat feature matrices
    X_train = train_df[FEATURE_COLS].values
    y_train = train_df[TARGET_COL].values
    X_val   = val_df[FEATURE_COLS].values
    y_val   = val_df[TARGET_COL].values
    X_test  = test_df[FEATURE_COLS].values
    y_test  = test_df[TARGET_COL].values

    print(f"  Feature columns ({len(FEATURE_COLS)}): {FEATURE_COLS}")

    # 3. Define models
    models = {
        "LinearRegression": LinearRegression(),
        "RandomForest": RandomForestRegressor(
            n_estimators=200, max_depth=20, min_samples_leaf=5,
            max_features="sqrt", random_state=42, n_jobs=-1
        ),
        "XGBoost": XGBRegressor(
            n_estimators=300, learning_rate=0.05, max_depth=6, random_state=42
        ),
        "GradientBoosting": GradientBoostingRegressor(
            n_estimators=200, random_state=42
        ),
    }

    # Model save directory
    model_dir = os.path.join("ml", "models", "baselines")
    os.makedirs(model_dir, exist_ok=True)

    # Results collector
    results_rows = []

    # 4. Train & evaluate each model
    for name, model in models.items():
        print(f"\n{'='*55}")
        print(f"Training: {name}")
        print(f"{'='*55}")

        t0 = time.time()
        model.fit(X_train, y_train)
        train_time = time.time() - t0
        print(f"  Training time: {train_time:.2f}s")

        # Save model
        if name == "XGBoost":
            save_path = os.path.join(model_dir, "xgboost.json")
            model.save_model(save_path) #type:ignore[union-attr]
        else:
            safe_name = name.lower().replace(" ", "_")
            # Map friendly names to file names
            file_map = {
                "linearregression": "linear_regression.pkl",
                "randomforest": "random_forest.pkl",
                "gradientboosting": "gradient_boosting.pkl",
            }
            save_path = os.path.join(model_dir, file_map.get(safe_name, f"{safe_name}.pkl"))
            joblib.dump(model, save_path, compress=3)
        print(f"  Saved to: {save_path}")

        # Evaluate on val and test
        for split_name, X_split, y_split in [("Val", X_val, y_val), ("Test", X_test, y_test)]:
            y_pred = model.predict(X_split)
            metrics = compute_metrics(y_split, y_pred)
            print(f"\n  {split_name} Metrics:")
            print(f"    MAE  = {metrics['MAE']:,.2f}")
            print(f"    MSE  = {metrics['MSE']:,.2f}")
            print(f"    RMSE = {metrics['RMSE']:,.2f}")
            print(f"    MAPE = {metrics['MAPE']:.2f}% (skipped {metrics['MAPE_skipped_rows']} zero-sales rows)")
            print(f"    R²   = {metrics['R²']:.6f}")

            results_rows.append({
                "Model": name,
                "Split": split_name,
                "MAE": f"{metrics['MAE']:,.2f}",
                "MSE": f"{metrics['MSE']:,.2f}",
                "RMSE": f"{metrics['RMSE']:,.2f}",
                "MAPE (%)": f"{metrics['MAPE']:.2f}",
                "R²": f"{metrics['R²']:.6f}",
                "Train Time (s)": f"{train_time:.2f}",
            })

    # 5. Feature importances for RF and XGBoost
    rf_model = models["RandomForest"]
    xgb_model = models["XGBoost"]
    print_feature_importances("RandomForest", rf_model.feature_importances_, FEATURE_COLS)
    print_feature_importances("XGBoost", xgb_model.feature_importances_, FEATURE_COLS)

    # 6. Build comparison table & save markdown
    results_df = pd.DataFrame(results_rows)

    print(f"\n{'='*55}")
    print("BASELINE COMPARISON TABLE")
    print(f"{'='*55}")
    header = "| " + " | ".join(results_df.columns) + " |"
    sep = "| " + " | ".join(["---"] * len(results_df.columns)) + " |"
    print(header)
    print(sep)
    for _, row in results_df.iterrows():
        print("| " + " | ".join(str(v) for v in row.values) + " |")

    # Save to markdown
    docs_dir = os.path.join("ml", "docs")
    os.makedirs(docs_dir, exist_ok=True)
    md_path = os.path.join(docs_dir, "baseline_results.md")
    with open(md_path, "w") as f:
        f.write("# Baseline Model Results — Rossmann Sales Prediction\n\n")
        f.write("Comparison of classical ML baselines on processed Rossmann data.\n")
        f.write("These results serve as the benchmark against which the VAE model will be compared.\n\n")
        f.write(header + "\n")
        f.write(sep + "\n")
        for _, row in results_df.iterrows():
            f.write("| " + " | ".join(str(v) for v in row.values) + " |\n")
        f.write(f"\n> Generated on: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    print(f"\nSaved results table to: {md_path}")

    print("\n[DONE] All baselines trained, evaluated, and saved successfully.")


if __name__ == "__main__":
    main()

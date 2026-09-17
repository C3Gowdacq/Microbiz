"""
fix_random_forest.py — Retrain RF with constrained depth, save compressed, update results.
"""
import os
import time
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Column groups (same as train_baselines.py)
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


def compute_metrics(y_true, y_pred):
    mae = mean_absolute_error(y_true, y_pred)
    mse = mean_squared_error(y_true, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_true, y_pred)
    nonzero = y_true != 0
    skipped = (~nonzero).sum()
    mape = np.mean(np.abs((y_true[nonzero] - y_pred[nonzero]) / y_true[nonzero])) * 100 if nonzero.sum() > 0 else float("nan")
    return {"MAE": mae, "MSE": mse, "RMSE": rmse, "MAPE": mape, "R2": r2, "skipped": int(skipped)}


def main():
    processed_dir = os.path.join("ml", "data", "processed")
    model_dir = os.path.join("ml", "models", "baselines")
    old_path = os.path.join(model_dir, "random_forest.pkl")

    # 1. Delete old oversized model
    if os.path.exists(old_path):
        old_size_mb = os.path.getsize(old_path) / (1024 * 1024)
        print(f"Deleting old random_forest.pkl ({old_size_mb:,.1f} MB)...")
        os.remove(old_path)
        print("  Deleted.")
    else:
        print("Old random_forest.pkl not found, proceeding to train.")

    # 2. Load data
    print("\nLoading processed parquet splits...")
    train_df = pd.read_parquet(os.path.join(processed_dir, "rossmann_train.parquet"))
    val_df   = pd.read_parquet(os.path.join(processed_dir, "rossmann_val.parquet"))
    test_df  = pd.read_parquet(os.path.join(processed_dir, "rossmann_test.parquet"))

    X_train = train_df[FEATURE_COLS].values
    y_train = train_df[TARGET_COL].values
    X_val   = val_df[FEATURE_COLS].values
    y_val   = val_df[TARGET_COL].values
    X_test  = test_df[FEATURE_COLS].values
    y_test  = test_df[TARGET_COL].values

    print(f"  Train: {len(train_df):,} rows | Val: {len(val_df):,} rows | Test: {len(test_df):,} rows")

    # 3. Retrain with constrained parameters
    print("\nTraining RandomForest (max_depth=20, min_samples_leaf=5, max_features='sqrt')...")
    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=20,
        min_samples_leaf=5,
        max_features="sqrt",
        random_state=42,
        n_jobs=-1,
    )
    t0 = time.time()
    model.fit(X_train, y_train)
    train_time = time.time() - t0
    print(f"  Training time: {train_time:.2f}s")

    # 4. Save with compression
    print(f"\nSaving with compress=3...")
    joblib.dump(model, old_path, compress=3)
    new_size_mb = os.path.getsize(old_path) / (1024 * 1024)
    print(f"  New file size: {new_size_mb:,.1f} MB")

    # 5. Evaluate on val and test
    print("\n" + "=" * 55)
    print("COMPARISON: Old (unconstrained) vs New (constrained) RF")
    print("=" * 55)

    old_results = {
        "Val":  {"MAE": 725.29, "RMSE": 983.65, "MAPE": 10.49, "R2": 0.895733},
        "Test": {"MAE": 673.14, "RMSE": 998.96, "MAPE": 9.97,  "R2": 0.893053},
    }

    new_results = {}
    for split_name, X_split, y_split in [("Val", X_val, y_val), ("Test", X_test, y_test)]:
        y_pred = model.predict(X_split)
        m = compute_metrics(y_split, y_pred)
        new_results[split_name] = m

        old = old_results[split_name]
        print(f"\n  {split_name} Split:")
        print(f"    {'Metric':<8} {'Old (unconstrained)':<22} {'New (constrained)':<22} {'Delta':<12}")
        print(f"    {'-'*64}")
        print(f"    {'MAE':<8} {old['MAE']:<22,.2f} {m['MAE']:<22,.2f} {m['MAE'] - old['MAE']:+,.2f}")
        print(f"    {'RMSE':<8} {old['RMSE']:<22,.2f} {m['RMSE']:<22,.2f} {m['RMSE'] - old['RMSE']:+,.2f}")
        print(f"    {'MAPE%':<8} {old['MAPE']:<22.2f} {m['MAPE']:<22.2f} {m['MAPE'] - old['MAPE']:+.2f}")
        print(f"    {'R2':<8} {old['R2']:<22.6f} {m['R2']:<22.6f} {m['R2'] - old['R2']:+.6f}")

    # 6. Update baseline_results.md
    docs_dir = os.path.join("ml", "docs")
    md_path = os.path.join(docs_dir, "baseline_results.md")

    # Read existing results, replace RF rows
    with open(md_path, "r") as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        if line.startswith("| RandomForest"):
            # skip old RF rows — we'll add new ones after all non-RF rows
            continue
        new_lines.append(line)

    # Find the position to insert RF rows (after LinearRegression rows)
    insert_idx = None
    for i, line in enumerate(new_lines):
        if line.startswith("| LinearRegression | Test"):
            insert_idx = i + 1
            break

    val_m = new_results["Val"]
    test_m = new_results["Test"]
    rf_val_line  = f"| RandomForest | Val | {val_m['MAE']:,.2f} | {val_m['MSE']:,.2f} | {val_m['RMSE']:,.2f} | {val_m['MAPE']:.2f} | {val_m['R2']:.6f} | {train_time:.2f} |\n"
    rf_test_line = f"| RandomForest | Test | {test_m['MAE']:,.2f} | {test_m['MSE']:,.2f} | {test_m['RMSE']:,.2f} | {test_m['MAPE']:.2f} | {test_m['R2']:.6f} | {train_time:.2f} |\n"

    if insert_idx is not None:
        new_lines.insert(insert_idx, rf_test_line)
        new_lines.insert(insert_idx, rf_val_line)
    else:
        # fallback: append before the Generated line
        for i, line in enumerate(new_lines):
            if line.startswith(">"):
                new_lines.insert(i, rf_val_line)
                new_lines.insert(i + 1, rf_test_line)
                break

    # Add file size note
    size_note = f"\n> RandomForest model file size: {new_size_mb:,.1f} MB (constrained: max_depth=20, min_samples_leaf=5, compress=3)\n"
    # Insert before the Generated line
    for i, line in enumerate(new_lines):
        if line.startswith("> Generated"):
            new_lines.insert(i, size_note)
            break

    with open(md_path, "w") as f:
        f.writelines(new_lines)

    print(f"\nUpdated {md_path}")
    print(f"\n[DONE] RandomForest retrained and saved. New size: {new_size_mb:,.1f} MB")


if __name__ == "__main__":
    main()

import os
import joblib
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler

def resolve_path(relative_path):
    """
    Resolves a path in ml/data/raw, supporting 'rossman' or 'rossmann' folder names.
    """
    base_dir = os.path.join("ml", "data", "raw")
    primary = os.path.join(base_dir, relative_path)
    if os.path.exists(primary):
        return primary
    if relative_path.startswith("rossmann/"):
        alt = os.path.join(base_dir, relative_path.replace("rossmann/", "rossman/", 1))
        if os.path.exists(alt):
            return alt
    raise FileNotFoundError(f"Cannot find dataset at {primary}")

def main():
    print("==================================================")
    print("STEP 1: Loading & Merging Rossmann Datasets")
    print("==================================================")
    
    train_path = resolve_path("rossmann/train.csv")
    store_path = resolve_path("rossmann/store.csv")
    
    print(f"Loading train dataset from: {train_path}")
    train_df = pd.read_csv(train_path, low_memory=False)
    
    print(f"Loading store dataset from: {store_path}")
    store_df = pd.read_csv(store_path)
    
    # Merge train and store on 'Store' using left join
    df = pd.merge(train_df, store_df, on="Store", how="left")
    print(f"Merged dataset shape: {df.shape}")

    print("\n==================================================")
    print("STEP 2: Cleaning Data")
    print("==================================================")
    
    # 2.1 Convert 'Date' to datetime
    df["Date"] = pd.to_datetime(df["Date"])
    
    # 2.2 Normalize StateHoliday to clean categorical
    # Map {0, '0'} -> 'none', keep 'a', 'b', 'c'; explicitly cast to str to eliminate mixed-type warnings
    df["StateHoliday"] = df["StateHoliday"].astype(str).replace({"0": "none", "0.0": "none", "nan": "none"})
    
    # 2.3 Filter out rows where Open == 0
    # Closed stores have Sales == 0 by definition and would just add noise to demand forecasting & VAE training.
    closed_count = (df["Open"] == 0).sum()
    print(f"Filtering out {closed_count} closed store records (Open == 0)...")
    df = df[df["Open"] == 1].copy()
    
    # 2.4 Handle store.csv nulls with boolean indicator flags before filling
    df["has_competition_data"] = df["CompetitionDistance"].notnull().astype(int)
    df["has_promo2_data"] = df["Promo2SinceYear"].notnull().astype(int)
    
    # Fill CompetitionDistance with max distance in data (signifying no known competitor nearby)
    max_comp_dist = df["CompetitionDistance"].max()
    if pd.isnull(max_comp_dist):
        max_comp_dist = 100000.0
    df["CompetitionDistance"] = df["CompetitionDistance"].fillna(max_comp_dist)
    
    # Fill month/year and promo2 start nulls with 0
    df["CompetitionOpenSinceMonth"] = df["CompetitionOpenSinceMonth"].fillna(0).astype(int)
    df["CompetitionOpenSinceYear"] = df["CompetitionOpenSinceYear"].fillna(0).astype(int)
    df["Promo2SinceWeek"] = df["Promo2SinceWeek"].fillna(0).astype(int)
    df["Promo2SinceYear"] = df["Promo2SinceYear"].fillna(0).astype(int)
    df["PromoInterval"] = df["PromoInterval"].fillna("none")
    
    # 2.5 Drop duplicates if any
    dupes = df.duplicated().sum()
    if dupes > 0:
        print(f"Dropping {dupes} duplicate rows...")
        df.drop_duplicates(inplace=True)
        
    print(f"Dataset shape after cleaning: {df.shape}")

    print("\n==================================================")
    print("STEP 3: Vectorized Feature Engineering")
    print("==================================================")
    
    # Sort by Store and Date for time-series features
    df.sort_values(by=["Store", "Date"], inplace=True)
    df.reset_index(drop=True, inplace=True)
    
    # Calendar features
    df["day_of_week"] = df["Date"].dt.dayofweek
    df["month"] = df["Date"].dt.month
    df["year"] = df["Date"].dt.year
    df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)
    
    # Vectorized promo_period_length calculation
    print("Computing promo_period_length (vectorized)...")
    df["promo_period_length"] = 0
    has_promo2 = (df["Promo2"] == 1) & (df["Promo2SinceYear"] > 0) & (df["Promo2SinceWeek"] > 0)
    if has_promo2.any():
        p2_years = df.loc[has_promo2, "Promo2SinceYear"].astype(str)
        p2_weeks = df.loc[has_promo2, "Promo2SinceWeek"].astype(str).str.zfill(2)
        p2_dates = pd.to_datetime(p2_years + "-W" + p2_weeks + "-1", format="%G-W%V-%u", errors="coerce")
        p2_days = (df.loc[has_promo2, "Date"] - p2_dates).dt.days.clip(lower=0).fillna(0)
        df.loc[has_promo2, "promo_period_length"] = p2_days.astype(int)

    # Vectorized competition_open_days calculation
    print("Computing competition_open_days (vectorized)...")
    df["competition_open_days"] = 0
    has_comp = (df["has_competition_data"] == 1) & (df["CompetitionOpenSinceYear"] > 0) & (df["CompetitionOpenSinceMonth"] > 0)
    if has_comp.any():
        c_years = df.loc[has_comp, "CompetitionOpenSinceYear"].astype(str)
        c_months = df.loc[has_comp, "CompetitionOpenSinceMonth"].astype(str).str.zfill(2)
        c_dates = pd.to_datetime(c_years + "-" + c_months + "-15", format="%Y-%m-%d", errors="coerce")
        c_days = (df.loc[has_comp, "Date"] - c_dates).dt.days.clip(lower=0).fillna(0)
        df.loc[has_comp, "competition_open_days"] = c_days.astype(int)

    # rolling_avg_7 and rolling_avg_30: shift(1) to avoid target leakage!
    print("Computing past rolling averages (7-day & 30-day)...")
    df["rolling_avg_7"] = df.groupby("Store")["Sales"].transform(lambda x: x.shift(1).rolling(7, min_periods=1).mean()).fillna(0)
    df["rolling_avg_30"] = df.groupby("Store")["Sales"].transform(lambda x: x.shift(1).rolling(30, min_periods=1).mean()).fillna(0)
    
    # sales_growth: (past 1-day sales - 7-day-ago sales) / (7-day-ago sales) per store
    print("Computing sales growth rate...")
    sales_shift1 = df.groupby("Store")["Sales"].shift(1)
    sales_shift8 = df.groupby("Store")["Sales"].shift(8)
    df["sales_growth"] = ((sales_shift1 - sales_shift8) / (sales_shift8 + 1.0)).fillna(0)

    print("\n==================================================")
    print("STEP 4: One-Hot Encoding")
    print("==================================================")
    
    categorical_cols = ["StoreType", "Assortment", "StateHoliday"]
    df = pd.get_dummies(df, columns=categorical_cols, dtype=int)

    print("\n==================================================")
    print("STEP 5: Structuring Columns into X, A, B, y")
    print("==================================================")
    
    # Find generated dummy columns
    state_holiday_cols = [c for c in df.columns if c.startswith("StateHoliday_")]
    store_type_cols = [c for c in df.columns if c.startswith("StoreType_")]
    assortment_cols = [c for c in df.columns if c.startswith("Assortment_")]
    
    # Group X (Global group-level / promo + period attributes & temporal features)
    X_cols = [
        "Promo", "Promo2", "promo_period_length", "SchoolHoliday",
        "day_of_week", "month", "is_weekend", "rolling_avg_7", "rolling_avg_30", "sales_growth"
    ] + state_holiday_cols
    
    # Group A (Functional store attributes)
    A_cols = store_type_cols + assortment_cols
    
    # Group B (Non-functional store attributes)
    B_cols = ["CompetitionDistance", "competition_open_days", "has_competition_data", "has_promo2_data"]
    
    # Target y
    y_col = ["Sales"]
    
    print("--- Column Groups ---")
    print(f"X (Global / Temporal / Promo attrs): {X_cols}")
    print(f"A (Functional store attrs):         {A_cols}")
    print(f"B (Non-functional store attrs):     {B_cols}")
    print(f"y (Target):                         {y_col}")

    print("\n==================================================")
    print("STEP 6: Chronological Train / Val / Test Split")
    print("==================================================")
    
    # Sort strictly by Date
    df.sort_values(by="Date", inplace=True)
    df.reset_index(drop=True, inplace=True)
    
    max_date = df["Date"].max()
    test_cutoff = max_date - pd.Timedelta(days=42)  # Last 6 weeks (~42 days)
    val_cutoff = test_cutoff - pd.Timedelta(days=42)  # Prior 6 weeks (~42 days)
    
    train_df = df[df["Date"] <= val_cutoff].copy()
    val_df = df[(df["Date"] > val_cutoff) & (df["Date"] <= test_cutoff)].copy()
    test_df = df[df["Date"] > test_cutoff].copy()

    print(f"Train split range: {train_df['Date'].min().strftime('%Y-%m-%d')} to {train_df['Date'].max().strftime('%Y-%m-%d')} | Rows: {len(train_df)}")
    print(f"Val split range:   {val_df['Date'].min().strftime('%Y-%m-%d')} to {val_df['Date'].max().strftime('%Y-%m-%d')}   | Rows: {len(val_df)}")
    print(f"Test split range:  {test_df['Date'].min().strftime('%Y-%m-%d')} to {test_df['Date'].max().strftime('%Y-%m-%d')}  | Rows: {len(test_df)}")

    print("\n==================================================")
    print("STEP 7: Fitting StandardScaler on TRAIN Split Only")
    print("==================================================")
    
    numeric_scale_cols = [
        "promo_period_length", "rolling_avg_7", "rolling_avg_30", "sales_growth",
        "CompetitionDistance", "competition_open_days"
    ]
    
    scaler = StandardScaler()
    scaler.fit(train_df[numeric_scale_cols])
    
    # Transform numeric columns across all splits
    train_df[numeric_scale_cols] = scaler.transform(train_df[numeric_scale_cols])
    val_df[numeric_scale_cols] = scaler.transform(val_df[numeric_scale_cols])
    test_df[numeric_scale_cols] = scaler.transform(test_df[numeric_scale_cols])
    
    processed_dir = os.path.join("ml", "data", "processed")
    os.makedirs(processed_dir, exist_ok=True)
    scaler_path = os.path.join(processed_dir, "scaler.pkl")
    joblib.dump(scaler, scaler_path)
    print(f"Saved fitted StandardScaler to {scaler_path}")

    print("\n==================================================")
    print("STEP 8: Saving Processed Datasets to Parquet")
    print("==================================================")
    
    # Save parquet files
    train_parquet = os.path.join(processed_dir, "rossmann_train.parquet")
    val_parquet = os.path.join(processed_dir, "rossmann_val.parquet")
    test_parquet = os.path.join(processed_dir, "rossmann_test.parquet")
    
    train_df.to_parquet(train_parquet, index=False)
    val_df.to_parquet(val_parquet, index=False)
    test_df.to_parquet(test_parquet, index=False)
    
    print(f"Saved {train_parquet}")
    print(f"Saved {val_parquet}")
    print(f"Saved {test_parquet}")

    print("\n==================================================")
    print("STEP 9: Final Pipeline Summary & Quality Checks")
    print("==================================================")
    
    all_pipeline_cols = X_cols + A_cols + B_cols + y_col
    
    train_nans = train_df[all_pipeline_cols].isnull().sum().sum()
    val_nans = val_df[all_pipeline_cols].isnull().sum().sum()
    test_nans = test_df[all_pipeline_cols].isnull().sum().sum()
    
    summary_table = pd.DataFrame([
        {
            "Split": "Train",
            "Rows": len(train_df),
            "Start Date": train_df["Date"].min().strftime("%Y-%m-%d"),
            "End Date": train_df["Date"].max().strftime("%Y-%m-%d"),
            "NaN Count": train_nans
        },
        {
            "Split": "Validation",
            "Rows": len(val_df),
            "Start Date": val_df["Date"].min().strftime("%Y-%m-%d"),
            "End Date": val_df["Date"].max().strftime("%Y-%m-%d"),
            "NaN Count": val_nans
        },
        {
            "Split": "Test",
            "Rows": len(test_df),
            "Start Date": test_df["Date"].min().strftime("%Y-%m-%d"),
            "End Date": test_df["Date"].max().strftime("%Y-%m-%d"),
            "NaN Count": test_nans
        }
    ])
    
    print(f"| {' | '.join(summary_table.columns)} |")
    print(f"| {' | '.join(['---'] * len(summary_table.columns))} |")
    for _, row in summary_table.iterrows():
        print(f"| {' | '.join([str(val) for val in row.values])} |")
        
    print(f"\nNaN Check Result: {'PASSED (Zero NaNs)' if (train_nans + val_nans + test_nans) == 0 else 'FAILED'}")
    print("==================================================")

if __name__ == "__main__":
    main()

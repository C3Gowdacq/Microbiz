"""
columns.py — Single source of truth for X, A, B, y column groups.
All scripts (preprocessing, baselines, VAE) import from here
to avoid hardcoding column lists in multiple places.
"""

# Group X: Global / temporal / promo attributes
X_COLS = [
    "Promo", "Promo2", "promo_period_length", "SchoolHoliday",
    "day_of_week", "month", "is_weekend",
    "rolling_avg_7", "rolling_avg_30", "sales_growth",
    "StateHoliday_a", "StateHoliday_b", "StateHoliday_c", "StateHoliday_none",
]

# Group A: Functional store attributes (store type, assortment)
A_COLS = [
    "StoreType_a", "StoreType_b", "StoreType_c", "StoreType_d",
    "Assortment_a", "Assortment_b", "Assortment_c",
]

# Group B: Non-functional store attributes (competition, promo2 metadata)
B_COLS = [
    "CompetitionDistance", "competition_open_days",
    "has_competition_data", "has_promo2_data",
]

# Target
Y_COL = "Sales"

# Convenience: all feature columns concatenated
FEATURE_COLS = X_COLS + A_COLS + B_COLS

# Numeric columns that get StandardScaler treatment (must match preprocess_rossmann.py)
NUMERIC_SCALE_COLS = [
    "promo_period_length", "rolling_avg_7", "rolling_avg_30", "sales_growth",
    "CompetitionDistance", "competition_open_days",
]

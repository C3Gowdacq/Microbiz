"""
sales_agent.py -- Thin wrapper around the trained Random Forest baseline
for use by downstream agents (Inventory, Cash Flow, etc.).

Provides:
  - predict(feature_rows) -> np.ndarray of predicted daily Sales
  - get_multi_day_forecast(feature_row, days=7) -> float total demand

KNOWN LIMITATION (document in project report):
  get_multi_day_forecast() is a simplification: it applies a 1-day forecasting
  model repeatedly (once per day, rolling day_of_week and is_weekend forward)
  rather than using a true multi-step or sequence-to-sequence forecaster.
  This is adequate for the proof-of-concept agent pipeline but would need to be
  replaced with an actual multi-horizon model for production use.
"""

import os
import sys
import copy
import joblib
import numpy as np
import pandas as pd

# Ensure columns.py is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from columns import FEATURE_COLS


# ── Lazy-loaded singleton RF model ───────────────────────────────────────────

_rf_model = None


def _load_rf():
    """Load the Random Forest model on first use."""
    global _rf_model
    if _rf_model is None:
        model_path = os.path.join("ml", "models", "baselines", "random_forest.pkl")
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Random Forest model not found at {model_path}. "
                f"Run train_baselines.py first."
            )
        _rf_model = joblib.load(model_path)
    return _rf_model


# ── Public API ───────────────────────────────────────────────────────────────

def predict(feature_rows):
    """
    Predict daily Sales for one or more rows using the trained Random Forest.

    Args:
        feature_rows: np.ndarray of shape (N, len(FEATURE_COLS)), or a
                      pd.DataFrame containing at least those columns.

    Returns:
        np.ndarray of shape (N,) with predicted daily Sales in raw Euros.
    """
    model = _load_rf()

    if isinstance(feature_rows, pd.DataFrame):
        X = feature_rows[FEATURE_COLS].values
    else:
        X = np.asarray(feature_rows, dtype=np.float64)

    return model.predict(X)


def predict_from_df(df):
    """
    Convenience: takes a DataFrame with the standard column names and
    returns predictions as a 1-D numpy array.
    """
    return predict(df[FEATURE_COLS].values)


def get_multi_day_forecast(base_feature_row, days=7):
    """
    Produce a cumulative demand forecast over `days` future days by
    repeatedly calling the 1-day Random Forest model.

    For each successive day d in [0, days):
      - day_of_week is rolled forward: (base_dow + d) % 7
      - is_weekend is recomputed: 1 if rolled dow in {5, 6}, else 0

    All other features (Promo, rolling averages, competition, etc.) are held
    constant from the base row, which is a simplification — in reality these
    would update daily.

    KNOWN LIMITATION:
      This is NOT a true multi-day forecasting model.  It repeatedly applies a
      single-day model with synthetic day-of-week shifts.  Rolling averages and
      promotional flags are frozen at their base-row values.  This is acceptable
      for the agent proof-of-concept but should be replaced with a proper
      multi-horizon approach for production.

    Args:
        base_feature_row: np.ndarray of shape (len(FEATURE_COLS),) or (1, len(FEATURE_COLS)).
                          Can also be a pd.Series with FEATURE_COLS.
        days: int, number of days to forecast (default 7).

    Returns:
        float: total cumulative predicted demand over the horizon.
    """
    # Resolve to a 1-D numpy array
    if isinstance(base_feature_row, pd.Series):
        row = base_feature_row[FEATURE_COLS].values.astype(np.float64).copy()
    elif isinstance(base_feature_row, pd.DataFrame):
        row = base_feature_row[FEATURE_COLS].values[0].astype(np.float64).copy()
    else:
        row = np.asarray(base_feature_row, dtype=np.float64).flatten().copy()

    # Locate the indices of the columns we need to mutate
    dow_idx = FEATURE_COLS.index("day_of_week")
    weekend_idx = FEATURE_COLS.index("is_weekend")

    base_dow = int(row[dow_idx])
    total_demand = 0.0

    model = _load_rf()
    for d in range(days):
        future_row = row.copy()
        future_dow = (base_dow + d) % 7
        future_row[dow_idx] = future_dow
        future_row[weekend_idx] = 1 if future_dow in (5, 6) else 0

        pred = model.predict(future_row.reshape(1, -1))[0]
        total_demand += max(0.0, pred)  # clamp negative predictions

    return total_demand

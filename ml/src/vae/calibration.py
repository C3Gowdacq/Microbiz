"""
calibration.py -- Offline calibration for the Reconstructed VAE (training-time only).

Implements bucket-mean calibration per the paper's Eq. 17:
  y_calibrated = y * eta + y_mean * (1 - eta)

ADAPTATION NOTE (Rossmann vs. paper's dataset):
  The base paper uses explicit "discount %" and "discount period" fields to define
  calibration buckets. Rossmann doesn't have these fields directly, so we adapt:
    - "discount" proxy: Promo (0/1 binary flag) — coarse but available
    - "period" proxy:   promo_period_length (days since Promo2 start, bucketed)
  This is a necessary substitution, not a literal match to the paper's definitions.
  The calibration logic (bucket means + fallback hierarchy) follows the paper exactly;
  only the input columns differ.

References:
  - Base paper Eq. 17
  - MicroBizAI_Architecture.md Section 5.4
"""

import numpy as np
import pandas as pd


def compute_bucket_means(train_df, discount_col="Promo", period_col="promo_period_length",
                         sales_col="Sales", period_bin=8):
    """
    Compute mean sales per (discount_bucket, period_bucket) from the training split.

    Args:
        train_df:     training DataFrame (processed, with scaled features)
        discount_col: column to use as discount proxy (default: Promo, 0/1)
        period_col:   column to use as period proxy (default: promo_period_length)
        sales_col:    target column (default: Sales)
        period_bin:   bin width for period bucketing (default: 8)

    Returns:
        dict with keys:
          'full':           Series mapping (discount_bucket, period_bucket) -> mean sales
          'period_only':    Series mapping period_bucket -> mean sales
          'discount_only':  Series mapping discount_bucket -> mean sales
          'global_mean':    scalar, global mean sales
          'period_bin':     bin width used
    """
    df = train_df[[discount_col, period_col, sales_col]].copy()

    # Discount bucket: Promo is already 0/1, use directly
    df["discount_bucket"] = df[discount_col].astype(int)

    # Period bucket: bin promo_period_length
    # For scaled values, floor(value / bin_width) gives consistent bucket IDs
    df["period_bucket"] = (df[period_col] / max(period_bin, 1e-6)).apply(np.floor).astype(int)

    # Compute bucket means at each level of the fallback hierarchy
    full_means = df.groupby(["discount_bucket", "period_bucket"])[sales_col].mean()
    period_means = df.groupby("period_bucket")[sales_col].mean()
    discount_means = df.groupby("discount_bucket")[sales_col].mean()
    global_mean = df[sales_col].mean()

    return {
        "full": full_means,
        "period_only": period_means,
        "discount_only": discount_means,
        "global_mean": float(global_mean),
        "period_bin": period_bin,
    }


def get_y_mean(discount_bucket, period_bucket, bucket_table):
    """
    Look up mean sales for a given (discount, period) bucket with fallback.

    Fallback hierarchy (per the paper):
      1. Same discount + period bucket (exact match)
      2. Same period bucket only
      3. Same discount bucket only
      4. Global mean (final fallback)

    Args:
        discount_bucket: int, discount bucket ID
        period_bucket:   int, period bucket ID
        bucket_table:    dict from compute_bucket_means()

    Returns:
        float: the looked-up mean sales value
    """
    # Level 1: exact (discount, period) match
    key = (discount_bucket, period_bucket)
    if key in bucket_table["full"]:
        return float(bucket_table["full"][key])

    # Level 2: same period only
    if period_bucket in bucket_table["period_only"]:
        return float(bucket_table["period_only"][period_bucket])

    # Level 3: same discount only
    if discount_bucket in bucket_table["discount_only"]:
        return float(bucket_table["discount_only"][discount_bucket])

    # Level 4: global mean
    return bucket_table["global_mean"]


def compute_y_mean_array(df, bucket_table, discount_col="Promo",
                         period_col="promo_period_length", period_bin=8):
    """
    Vectorized computation of y_mean for every row in a DataFrame.

    Uses merge-based lookup instead of row-by-row iteration for speed.

    Args:
        df:           DataFrame to compute y_mean for
        bucket_table: dict from compute_bucket_means()
        discount_col: discount proxy column
        period_col:   period proxy column
        period_bin:   bin width (must match compute_bucket_means)

    Returns:
        np.ndarray of shape (len(df),) with y_mean per row
    """
    temp = df[[discount_col, period_col]].copy()
    temp["discount_bucket"] = temp[discount_col].astype(int)
    temp["period_bucket"] = (temp[period_col] / max(period_bin, 1e-6)).apply(np.floor).astype(int)

    # Level 1: exact match via merge
    full_df = bucket_table["full"].reset_index()
    full_df.columns = ["discount_bucket", "period_bucket", "y_mean_full"]
    temp = temp.merge(full_df, on=["discount_bucket", "period_bucket"], how="left")

    # Level 2: period-only fallback
    period_df = bucket_table["period_only"].reset_index()
    period_df.columns = ["period_bucket", "y_mean_period"]
    temp = temp.merge(period_df, on="period_bucket", how="left")

    # Level 3: discount-only fallback
    discount_df = bucket_table["discount_only"].reset_index()
    discount_df.columns = ["discount_bucket", "y_mean_discount"]
    temp = temp.merge(discount_df, on="discount_bucket", how="left")

    # Apply fallback hierarchy: full -> period -> discount -> global
    y_mean = temp["y_mean_full"].fillna(temp["y_mean_period"])
    y_mean = y_mean.fillna(temp["y_mean_discount"])
    y_mean = y_mean.fillna(bucket_table["global_mean"])

    return y_mean.values.astype(np.float32)


def apply_offline_calibration(y, y_mean, eta=0.6):
    """
    Offline calibration blending (Eq. 17 equivalent):
      y_calibrated = y * eta + y_mean * (1 - eta)

    Args:
        y:      actual sales values (tensor or array)
        y_mean: bucket mean values (tensor or array, same shape as y)
        eta:    blending weight (default 0.6, higher = more weight on actual)

    Returns:
        calibrated target (same type and shape as y)
    """
    return y * eta + y_mean * (1 - eta)

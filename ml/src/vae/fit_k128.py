"""
fit_k128.py -- Fit KMeans with K=128 on the full train split and save to ml/models/vae/kmeans_k128.pkl.
"""

import os
import sys
import joblib
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

from columns import FEATURE_COLS
from clustering import fit_kmeans


def main():
    processed_dir = os.path.join("ml", "data", "processed")
    model_dir = os.path.join("ml", "models", "vae")
    os.makedirs(model_dir, exist_ok=True)

    print("=" * 65)
    print("STEP 1: Fitting KMeans (K=128) on full train split")
    print("=" * 65)
    train_df = pd.read_parquet(os.path.join(processed_dir, "rossmann_train.parquet"))
    print(f"  Train rows: {len(train_df):,}")

    km128 = fit_kmeans(train_df, n_clusters=128)

    save_path = os.path.join(model_dir, "kmeans_k128.pkl")
    joblib.dump(km128, save_path, compress=3)
    size_mb = os.path.getsize(save_path) / (1024 * 1024)
    print(f"  Saved K=128 KMeans model to: {save_path} ({size_mb:.2f} MB)")
    print("=" * 65)


if __name__ == "__main__":
    main()

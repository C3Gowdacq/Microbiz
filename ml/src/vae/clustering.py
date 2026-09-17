"""
clustering.py -- K-Means clustering module for the Reconstructed VAE.

Fits KMeans on the TRAIN split only, assigns cluster labels to any split,
and saves the fitted model for reuse in the VAE dataset pipeline.

References:
  - Paper Section 5.2 / Eq. 5: cluster label L_n -> embedding c_n
"""

import os
import sys
import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans

# Add parent dir so we can import columns.py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from columns import X_COLS, A_COLS, B_COLS, FEATURE_COLS


def run_inertia_sweep(X_sample, k_values, random_state=42, n_init=10):
    """
    Fit KMeans for each K on a subsample and return {K: inertia}.
    Used to pick K with evidence rather than guessing.
    """
    results = {}
    for k in k_values:
        km = KMeans(n_clusters=k, random_state=random_state, n_init=n_init)
        km.fit(X_sample)
        results[k] = km.inertia_
        print(f"  K={k:<5d}  Inertia={km.inertia_:>18,.2f}")
    return results


def pick_best_k(inertia_dict):
    """
    Simple elbow heuristic: pick the K with the largest relative drop in inertia.
    Returns the recommended K.
    """
    ks = sorted(inertia_dict.keys())
    if len(ks) <= 1:
        return ks[0]

    # Compute relative drops: (inertia[k-1] - inertia[k]) / inertia[k-1]
    drops = {}
    for i in range(1, len(ks)):
        prev_k, curr_k = ks[i - 1], ks[i]
        drop = (inertia_dict[prev_k] - inertia_dict[curr_k]) / inertia_dict[prev_k]
        drops[curr_k] = drop

    # Find the K where the *marginal* improvement starts flattening
    # i.e. the K after the biggest relative drop
    best_k = max(drops, key=drops.get)
    return best_k


def fit_kmeans(train_df, n_clusters, random_state=42, n_init=10):
    """
    Fit KMeans on the full TRAIN split feature matrix (X + A + B).
    Returns the fitted KMeans model.
    """
    X = train_df[FEATURE_COLS].values.astype(np.float32)
    print(f"  Fitting KMeans(K={n_clusters}) on {X.shape[0]:,} rows x {X.shape[1]} features...")
    km = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=n_init)
    km.fit(X)
    print(f"  Final inertia: {km.inertia_:,.2f}")
    return km


def assign_clusters(df, kmeans_model):
    """
    Assign cluster labels to any split using the already-fitted KMeans model.
    Never refits -- only calls predict().

    Args:
        df: DataFrame with FEATURE_COLS present
        kmeans_model: fitted KMeans instance

    Returns:
        np.ndarray of int cluster labels, shape (len(df),)
    """
    X = df[FEATURE_COLS].values.astype(np.float32)
    return kmeans_model.predict(X)


def main():
    processed_dir = os.path.join("ml", "data", "processed")
    model_dir = os.path.join("ml", "models", "vae")
    os.makedirs(model_dir, exist_ok=True)

    # Load train split
    print("=" * 60)
    print("STEP 1: Loading train split for clustering")
    print("=" * 60)
    train_df = pd.read_parquet(os.path.join(processed_dir, "rossmann_train.parquet"))
    print(f"  Train rows: {len(train_df):,}")

    # Inertia sweep on a 100k subsample for speed
    print("\n" + "=" * 60)
    print("STEP 2: Inertia sweep (100k sample) for K selection")
    print("=" * 60)

    sample_size = min(100_000, len(train_df))
    sample_df = train_df.sample(n=sample_size, random_state=42)
    X_sample = sample_df[FEATURE_COLS].values.astype(np.float32)

    k_values = [8, 32, 128, 512]
    print(f"  Sweeping K in {k_values} on {sample_size:,} rows...")
    inertia_results = run_inertia_sweep(X_sample, k_values)

    recommended_k = pick_best_k(inertia_results)
    print(f"\n  Recommended K (largest relative inertia drop): {recommended_k}")

    # Fit final KMeans on full train with recommended K
    print("\n" + "=" * 60)
    print(f"STEP 3: Fitting final KMeans (K={recommended_k}) on FULL train set")
    print("=" * 60)
    kmeans_model = fit_kmeans(train_df, n_clusters=recommended_k)

    # Save model
    save_path = os.path.join(model_dir, "kmeans.pkl")
    joblib.dump(kmeans_model, save_path, compress=3)
    file_size_mb = os.path.getsize(save_path) / (1024 * 1024)
    print(f"  Saved KMeans model to: {save_path} ({file_size_mb:.1f} MB)")

    # Assign clusters to all splits and show distribution
    print("\n" + "=" * 60)
    print("STEP 4: Assigning cluster labels to all splits")
    print("=" * 60)

    val_df = pd.read_parquet(os.path.join(processed_dir, "rossmann_val.parquet"))
    test_df = pd.read_parquet(os.path.join(processed_dir, "rossmann_test.parquet"))

    for name, df in [("Train", train_df), ("Val", val_df), ("Test", test_df)]:
        labels = assign_clusters(df, kmeans_model)
        unique_labels = np.unique(labels)
        print(f"\n  {name}: {len(df):,} rows -> {len(unique_labels)} unique clusters")
        print(f"    Label range: [{labels.min()}, {labels.max()}]")
        # Show top-5 cluster sizes
        label_counts = pd.Series(labels).value_counts().head(5)
        print(f"    Top-5 cluster sizes: {dict(label_counts)}")

    print("\n[DONE] KMeans clustering complete.")


if __name__ == "__main__":
    main()

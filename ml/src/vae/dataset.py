"""
dataset.py -- PyTorch Dataset, DataLoader factory, and ClusterEmbedding for the Reconstructed VAE.

Provides:
  - RossmannVAEDataset: returns (X, A, B, y_scaled, cluster_label, y_raw) tensors per sample
  - get_y_scaler(): fits/loads StandardScaler on TRAIN split 'Sales' column
  - get_dataloaders(): convenience function returning train/val/test DataLoaders
  - ClusterEmbedding: nn.Module wrapping nn.Embedding(K, embedding_dim) for c_n

References:
  - Paper Section 5.2 / Eq. 5: cluster label L_n -> embedding c_n
"""

import os
import sys
import joblib
import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader
import torch.nn as nn
from sklearn.preprocessing import StandardScaler

# Add parent dir so we can import columns.py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from columns import X_COLS, A_COLS, B_COLS, Y_COL, FEATURE_COLS

# Add vae dir for clustering import
sys.path.insert(0, os.path.dirname(__file__))
from clustering import assign_clusters


def get_y_scaler(y_scaler_path=None, force_refit=False):
    """
    Fit or load StandardScaler on TRAIN split's Sales column.
    Saves to ml/models/vae/y_scaler.pkl.
    """
    if y_scaler_path is None:
        model_dir = os.path.join("ml", "models", "vae")
        y_scaler_path = os.path.join(model_dir, "y_scaler.pkl")

    if os.path.exists(y_scaler_path) and not force_refit:
        return joblib.load(y_scaler_path)

    processed_dir = os.path.join("ml", "data", "processed")
    train_path = os.path.join(processed_dir, "rossmann_train.parquet")
    train_df = pd.read_parquet(train_path)

    y_scaler = StandardScaler()
    y_scaler.fit(train_df[[Y_COL]])

    os.makedirs(os.path.dirname(y_scaler_path), exist_ok=True)
    joblib.dump(y_scaler, y_scaler_path)
    print(f"  Fitted and saved y_scaler to {y_scaler_path} (mean={y_scaler.mean_[0]:.2f}, scale={y_scaler.scale_[0]:.2f})", flush=True)
    return y_scaler


class RossmannVAEDataset(Dataset):
    """
    PyTorch Dataset for the Reconstructed VAE on Rossmann data.

    Each sample returns:
        X:             float32 tensor, shape (len(X_COLS),)
        A:             float32 tensor, shape (len(A_COLS),)
        B:             float32 tensor, shape (len(B_COLS),)
        y:             float32 tensor, shape (1,) — SCALED Sales target
        cluster_label: int64 tensor, shape () — KMeans cluster ID for embedding lookup
        y_raw:         float32 tensor, shape (1,) — RAW Sales target (for metrics)
    """

    def __init__(self, parquet_path, kmeans_model, y_scaler=None, scale_y=True):
        """
        Args:
            parquet_path: path to a processed parquet file (train/val/test)
            kmeans_model: fitted KMeans model (only calls predict, never refit)
            y_scaler: fitted StandardScaler for Sales (if None and scale_y=True, loads/fits automatically)
            scale_y: bool, whether to scale y using y_scaler (default True)
        """
        df = pd.read_parquet(parquet_path)

        # Extract column groups as float32 numpy arrays
        self.X = df[X_COLS].values.astype(np.float32)
        self.A = df[A_COLS].values.astype(np.float32)
        self.B = df[B_COLS].values.astype(np.float32)
        self.y_raw = df[[Y_COL]].values.astype(np.float32)

        if scale_y:
            if y_scaler is None:
                y_scaler = get_y_scaler()
            self.y_scaler = y_scaler
            self.y = y_scaler.transform(pd.DataFrame(self.y_raw, columns=[Y_COL])).astype(np.float32)
        else:
            self.y_scaler = None
            self.y = self.y_raw.copy()

        # Assign cluster labels using the fitted KMeans (predict only, no refit)
        self.cluster_labels = assign_clusters(df, kmeans_model).astype(np.int64)

        self.n_samples = len(df)

    def __len__(self):
        return self.n_samples

    def __getitem__(self, idx):
        return (
            torch.from_numpy(self.X[idx]),
            torch.from_numpy(self.A[idx]),
            torch.from_numpy(self.B[idx]),
            torch.from_numpy(self.y[idx]),
            torch.tensor(self.cluster_labels[idx], dtype=torch.long),
            torch.from_numpy(self.y_raw[idx]),
        )


class ClusterEmbedding(nn.Module):
    """
    Cluster label embedding: L_n -> c_n (Section 5.2 / Eq. 5).

    Maps integer cluster labels to dense embedding vectors that get
    concatenated with other inputs to the VAE encoder/decoder.

    Args:
        num_clusters (int): K, the number of KMeans clusters
        embedding_dim (int): dimensionality of c_n (default 10)
    """

    def __init__(self, num_clusters, embedding_dim=10):
        super().__init__()
        self.embedding = nn.Embedding(
            num_embeddings=num_clusters,
            embedding_dim=embedding_dim,
        )

    def forward(self, cluster_labels):
        """
        Args:
            cluster_labels: LongTensor of shape (batch_size,)

        Returns:
            c_n: float tensor of shape (batch_size, embedding_dim)
        """
        return self.embedding(cluster_labels)


def get_dataloaders(batch_size=2048, num_workers=2, kmeans_model=None, y_scaler=None, scale_y=True):
    """
    Build train/val/test DataLoaders for the Rossmann VAE pipeline.

    Args:
        batch_size: batch size for all loaders (default 2048)
        num_workers: DataLoader workers (default 2 for CPU parallelism)
        kmeans_model: fitted KMeans model. If None, loads from ml/models/vae/kmeans.pkl
        y_scaler: fitted StandardScaler for Sales. If None and scale_y=True, loads/fits automatically
        scale_y: whether to return scaled y in dataloaders

    Returns:
        dict with keys 'train', 'val', 'test' -> DataLoader instances
    """
    processed_dir = os.path.join("ml", "data", "processed")
    model_dir = os.path.join("ml", "models", "vae")

    if kmeans_model is None:
        kmeans_path = os.path.join(model_dir, "kmeans.pkl")
        if not os.path.exists(kmeans_path):
            raise FileNotFoundError(
                f"KMeans model not found at {kmeans_path}. "
                "Run clustering.py first to fit and save the KMeans model."
            )
        kmeans_model = joblib.load(kmeans_path)

    if scale_y and y_scaler is None:
        y_scaler = get_y_scaler()

    splits = {
        "train": os.path.join(processed_dir, "rossmann_train.parquet"),
        "val": os.path.join(processed_dir, "rossmann_val.parquet"),
        "test": os.path.join(processed_dir, "rossmann_test.parquet"),
    }

    use_persistent = num_workers > 0

    loaders = {}
    for name, path in splits.items():
        dataset = RossmannVAEDataset(path, kmeans_model, y_scaler=y_scaler, scale_y=scale_y)
        loaders[name] = DataLoader(
            dataset,
            batch_size=batch_size,
            shuffle=(name == "train"),  # Only shuffle training data
            num_workers=num_workers,
            pin_memory=False,  # CPU-only, no benefit from pin_memory
            drop_last=False,
            persistent_workers=use_persistent,
        )
        print(f"  {name:>5s} DataLoader: {len(dataset):,} samples, "
              f"{len(loaders[name]):,} batches (batch_size={batch_size})",
              flush=True)

    return loaders

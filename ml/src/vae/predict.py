"""
predict.py -- Inference module for the Reconstructed VAE.

Loads vae_checkpoint.pt, kmeans.pkl, scaler.pkl, and y_scaler.pkl,
and exposes predict(X, A, B, cluster_label) which returns predicted sales
already inverse-transformed to raw Sales scale.

References:
  - Base paper Section 5.4
  - MicroBizAI_Architecture.md Section 5.7
"""

import os
import sys
import joblib
import numpy as np
import torch

# Add parent dirs for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

from columns import X_COLS, A_COLS, B_COLS
from model import ReconstructedVAE


class VAEInferencePipeline:
    """
    Inference wrapper loading all saved assets and providing clean prediction API.
    """

    def __init__(self, checkpoint_path=None, device=None):
        model_dir = os.path.join("ml", "models", "vae")
        if checkpoint_path is None:
            checkpoint_path = os.path.join(model_dir, "vae_checkpoint.pt")

        if not os.path.exists(checkpoint_path):
            raise FileNotFoundError(f"Checkpoint not found at {checkpoint_path}")

        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

        # Load checkpoint
        ckpt = torch.load(checkpoint_path, map_location=self.device)
        hp = ckpt["hyperparameters"]

        # Load saved scalers and models
        kmeans_path = ckpt.get("kmeans_path", os.path.join(model_dir, "kmeans.pkl"))
        y_scaler_path = ckpt.get("y_scaler_path", os.path.join(model_dir, "y_scaler.pkl"))
        scaler_path = ckpt.get("scaler_path", os.path.join("ml", "data", "processed", "scaler.pkl"))

        self.kmeans_model = joblib.load(kmeans_path)
        self.y_scaler = joblib.load(y_scaler_path)
        self.feature_scaler = joblib.load(scaler_path)

        # Instantiate model architecture
        self.model = ReconstructedVAE(
            x_dim=len(X_COLS),
            a_dim=len(A_COLS),
            b_dim=len(B_COLS),
            num_clusters=hp["K"],
            cluster_emb_dim=hp["cluster_emb_dim"],
            latent_dim=hp["latent_dim"],
            prior_encoder_dim=hp["prior_encoder_dim"],
            prior_hidden_dim=hp["prior_hidden_dim"],
            post_encoder_dim=hp["post_encoder_dim"],
            decoder_hidden_dim=hp["decoder_hidden_dim"],
            regressor_hidden_dim=hp["regressor_hidden_dim"],
            dropout_p=hp["dropout_p"],
        ).to(self.device)

        self.model.load_state_dict(ckpt["model_state_dict"])
        self.model.eval()

    @torch.no_grad()
    def predict(self, X, A, B, cluster_label):
        """
        Run inference on input tensors and return predictions in raw Sales units.

        Args:
            X:             Tensor or ndarray of shape (N, len(X_COLS))
            A:             Tensor or ndarray of shape (N, len(A_COLS))
            B:             Tensor or ndarray of shape (N, len(B_COLS))
            cluster_label: Tensor or ndarray of shape (N,) with cluster IDs

        Returns:
            y_pred_raw: np.ndarray of shape (N, 1) in raw Sales units (e.g. 5000.0)
        """
        if not isinstance(X, torch.Tensor):
            X = torch.tensor(X, dtype=torch.float32)
        if not isinstance(A, torch.Tensor):
            A = torch.tensor(A, dtype=torch.float32)
        if not isinstance(B, torch.Tensor):
            B = torch.tensor(B, dtype=torch.float32)
        if not isinstance(cluster_label, torch.Tensor):
            cluster_label = torch.tensor(cluster_label, dtype=torch.long)

        X = X.to(self.device)
        A = A.to(self.device)
        B = B.to(self.device)
        cluster_label = cluster_label.to(self.device)

        y_hat_scaled = self.model.predict(X, A, B, cluster_label).cpu().numpy()
        y_hat_raw = self.y_scaler.inverse_transform(y_hat_scaled)

        return y_hat_raw


# Global singleton instance for simple module-level predict() call
_pipeline = None


def predict(X, A, B, cluster_label, checkpoint_path=None):
    """
    Exposes predict(X, A, B, cluster_label) function returning predictions
    inverse-transformed to raw Sales scale.

    Args:
        X, A, B, cluster_label: input data (Tensors or ndarrays)

    Returns:
        np.ndarray of shape (N, 1) in raw Sales units
    """
    global _pipeline
    if _pipeline is None or checkpoint_path is not None:
        _pipeline = VAEInferencePipeline(checkpoint_path=checkpoint_path)
    return _pipeline.predict(X, A, B, cluster_label)

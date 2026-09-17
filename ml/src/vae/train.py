"""
train.py -- Full training loop for the Reconstructed VAE with target scaling.

Implements Algorithm 1 from the paper / Section 5.6 of MicroBizAI_Architecture.md:
  - Target scaling: StandardScaler on Sales (y) so regression loss is on unit-variance scale
  - Adam optimizer with L2 regularization (weight_decay)
  - Offline calibration of training targets via bucket means (in scaled space)
  - Per-epoch logging of loss components (recon, reg, KL) + val MAE/RMSE in RAW Sales units
  - Early stopping on val MAE in RAW Sales units with patience
  - Best checkpoint saving

References:
  - Base paper Algorithm 1, Eq. 15-16
  - MicroBizAI_Architecture.md Section 5.6
"""

import os
import sys
import time
import math
import joblib
import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader

# Set PyTorch thread count to physical cores for optimal CPU throughput
NUM_THREADS = min(os.cpu_count() or 4, 10)  # cap at 10 to avoid diminishing returns
torch.set_num_threads(NUM_THREADS)

# Add parent dirs for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

from columns import X_COLS, A_COLS, B_COLS, Y_COL, FEATURE_COLS
from clustering import assign_clusters
from dataset import ClusterEmbedding, RossmannVAEDataset, get_y_scaler
from model import ReconstructedVAE
from loss import vae_loss
from calibration import compute_bucket_means, compute_y_mean_array, apply_offline_calibration


P = lambda *args, **kw: print(*args, **kw, flush=True)  # flush=True helper


# ── Training Dataset with calibration targets & target scaling ────────────────

class CalibratedVAEDataset(Dataset):
    """
    Extended VAE Dataset that returns scaled y, scaled y_mean, and raw y.
    Used for training only; val/test use the standard RossmannVAEDataset.
    """

    def __init__(self, parquet_path, kmeans_model, y_mean_raw_array, y_scaler):
        df = pd.read_parquet(parquet_path)
        self.X = df[X_COLS].values.astype(np.float32)
        self.A = df[A_COLS].values.astype(np.float32)
        self.B = df[B_COLS].values.astype(np.float32)

        self.y_raw = df[[Y_COL]].values.astype(np.float32)
        self.y = y_scaler.transform(pd.DataFrame(self.y_raw, columns=[Y_COL])).astype(np.float32)

        # Scale y_mean array to scaled target space
        y_mean_2d = y_mean_raw_array.reshape(-1, 1).astype(np.float32)
        self.y_mean = y_scaler.transform(pd.DataFrame(y_mean_2d, columns=[Y_COL])).astype(np.float32)

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
            torch.from_numpy(self.y_mean[idx]),
            torch.from_numpy(self.y_raw[idx]),
        )


# ── Training loop ────────────────────────────────────────────────────────────

def train_vae(
    max_epochs=50,
    batch_size=2048,
    lr=1e-3,
    weight_decay=1e-5,
    tau=0.01,
    eta=0.6,
    patience=15,
    latent_dim=64,
    prior_encoder_dim=64,
    prior_hidden_dim=256,
    post_encoder_dim=128,
    decoder_hidden_dim=128,
    regressor_hidden_dim=128,
    cluster_emb_dim=10,
    dropout_p=0.1,
    num_workers=2,
    checkpoint_filename="vae_checkpoint.pt",
    kmeans_filename="kmeans.pkl",
):
    """Full training pipeline for the Reconstructed VAE with target scaling."""

    processed_dir = os.path.join("ml", "data", "processed")
    model_dir = os.path.join("ml", "models", "vae")
    os.makedirs(model_dir, exist_ok=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    P(f"Device: {device}")
    P(f"PyTorch threads: {torch.get_num_threads()}")

    # ── 1. Load KMeans model and y_scaler ──────────────────────────────
    P("\n" + "=" * 70)
    P("STEP 1: Loading KMeans model and y_scaler")
    P("=" * 70)
    kmeans_model = joblib.load(os.path.join(model_dir, kmeans_filename))
    K = kmeans_model.n_clusters
    P(f"  K={K} clusters (from {kmeans_filename})")

    y_scaler = get_y_scaler(force_refit=True)
    P(f"  y_scaler mean: {y_scaler.mean_[0]:.2f}, scale: {y_scaler.scale_[0]:.2f}")

    # ── 2. Compute calibration bucket means from training data ────────
    P("\n" + "=" * 70)
    P("STEP 2: Computing calibration bucket means")
    P("=" * 70)
    train_df = pd.read_parquet(os.path.join(processed_dir, "rossmann_train.parquet"))
    bucket_table = compute_bucket_means(train_df)
    y_mean_train_raw = compute_y_mean_array(train_df, bucket_table)
    P(f"  Bucket table: {len(bucket_table['full'])} (discount, period) buckets")
    P(f"  y_mean raw range: [{y_mean_train_raw.min():.1f}, {y_mean_train_raw.max():.1f}]")
    P(f"  Global mean sales: {bucket_table['global_mean']:.1f}")
    del train_df  # Free memory

    # ── 3. Build DataLoaders ──────────────────────────────────────────
    P("\n" + "=" * 70)
    P("STEP 3: Building DataLoaders")
    P("=" * 70)

    train_dataset = CalibratedVAEDataset(
        os.path.join(processed_dir, "rossmann_train.parquet"),
        kmeans_model, y_mean_train_raw, y_scaler,
    )
    train_loader = DataLoader(
        train_dataset, batch_size=batch_size, shuffle=True,
        num_workers=num_workers, pin_memory=False, drop_last=False,
        persistent_workers=(num_workers > 0),
    )
    P(f"  Train: {len(train_dataset):,} samples, {len(train_loader):,} batches (bs={batch_size})")

    val_dataset = RossmannVAEDataset(
        os.path.join(processed_dir, "rossmann_val.parquet"), kmeans_model,
        y_scaler=y_scaler, scale_y=True,
    )
    val_loader = DataLoader(
        val_dataset, batch_size=batch_size, shuffle=False,
        num_workers=0, pin_memory=False, drop_last=False,
    )
    P(f"  Val:   {len(val_dataset):,} samples, {len(val_loader):,} batches (bs={batch_size})")

    total_train_batches = len(train_loader)

    # ── 4. Instantiate model ──────────────────────────────────────────
    P("\n" + "=" * 70)
    P("STEP 4: Instantiating ReconstructedVAE")
    P("=" * 70)

    model = ReconstructedVAE(
        x_dim=len(X_COLS),
        a_dim=len(A_COLS),
        b_dim=len(B_COLS),
        num_clusters=K,
        cluster_emb_dim=cluster_emb_dim,
        latent_dim=latent_dim,
        prior_encoder_dim=prior_encoder_dim,
        prior_hidden_dim=prior_hidden_dim,
        post_encoder_dim=post_encoder_dim,
        decoder_hidden_dim=decoder_hidden_dim,
        regressor_hidden_dim=regressor_hidden_dim,
        dropout_p=dropout_p,
    ).to(device)

    total_params = sum(p.numel() for p in model.parameters())
    P(f"  Total trainable parameters: {total_params:,}")

    # ── 5. Optimizer ──────────────────────────────────────────────────
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=weight_decay)

    # ── 6. Training loop ──────────────────────────────────────────────
    P("\n" + "=" * 70)
    P("STEP 5: Training (with Target Scaling)")
    P("=" * 70)
    P(f"  max_epochs={max_epochs}, lr={lr}, weight_decay={weight_decay}")
    P(f"  tau={tau}, eta={eta}, patience={patience}, batch_size={batch_size}")
    P(f"  num_workers={num_workers}, torch_threads={torch.get_num_threads()}")

    best_val_mae = float("inf")
    best_epoch = -1
    patience_counter = 0
    best_state_dict = None
    history = []
    training_start = time.time()

    # Header for epoch logging
    P(f"\n  {'Ep':<5} {'Loss':<11} {'Recon':<9} {'Reg':<11} {'KL':<9} "
      f"{'ValMAE':<11} {'ValRMSE':<11} {'Time(s)':<8} {'Note'}")
    P(f"  {'-'*85}")

    for epoch in range(1, max_epochs + 1):
        epoch_start = time.time()

        # ── Train phase ───────────────────────────────────────────
        model.train()
        epoch_loss = 0.0
        epoch_recon = 0.0
        epoch_reg = 0.0
        epoch_kl = 0.0
        n_batches = 0
        batch_times = []

        for batch_idx, batch in enumerate(train_loader, 1):
            batch_start = time.time()

            X, A, B, y_scaled, cluster_labels, y_mean_scaled, y_raw = batch
            X = X.to(device)
            A = A.to(device)
            B = B.to(device)
            y_scaled = y_scaled.to(device)
            cluster_labels = cluster_labels.to(device)
            y_mean_scaled = y_mean_scaled.to(device)

            # Forward pass
            outputs = model(X, A, B, cluster_labels)

            # Calibrated training target in SCALED space (Eq. 17)
            calibrated_y_scaled = apply_offline_calibration(y_scaled, y_mean_scaled, eta=eta)

            # Compute loss using calibrated SCALED target for regression
            loss_dict = vae_loss(outputs, X, A, B, calibrated_y_scaled, tau=tau)
            loss = loss_dict["total"]

            # NaN detection: stop immediately and report which component failed
            if torch.isnan(loss):
                P(f"\n  [FATAL] NaN loss detected at epoch {epoch}, batch {batch_idx}!")
                P(f"    recon_loss: {loss_dict['recon_loss'].item()}")
                P(f"    reg_loss:   {loss_dict['reg_loss'].item()}")
                P(f"    kl_loss:    {loss_dict['kl_loss'].item()}")
                nan_component = "unknown"
                if torch.isnan(loss_dict["recon_loss"]):
                    nan_component = "recon_loss"
                elif torch.isnan(loss_dict["reg_loss"]):
                    nan_component = "reg_loss"
                elif torch.isnan(loss_dict["kl_loss"]):
                    nan_component = "kl_loss"
                P(f"    First NaN component: {nan_component}")
                P("  Training ABORTED.")
                return

            # Backprop
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            batch_time = time.time() - batch_start
            batch_times.append(batch_time)

            epoch_loss += loss.item()
            epoch_recon += loss_dict["recon_loss"].item()
            epoch_reg += loss_dict["reg_loss"].item()
            epoch_kl += loss_dict["kl_loss"].item()
            n_batches += 1

            # Intra-epoch progress logging (first epoch only, every 10 batches)
            if epoch == 1 and batch_idx % 10 == 0:
                avg_bt = sum(batch_times) / len(batch_times) * 1000
                eta_epoch = avg_bt * (total_train_batches - batch_idx) / 1000
                P(f"    [Epoch 1] batch {batch_idx}/{total_train_batches}, "
                  f"avg {avg_bt:.0f}ms/batch, "
                  f"loss={loss.item():.4f}, "
                  f"ETA this epoch: {eta_epoch:.0f}s")

        avg_loss = epoch_loss / n_batches
        avg_recon = epoch_recon / n_batches
        avg_reg = epoch_reg / n_batches
        avg_kl = epoch_kl / n_batches

        # ── Validation phase (no calibration, raw predicted vs actual) ─
        model.eval()
        val_abs_errors = []
        val_sq_errors = []

        with torch.no_grad():
            for batch in val_loader:
                X_v, A_v, B_v, y_v_scaled, cl_v, y_v_raw = batch
                X_v = X_v.to(device)
                A_v = A_v.to(device)
                B_v = B_v.to(device)
                cl_v = cl_v.to(device)

                # Predict scaled y_hat
                y_hat_scaled = model.predict(X_v, A_v, B_v, cl_v).cpu().numpy()

                # Inverse transform back to RAW sales scale
                y_hat_raw = y_scaler.inverse_transform(y_hat_scaled)
                y_v_raw_np = y_v_raw.numpy()

                abs_err = np.abs(y_hat_raw - y_v_raw_np)
                sq_err = (y_hat_raw - y_v_raw_np) ** 2

                val_abs_errors.append(abs_err)
                val_sq_errors.append(sq_err)

        val_abs_all = np.vstack(val_abs_errors)
        val_sq_all = np.vstack(val_sq_errors)
        val_mae = float(np.mean(val_abs_all))
        val_rmse = float(np.sqrt(np.mean(val_sq_all)))

        epoch_time = time.time() - epoch_start

        # Early stopping check (based on raw Sales units MAE)
        note = ""
        if val_mae < best_val_mae:
            best_val_mae = val_mae
            best_epoch = epoch
            best_state_dict = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            patience_counter = 0
            note = "*best*"
        else:
            patience_counter += 1
            if patience_counter >= patience:
                note = "STOP"

        # Log this epoch (flush=True via P())
        P(f"  {epoch:<5d} {avg_loss:<11.4f} {avg_recon:<9.4f} {avg_reg:<11.4f} "
          f"{avg_kl:<9.4f} {val_mae:<11.2f} {val_rmse:<11.2f} {epoch_time:<8.1f} {note}")

        # Benchmark print after epoch 1
        if epoch == 1:
            avg_batch_ms = sum(batch_times) / len(batch_times) * 1000
            P(f"\n  >>> EPOCH 1 BENCHMARK: {epoch_time:.1f}s total, "
              f"{avg_batch_ms:.0f}ms/batch, {n_batches} batches")
            P(f"  >>> Projected: {max_epochs} epochs = {epoch_time * max_epochs / 60:.1f} min")
            P(f"  >>> With early stopping (patience={patience}): "
              f"likely {epoch_time * min(max_epochs, 30) / 60:.1f} min\n")

        # Record history
        history.append({
            "epoch": epoch,
            "loss": avg_loss,
            "recon": avg_recon,
            "reg": avg_reg,
            "kl": avg_kl,
            "val_mae": val_mae,
            "val_rmse": val_rmse,
            "epoch_time": epoch_time,
            "is_best": (note == "*best*"),
        })

        if patience_counter >= patience:
            P(f"\n  Early stopping at epoch {epoch} (no improvement for {patience} epochs)")
            break

    # ── 7. Restore best weights and save checkpoint ───────────────────
    total_time = time.time() - training_start

    P("\n" + "=" * 70)
    P("STEP 6: Saving best checkpoint")
    P("=" * 70)

    if best_state_dict is not None:
        model.load_state_dict(best_state_dict)
        model = model.to(device)

    checkpoint = {
        "model_state_dict": model.state_dict(),
        "hyperparameters": {
            "K": K,
            "latent_dim": latent_dim,
            "cluster_emb_dim": cluster_emb_dim,
            "prior_encoder_dim": prior_encoder_dim,
            "prior_hidden_dim": prior_hidden_dim,
            "post_encoder_dim": post_encoder_dim,
            "decoder_hidden_dim": decoder_hidden_dim,
            "regressor_hidden_dim": regressor_hidden_dim,
            "dropout_p": dropout_p,
            "tau": tau,
            "eta": eta,
            "lr": lr,
            "weight_decay": weight_decay,
            "batch_size": batch_size,
        },
        "best_epoch": best_epoch,
        "best_val_mae": best_val_mae,
        "kmeans_path": os.path.join(model_dir, kmeans_filename),
        "scaler_path": os.path.join(processed_dir, "scaler.pkl"),
        "y_scaler_path": os.path.join(model_dir, "y_scaler.pkl"),
    }

    ckpt_path = os.path.join(model_dir, checkpoint_filename)
    torch.save(checkpoint, ckpt_path)
    ckpt_size_mb = os.path.getsize(ckpt_path) / (1024 * 1024)
    P(f"  Saved checkpoint to: {ckpt_path} ({ckpt_size_mb:.1f} MB)")

    # ── 8. Final summary ─────────────────────────────────────────────
    P("\n" + "=" * 70)
    P("TRAINING SUMMARY")
    P("=" * 70)
    P(f"  Best epoch:        {best_epoch}")
    P(f"  Best val MAE:      {best_val_mae:.2f} (in raw Sales units)")
    P(f"  Total train time:  {total_time / 60:.1f} minutes ({total_time:.0f}s)")
    P(f"  Total parameters:  {total_params:,}")
    P(f"  Device:            {device}")
    P("=" * 70)

    return best_val_mae, history


if __name__ == "__main__":
    train_vae()

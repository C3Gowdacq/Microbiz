"""
test_model.py -- End-to-end test for the full ReconstructedVAE model.

Verifies:
  1. Model instantiation with real dimensions from Parts 4a/4b
  2. Forward pass on a real data batch
  3. Output shapes for x_hat, a_hat, b_hat, y_hat match originals
  4. y_hat sanity check (no NaNs, min/max/mean)
  5. Total trainable parameter count
"""

import os
import sys
import joblib
import torch

# Add parent dirs for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

from columns import X_COLS, A_COLS, B_COLS
from dataset import get_dataloaders
from model import ReconstructedVAE


def main():
    model_dir = os.path.join("ml", "models", "vae")

    # 1. Load KMeans to get K and build DataLoaders
    print("=" * 65)
    print("SETUP: Loading KMeans and building DataLoaders")
    print("=" * 65)
    kmeans_model = joblib.load(os.path.join(model_dir, "kmeans.pkl"))
    K = kmeans_model.n_clusters
    print(f"  KMeans K={K}")

    loaders = get_dataloaders(batch_size=512, kmeans_model=kmeans_model)

    # 2. Instantiate the full model
    print("\n" + "=" * 65)
    print("TEST 1: Model instantiation")
    print("=" * 65)

    model = ReconstructedVAE(
        x_dim=len(X_COLS),      # 14
        a_dim=len(A_COLS),      # 7
        b_dim=len(B_COLS),      # 4
        num_clusters=K,          # 32
        cluster_emb_dim=10,
        latent_dim=64,
        prior_encoder_dim=64,
        prior_hidden_dim=256,
        post_encoder_dim=128,
        decoder_hidden_dim=128,
        regressor_hidden_dim=128,
        dropout_p=0.1,
    )

    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"  Total parameters:     {total_params:,}")
    print(f"  Trainable parameters: {trainable_params:,}")
    print(f"  Model components: {list(model._modules.keys())}")

    # 3. Fetch a real batch
    print("\n" + "=" * 65)
    print("TEST 2: Forward pass on real data batch")
    print("=" * 65)

    batch = next(iter(loaders["train"]))
    X, A, B, y, cluster_labels = batch
    print(f"  Input shapes: X={tuple(X.shape)}, A={tuple(A.shape)}, "
          f"B={tuple(B.shape)}, y={tuple(y.shape)}, labels={tuple(cluster_labels.shape)}")

    # Forward pass
    model.train()
    outputs = model(X, A, B, cluster_labels)

    print(f"  Output keys: {list(outputs.keys())}")

    # 4. Check output shapes
    print("\n" + "=" * 65)
    print("TEST 3: Output shape verification")
    print("=" * 65)

    expected_shapes = {
        "x_hat": (512, len(X_COLS)),   # (512, 14)
        "a_hat": (512, len(A_COLS)),   # (512, 7)
        "b_hat": (512, len(B_COLS)),   # (512, 4)
        "y_hat": (512, 1),
    }

    all_shapes_ok = True
    print(f"  {'Output':<12} {'Expected':<16} {'Actual':<16} {'Status'}")
    print(f"  {'-'*54}")

    for name, expected in expected_shapes.items():
        actual = tuple(outputs[name].shape)
        ok = expected == actual
        if not ok:
            all_shapes_ok = False
        print(f"  {name:<12} {str(expected):<16} {str(actual):<16} {'PASS' if ok else 'FAIL'}")

    # Check prior/posterior dict structure
    print(f"\n  Prior latent outputs:")
    for lname in ["z", "s", "v", "d"]:
        mu, sigma = outputs["prior"][lname]
        print(f"    {lname}: mu={tuple(mu.shape)}, sigma={tuple(sigma.shape)}")

    print(f"  Posterior latent outputs:")
    for lname in ["z", "s", "v", "d"]:
        mu, sigma = outputs["posterior"][lname]
        print(f"    {lname}: mu={tuple(mu.shape)}, sigma={tuple(sigma.shape)}")

    print(f"  Sampled latent shapes:")
    for lname in ["z", "s", "v", "d"]:
        print(f"    {lname}: {tuple(outputs['sampled'][lname].shape)}")

    # 5. y_hat sanity checks
    print("\n" + "=" * 65)
    print("TEST 4: y_hat sanity check")
    print("=" * 65)

    y_hat = outputs["y_hat"]
    has_nan = torch.isnan(y_hat).any().item()
    has_inf = torch.isinf(y_hat).any().item()
    y_min = y_hat.min().item()
    y_max = y_hat.max().item()
    y_mean = y_hat.mean().item()
    y_std = y_hat.std().item()

    print(f"  NaN check:  {'PASS (no NaNs)' if not has_nan else 'FAIL (NaNs found!)'}")
    print(f"  Inf check:  {'PASS (no Infs)' if not has_inf else 'FAIL (Infs found!)'}")
    print(f"  y_hat min:  {y_min:.4f}")
    print(f"  y_hat max:  {y_max:.4f}")
    print(f"  y_hat mean: {y_mean:.4f}")
    print(f"  y_hat std:  {y_std:.4f}")
    print(f"  (Untrained model -- values will be near-random, just checking no explosion/collapse)")

    y_hat_ok = not has_nan and not has_inf

    # 6. Test predict() convenience method
    print("\n" + "=" * 65)
    print("TEST 5: predict() convenience method")
    print("=" * 65)

    y_pred = model.predict(X, A, B, cluster_labels)
    pred_shape_ok = tuple(y_pred.shape) == (512, 1)
    pred_nan_free = not torch.isnan(y_pred).any().item()
    print(f"  Shape: {tuple(y_pred.shape)} -> {'PASS' if pred_shape_ok else 'FAIL'}")
    print(f"  NaN-free: {'PASS' if pred_nan_free else 'FAIL'}")

    # ── SUMMARY ───────────────────────────────────────────────────────
    print("\n" + "=" * 65)
    all_passed = all_shapes_ok and y_hat_ok and pred_shape_ok and pred_nan_free
    if all_passed:
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED -- check output above")
    print("=" * 65)
    print(f"\nTotal trainable parameters: {trainable_params:,}")


if __name__ == "__main__":
    main()

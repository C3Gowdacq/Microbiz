"""
test_encoder.py -- End-to-end test for PriorNetwork and PosteriorNetwork.

Loads a real batch from the VAE DataLoader, runs it through both networks,
and verifies shapes, positivity of sigma, and reparameterization output.
"""

import os
import sys
import joblib
import torch

# Add parent dirs for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

from columns import X_COLS, A_COLS, B_COLS
from dataset import get_dataloaders, ClusterEmbedding
from encoder import PriorNetwork, PosteriorNetwork, reparameterize


def main():
    model_dir = os.path.join("ml", "models", "vae")

    # 1. Load KMeans and build DataLoader
    print("=" * 65)
    print("SETUP: Loading KMeans model and building DataLoader")
    print("=" * 65)
    kmeans_model = joblib.load(os.path.join(model_dir, "kmeans.pkl"))
    K = kmeans_model.n_clusters
    print(f"  KMeans K={K}")

    loaders = get_dataloaders(batch_size=512, kmeans_model=kmeans_model)

    # 2. Fetch one batch
    batch = next(iter(loaders["train"]))
    X, A, B, y, cluster_labels = batch
    print(f"  Batch shapes: X={tuple(X.shape)}, A={tuple(A.shape)}, "
          f"B={tuple(B.shape)}, y={tuple(y.shape)}, labels={tuple(cluster_labels.shape)}")

    # 3. Build cluster embedding
    embedding_dim = 10
    cluster_embed = ClusterEmbedding(num_clusters=K, embedding_dim=embedding_dim)
    c_n = cluster_embed(cluster_labels)
    print(f"  c_n shape: {tuple(c_n.shape)}")

    # 4. Instantiate networks
    latent_dim = 64
    prior_net = PriorNetwork(
        a_dim=len(A_COLS), b_dim=len(B_COLS), c_dim=embedding_dim,
        encoder_dim=64, hidden_dim=256, latent_dim=latent_dim,
    )
    posterior_net = PosteriorNetwork(
        x_dim=len(X_COLS), a_dim=len(A_COLS), b_dim=len(B_COLS), c_dim=embedding_dim,
        encoder_dim=128, latent_dim=latent_dim, dropout_p=0.1,
    )

    # Count parameters
    prior_params = sum(p.numel() for p in prior_net.parameters())
    post_params = sum(p.numel() for p in posterior_net.parameters())
    print(f"\n  PriorNetwork params:     {prior_params:,}")
    print(f"  PosteriorNetwork params: {post_params:,}")

    # ── TEST: PriorNetwork ────────────────────────────────────────────
    print("\n" + "=" * 65)
    print("TEST 1: PriorNetwork forward pass")
    print("=" * 65)

    prior_out = prior_net(A, B, c_n)
    all_prior_ok = True

    print(f"  {'Latent':<8} {'mu shape':<20} {'sigma shape':<20} {'sigma>0?':<10} {'Status'}")
    print(f"  {'-'*68}")

    for name in ["z", "s", "v", "d"]:
        mu, sigma = prior_out[name]
        expected = (512, latent_dim)
        mu_ok = tuple(mu.shape) == expected
        sigma_ok = tuple(sigma.shape) == expected
        sigma_positive = (sigma > 0).all().item()
        status = "PASS" if (mu_ok and sigma_ok and sigma_positive) else "FAIL"
        if status == "FAIL":
            all_prior_ok = False
        print(f"  {name:<8} {str(tuple(mu.shape)):<20} {str(tuple(sigma.shape)):<20} "
              f"{'Yes' if sigma_positive else 'NO!':<10} {status}")

    # ── TEST: PosteriorNetwork ────────────────────────────────────────
    print("\n" + "=" * 65)
    print("TEST 2: PosteriorNetwork forward pass")
    print("=" * 65)

    posterior_net.eval()  # Set eval mode for BatchNorm/Dropout behavior
    with torch.no_grad():
        post_out = posterior_net(X, A, B, c_n)

    all_post_ok = True

    print(f"  {'Latent':<8} {'mu shape':<20} {'sigma shape':<20} {'sigma>0?':<10} "
          f"{'sigma_min':<12} {'Status'}")
    print(f"  {'-'*80}")

    for name in ["z", "s", "v", "d"]:
        mu, sigma = post_out[name]
        expected = (512, latent_dim)
        mu_ok = tuple(mu.shape) == expected
        sigma_ok = tuple(sigma.shape) == expected
        sigma_positive = (sigma > 0).all().item()
        sigma_min = sigma.min().item()
        status = "PASS" if (mu_ok and sigma_ok and sigma_positive) else "FAIL"
        if status == "FAIL":
            all_post_ok = False
        print(f"  {name:<8} {str(tuple(mu.shape)):<20} {str(tuple(sigma.shape)):<20} "
              f"{'Yes' if sigma_positive else 'NO!':<10} {sigma_min:<12.6f} {status}")

    # ── TEST: Reparameterization ──────────────────────────────────────
    print("\n" + "=" * 65)
    print("TEST 3: Reparameterization (sampling)")
    print("=" * 65)

    all_reparam_ok = True

    print(f"  {'Latent':<8} {'sample shape':<20} {'has NaN?':<12} {'Status'}")
    print(f"  {'-'*50}")

    for name in ["z", "s", "v", "d"]:
        mu, sigma = post_out[name]
        sample = reparameterize(mu, sigma)
        expected = (512, latent_dim)
        shape_ok = tuple(sample.shape) == expected
        has_nan = torch.isnan(sample).any().item()
        status = "PASS" if (shape_ok and not has_nan) else "FAIL"
        if status == "FAIL":
            all_reparam_ok = False
        print(f"  {name:<8} {str(tuple(sample.shape)):<20} "
              f"{'No' if not has_nan else 'YES!':<12} {status}")

    # ── TEST: Train mode sigma positivity ─────────────────────────────
    print("\n" + "=" * 65)
    print("TEST 4: PosteriorNetwork in TRAIN mode (Dropout active)")
    print("=" * 65)

    posterior_net.train()
    post_out_train = posterior_net(X, A, B, c_n)
    all_train_ok = True

    print(f"  {'Latent':<8} {'sigma>0?':<10} {'sigma_min':<14} {'sigma_max':<14} {'Status'}")
    print(f"  {'-'*56}")

    for name in ["z", "s", "v", "d"]:
        mu, sigma = post_out_train[name]
        sigma_positive = (sigma > 0).all().item()
        status = "PASS" if sigma_positive else "FAIL"
        if status == "FAIL":
            all_train_ok = False
        print(f"  {name:<8} {'Yes' if sigma_positive else 'NO!':<10} "
              f"{sigma.min().item():<14.6f} {sigma.max().item():<14.6f} {status}")

    # ── SUMMARY ───────────────────────────────────────────────────────
    print("\n" + "=" * 65)
    all_passed = all_prior_ok and all_post_ok and all_reparam_ok and all_train_ok
    if all_passed:
        print("ALL TESTS PASSED")
    else:
        parts = []
        if not all_prior_ok:
            parts.append("Prior")
        if not all_post_ok:
            parts.append("Posterior")
        if not all_reparam_ok:
            parts.append("Reparameterize")
        if not all_train_ok:
            parts.append("TrainMode")
        print(f"FAILED: {', '.join(parts)}")
    print("=" * 65)


if __name__ == "__main__":
    main()

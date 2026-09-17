"""
test_dataset.py -- End-to-end smoke test for KMeans clustering + VAE Dataset + ClusterEmbedding.

Verifies:
  1. KMeans model loads correctly
  2. DataLoader produces correct tensor shapes for X, A, B, y, cluster_label
  3. ClusterEmbedding produces c_n with expected shape
  4. No NaNs in any tensor
  5. All cluster labels are in range [0, K)
"""

import os
import sys
import joblib
import torch

# Add parent dirs for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

from columns import X_COLS, A_COLS, B_COLS
from dataset import RossmannVAEDataset, ClusterEmbedding, get_dataloaders


def main():
    model_dir = os.path.join("ml", "models", "vae")
    kmeans_path = os.path.join(model_dir, "kmeans.pkl")

    # 1. Load KMeans model
    print("=" * 60)
    print("TEST 1: Loading KMeans model")
    print("=" * 60)
    assert os.path.exists(kmeans_path), f"KMeans model not found at {kmeans_path}"
    kmeans_model = joblib.load(kmeans_path)
    K = kmeans_model.n_clusters
    print(f"  Loaded KMeans with K={K} clusters")
    print(f"  Cluster centers shape: {kmeans_model.cluster_centers_.shape}")

    # 2. Build DataLoaders
    print("\n" + "=" * 60)
    print("TEST 2: Building DataLoaders")
    print("=" * 60)
    loaders = get_dataloaders(batch_size=512, kmeans_model=kmeans_model)

    # 3. Fetch one batch from train loader
    print("\n" + "=" * 60)
    print("TEST 3: Fetching one batch and checking shapes")
    print("=" * 60)
    batch = next(iter(loaders["train"]))
    X, A, B, y, cluster_labels = batch

    expected_shapes = {
        "X": (512, len(X_COLS)),
        "A": (512, len(A_COLS)),
        "B": (512, len(B_COLS)),
        "y": (512, 1),
        "cluster_labels": (512,),
    }

    actual_shapes = {
        "X": tuple(X.shape),
        "A": tuple(A.shape),
        "B": tuple(B.shape),
        "y": tuple(y.shape),
        "cluster_labels": tuple(cluster_labels.shape),
    }

    print(f"  {'Tensor':<18} {'Expected Shape':<20} {'Actual Shape':<20} {'dtype':<15} {'Status'}")
    print(f"  {'-'*85}")

    all_shapes_ok = True
    for name in expected_shapes:
        expected = expected_shapes[name]
        actual = actual_shapes[name]
        tensor = {"X": X, "A": A, "B": B, "y": y, "cluster_labels": cluster_labels}[name]
        ok = expected == actual
        status = "PASS" if ok else "FAIL"
        if not ok:
            all_shapes_ok = False
        print(f"  {name:<18} {str(expected):<20} {str(actual):<20} {str(tensor.dtype):<15} {status}")

    # 4. NaN check
    print("\n" + "=" * 60)
    print("TEST 4: NaN check on all tensors")
    print("=" * 60)
    all_nan_free = True
    for name, tensor in [("X", X), ("A", A), ("B", B), ("y", y), ("cluster_labels", cluster_labels)]:
        has_nan = torch.isnan(tensor.float()).any().item()
        status = "PASS (no NaNs)" if not has_nan else "FAIL (NaNs found!)"
        if has_nan:
            all_nan_free = False
        print(f"  {name:<18} {status}")

    # 5. Cluster label range check
    print("\n" + "=" * 60)
    print("TEST 5: Cluster label range check")
    print("=" * 60)
    min_label = cluster_labels.min().item()
    max_label = cluster_labels.max().item()
    unique_in_batch = cluster_labels.unique().shape[0]
    in_range = (min_label >= 0) and (max_label < K)
    status = "PASS" if in_range else "FAIL"
    print(f"  K={K}, label range in batch: [{min_label}, {max_label}], unique: {unique_in_batch}  -> {status}")

    # 6. ClusterEmbedding test
    print("\n" + "=" * 60)
    print("TEST 6: ClusterEmbedding forward pass")
    print("=" * 60)
    embedding_dim = 10
    embed = ClusterEmbedding(num_clusters=K, embedding_dim=embedding_dim)
    c_n = embed(cluster_labels)

    expected_cn_shape = (512, embedding_dim)
    actual_cn_shape = tuple(c_n.shape)
    shape_ok = expected_cn_shape == actual_cn_shape
    nan_free = not torch.isnan(c_n).any().item()

    print(f"  ClusterEmbedding(K={K}, dim={embedding_dim})")
    print(f"  Input:  cluster_labels shape = {tuple(cluster_labels.shape)}")
    print(f"  Output: c_n shape = {actual_cn_shape} (expected {expected_cn_shape})  -> {'PASS' if shape_ok else 'FAIL'}")
    print(f"  c_n NaN check: {'PASS' if nan_free else 'FAIL'}")
    print(f"  c_n sample (first 3 rows, first 5 dims):")
    print(f"    {c_n[:3, :5].detach().numpy()}")

    # Summary
    print("\n" + "=" * 60)
    all_passed = all_shapes_ok and all_nan_free and in_range and shape_ok and nan_free
    if all_passed:
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED -- check output above")
    print("=" * 60)


if __name__ == "__main__":
    main()

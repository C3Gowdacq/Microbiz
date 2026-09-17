"""
sanity_check_y_scaler.py -- Verify y_scaler fitting and scaled y values before retraining.
"""

import os
import sys
import joblib
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

from dataset import get_y_scaler, get_dataloaders


def main():
    print("=" * 65)
    print("SANITY CHECK: Target (Sales) Scaling")
    print("=" * 65)

    # 1. Fit and load y_scaler
    y_scaler = get_y_scaler(force_refit=True)
    print(f"  y_scaler class:  {type(y_scaler).__name__}")
    print(f"  y_scaler.mean_:  {y_scaler.mean_[0]:.4f} (Expected mean sales ~6,900)")
    print(f"  y_scaler.scale_: {y_scaler.scale_[0]:.4f} (Expected sales std ~3,100)")

    # 2. Load one batch from DataLoader
    print("\nFetching one batch from train DataLoader...")
    loaders = get_dataloaders(batch_size=512, scale_y=True, y_scaler=y_scaler)
    batch = next(iter(loaders["train"]))
    X, A, B, y_scaled, cluster_labels, y_raw = batch

    # 3. Print 5 sample raw vs scaled values
    print("\nSample 5 values (Raw vs Scaled vs Inverse-Transformed):")
    print(f"  {'Sample':<8} {'Raw Sales':<15} {'Scaled y':<15} {'Inverse-Transformed':<20}")
    print("  " + "-" * 60)

    y_scaled_np = y_scaled[:5].numpy()
    y_raw_np = y_raw[:5].numpy()
    y_inv_np = y_scaler.inverse_transform(y_scaled_np)

    for i in range(5):
        raw_val = float(y_raw_np[i][0])
        scaled_val = float(y_scaled_np[i][0])
        inv_val = float(y_inv_np[i][0])
        print(f"  {i+1:<8} {raw_val:<15.2f} {scaled_val:<15.4f} {inv_val:<20.2f}")

    # 4. Check scaled y statistics across full batch
    batch_mean = float(y_scaled.mean())
    batch_std = float(y_scaled.std())
    print(f"\nFull batch (N=512) Scaled y Stats:")
    print(f"  Batch Mean: {batch_mean:.4f} (Expected ~0.0)")
    print(f"  Batch Std:  {batch_std:.4f} (Expected ~1.0)")

    is_scaled_ok = abs(batch_mean) < 0.5 and 0.5 < batch_std < 1.5
    status = "PASSED (Zero-mean / Unit-variance scaling verified!)" if is_scaled_ok else "FAILED"
    print(f"\nSanity Check Result: {status}")
    print("=" * 65)


if __name__ == "__main__":
    main()

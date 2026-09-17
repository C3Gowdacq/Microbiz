"""
run_k128_exp.py -- 20-epoch experiment with K=128 KMeans clustering.

Uses the Exp 2 winning config (lr=1e-3, tau=0.01, patience=15),
with kmeans_filename="kmeans_k128.pkl".
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

from train import train_vae


def main():
    print("=" * 80, flush=True)
    print("RUNNING K=128 CLUSTERING EXPERIMENT (20 EPOCHS)", flush=True)
    print("=" * 80, flush=True)

    kmeans_path = os.path.join("ml", "models", "vae", "kmeans_k128.pkl")
    if not os.path.exists(kmeans_path):
        raise FileNotFoundError(f"K128 model not found at {kmeans_path}. Run fit_k128.py first.")

    best_mae, history = train_vae(
        max_epochs=20,
        patience=15,
        lr=1e-3,
        tau=0.01,
        checkpoint_filename="exp_k128.pt",
        kmeans_filename="kmeans_k128.pkl",
    )

    hist_by_epoch = {h["epoch"]: h["val_mae"] for h in history}

    print("\n" + "=" * 80, flush=True)
    print("K=128 EXPERIMENT RESULTS (VAL MAE in RAW Sales Units)", flush=True)
    print("=" * 80, flush=True)

    check_epochs = [1, 5, 10, 15, 20]
    header = f"| {'Experiment':<45} | " + " | ".join([f"Ep {e:<2}" for e in check_epochs]) + " | Best Val MAE |"
    sep = "| " + " | ".join(["---"] * (len(check_epochs) + 2)) + " |"

    print(header, flush=True)
    print(sep, flush=True)

    vals = [f"{hist_by_epoch.get(e, float('nan')):>6.2f}" for e in check_epochs]
    best = min(hist_by_epoch.values())
    print(f"| {'Exp 4: K=128 Clustering (lr=1e-3, tau=0.01)':<45} | " + " | ".join(vals) + f" | {best:>12.2f} |", flush=True)

    print("=" * 80, flush=True)


if __name__ == "__main__":
    main()

"""
run_experiments.py -- Run 3 hyperparameter experiments (20 epochs each) to find best config.

Experiment 1: Lower learning rate (lr=3e-4, tau=0.1, patience=20)
Experiment 2: Reduced KL weight   (lr=1e-3, tau=0.01, patience=20)
Experiment 3: Increased patience  (lr=1e-3, tau=0.1, patience=20)
"""

import os
import sys
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

from train import train_vae


def main():
    print("=" * 80, flush=True)
    print("RUNNING 3 HYPERPARAMETER EXPERIMENTS (20 EPOCHS EACH)", flush=True)
    print("=" * 80, flush=True)

    experiments = [
        {
            "name": "Exp 1: Lower LR (lr=3e-4)",
            "kwargs": {
                "max_epochs": 20,
                "patience": 20,
                "lr": 3e-4,
                "tau": 0.1,
                "checkpoint_filename": "exp1_lr3e4.pt",
            },
        },
        {
            "name": "Exp 2: Reduced KL Weight (tau=0.01)",
            "kwargs": {
                "max_epochs": 20,
                "patience": 20,
                "lr": 1e-3,
                "tau": 0.01,
                "checkpoint_filename": "exp2_tau001.pt",
            },
        },
        {
            "name": "Exp 3: Default config / Higher Patience (lr=1e-3, tau=0.1)",
            "kwargs": {
                "max_epochs": 20,
                "patience": 20,
                "lr": 1e-3,
                "tau": 0.1,
                "checkpoint_filename": "exp3_patience20.pt",
            },
        },
    ]

    all_results = {}

    for exp in experiments:
        name = exp["name"]
        kwargs = exp["kwargs"]

        print(f"\n" + "#" * 80, flush=True)
        print(f"STARTING EXPERIMENT: {name}", flush=True)
        print("#" * 80, flush=True)

        best_mae, history = train_vae(**kwargs)

        # Store history mapped by epoch
        hist_by_epoch = {h["epoch"]: h["val_mae"] for h in history}
        all_results[name] = hist_by_epoch

    # Print summary table at epochs 1, 5, 10, 15, 20
    print("\n" + "=" * 80, flush=True)
    print("HYPERPARAMETER EXPERIMENTS COMPARISON (VAL MAE in RAW Sales Units)", flush=True)
    print("=" * 80, flush=True)

    check_epochs = [1, 5, 10, 15, 20]
    header = f"| {'Experiment':<45} | " + " | ".join([f"Ep {e:<2}" for e in check_epochs]) + " | Best Val MAE |"
    sep = "| " + " | ".join(["---"] * (len(check_epochs) + 2)) + " |"

    print(header, flush=True)
    print(sep, flush=True)

    for name, hist in all_results.items():
        vals = [f"{hist.get(e, float('nan')):>6.2f}" for e in check_epochs]
        best = min(hist.values())
        print(f"| {name:<45} | " + " | ".join(vals) + f" | {best:>12.2f} |", flush=True)

    print("=" * 80, flush=True)


if __name__ == "__main__":
    main()

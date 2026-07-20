"""Experiment 3: Batch Picking vs Single-Order Picking.

Compares batch picking (time-window accumulation) with single-order
picking, both using the Largest Gap strategy internally.

Usage:
    python scripts/run_batch_experiment.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.experiment import run_experiment

print("=" * 60)
print("  Experiment 3: Batch Picking Comparison")
print("  Modes: Single-Order (LG) | Batch (LG)")
print("  Factors: arrival_rate × batch_window")
print("  Runs: 2 × 3 × 3 × 5 = 90 simulations")
print("=" * 60)

parameter_grid = {
    "arrival_mean": [180.0, 300.0, 600.0],
    "batch_window": [120.0, 300.0, 600.0],
}
common = {
    "num_aisles": 10,
    "positions_per_aisle": 20,
    "num_pickers": 2,
    "duration": 28800.0,
    "warmup": 3600.0,
}
strategies = ["largest_gap", "batch_lg"]

path = run_experiment(
    parameter_grid, strategies, common, replications=5,
    output_csv="batch_experiment.csv",
)
print(f"\nOutput: {path}")

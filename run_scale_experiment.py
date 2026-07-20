"""Experiment 2: Warehouse Scale Sensitivity.

Compares strategies (S-Shape, Largest Gap, HSGA) across different
warehouse sizes (5, 10, 20 aisles).

Usage:
    python scripts/run_scale_experiment.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.experiment import run_experiment

print("=" * 60)
print("  Experiment 2: Warehouse Scale Sensitivity")
print("  Strategies: S-Shape | Largest Gap | HSGA")
print("  Factors: num_aisles")
print("  Runs: 3 × 3 × 5 = 45 simulations")
print("=" * 60)

parameter_grid = {
    "num_aisles": [5, 10, 20],
    "num_pickers": [2],
}
common = {
    "positions_per_aisle": 20,
    "arrival_mean": 300.0,
    "duration": 28800.0,
    "warmup": 3600.0,
    "ga_generations": 30,
    "ga_pop_size": 20,
}
strategies = ["s_shape", "largest_gap", "hybrid_ga"]

path = run_experiment(
    parameter_grid, strategies, common, replications=5,
    output_csv="scale_experiment.csv",
)
print(f"\nOutput: {path}")

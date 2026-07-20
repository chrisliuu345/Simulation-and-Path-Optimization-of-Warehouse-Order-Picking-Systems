"""Experiment 1: Strategy Productivity Comparison.

Compares four path-planning strategies (S-Shape, Largest Gap, GA, HSGA)
across different arrival rates and picker counts.

Usage:
    python scripts/run_productivity_experiment.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.experiment import run_experiment

print("=" * 60)
print("  Experiment 1: Strategy Productivity Comparison")
print("  Strategies: S-Shape | Largest Gap | GA | HSGA")
print("  Factors: arrival_rate × num_pickers")
print("  Runs: 4 × 3 × 2 × 5 = 120 simulations")
print("=" * 60)

parameter_grid = {
    "arrival_mean": [180.0, 300.0, 600.0],
    "num_pickers": [1, 2],
}
common = {
    "num_aisles": 10,
    "positions_per_aisle": 20,
    "duration": 28800.0,
    "warmup": 3600.0,
    "ga_generations": 30,
    "ga_pop_size": 20,
}
strategies = ["s_shape", "largest_gap", "genetic", "hybrid_ga"]

path = run_experiment(
    parameter_grid, strategies, common, replications=5,
    output_csv="productivity_experiment.csv",
)
print(f"\nOutput: {path}")

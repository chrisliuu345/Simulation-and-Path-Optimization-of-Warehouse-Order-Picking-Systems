"""Run all three experiments sequentially and generate plots.

Usage:
    python scripts/run_all_experiments.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.experiment import default_productivity_experiment, default_scale_experiment, default_batch_experiment

print("=" * 60)
print("  Full Experiment Suite — 255 simulations total")
print("=" * 60)

p1 = default_productivity_experiment()
print()

p2 = default_scale_experiment()
print()

p3 = default_batch_experiment()
print()

# Generate plots
print("\nGenerating visualizations...")
from src.visualize import generate_all_plots
generate_all_plots(p1)
generate_all_plots(p2)
generate_all_plots(p3)
# Re-run productivity last to restore strategy_comparison.png with 4 strategies
generate_all_plots(p1)

print(f"\nDone. Output files:")
print(f"  {p1}")
print(f"  {p2}")
print(f"  {p3}")
print(f"  results/*.png")

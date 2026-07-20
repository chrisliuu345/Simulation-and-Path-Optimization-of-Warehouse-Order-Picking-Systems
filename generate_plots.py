"""Generate all visualization charts from experiment CSV data.

Usage:
    python scripts/generate_plots.py                          # all available CSVs
    python scripts/generate_plots.py results/data.csv          # specific file
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.visualize import generate_all_plots

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")

if len(sys.argv) > 1:
    generate_all_plots(sys.argv[1])
else:
    csv_order = [
        "scale_experiment.csv",
        "batch_experiment.csv",
        "productivity_experiment.csv",
        "productivity_experiment.csv",  # again to restore strategy_comparison
    ]
    for name in csv_order:
        path = os.path.join(RESULTS_DIR, name)
        if os.path.exists(path):
            print(f"\n--- {name} ---")
            generate_all_plots(path)
    print("\nAll plots generated in results/")

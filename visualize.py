"""Visualization module for simulation experiment results.

Generates:
  - Box plots comparing strategies
  - Heatmaps for sensitivity analysis
  - Throughput vs arrival rate line charts
"""

from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np

plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
import csv
from collections import defaultdict

from src.experiment import RESULTS_DIR


def ensure_results_dir() -> str:
    os.makedirs(RESULTS_DIR, exist_ok=True)
    return RESULTS_DIR


def load_csv(csv_path: str) -> list[dict]:
    """Load experiment CSV into list of dicts."""
    rows = []
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            for key in [
                "orders_completed",
                "throughput_orders_hr",
                "avg_distance_m",
                "avg_flow_time_s",
                "avg_wait_time_s",
                "utilization",
            ]:
                row[key] = float(row[key])
            for int_key in ["replication", "num_pickers"]:
                if int_key in row:
                    row[int_key] = int(float(row[int_key]))
            if "arrival_mean" in row:
                row["arrival_mean"] = float(row["arrival_mean"])
            if "num_aisles" in row:
                row["num_aisles"] = int(float(row["num_aisles"]))
            rows.append(row)
    return rows


def plot_strategy_comparison(csv_path: str, output_name: str = "strategy_comparison.png") -> str:
    """Box plot comparing three strategies on key KPIs."""
    rows = load_csv(csv_path)
    results_dir = ensure_results_dir()

    strategies = ["s_shape", "largest_gap", "genetic"]
    strategy_data: dict[str, dict[str, list[float]]] = {
        s: defaultdict(list) for s in strategies
    }

    for row in rows:
        st = row["strategy"]
        if st not in strategy_data:
            continue
        for metric in ["avg_distance_m", "throughput_orders_hr", "avg_flow_time_s"]:
            strategy_data[st][metric].append(row[metric])

    available_strats = [s for s in strategies if len(strategy_data[s]["avg_distance_m"]) > 0]

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    metrics = ["avg_distance_m", "throughput_orders_hr", "avg_flow_time_s"]
    titles = ["Avg Distance (m)", "Throughput (orders/hr)", "Avg Flow Time (s)"]

    for ax, metric, title in zip(axes, metrics, titles):
        box_data = [strategy_data[s][metric] for s in available_strats]
        bp = ax.boxplot(
            box_data,
        patch_artist=True,
    )
        ax.set_xticklabels(
            [s.replace("_", "\n").title() for s in available_strats]
        )
        colors = ["#3498db", "#2ecc71", "#e74c3c"]
        for patch, color in zip(bp["boxes"], colors[:len(available_strats)]):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        ax.set_title(title)
        ax.grid(axis="y", alpha=0.3)

    fig.suptitle("Strategy Performance Comparison", fontsize=14, fontweight="bold")
    plt.tight_layout()

    output_path = os.path.join(results_dir, output_name)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {output_path}")
    return output_path


def plot_arrival_sensitivity(csv_path: str, output_name: str = "arrival_sensitivity.png") -> str:
    """Line chart: throughput/flow time vs arrival rate."""
    rows = load_csv(csv_path)
    results_dir = ensure_results_dir()

    grouped: dict[str, dict[float, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for row in rows:
        am = row.get("arrival_mean", None)
        if am is None:
            continue
        grouped[row["strategy"]][am].append(row["throughput_orders_hr"])

    if not grouped:
        print("No arrival_mean data found in CSV.")
        return ""

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = {"s_shape": "#3498db", "largest_gap": "#2ecc71", "genetic": "#e74c3c"}

    for strat, data in sorted(grouped.items()):
        x_vals = sorted(data.keys())
        y_means = [np.mean(data[x]) for x in x_vals]
        y_std = [np.std(data[x]) for x in x_vals]

        label = strat.replace("_", " ").title()
        ax.errorbar(
            x_vals, y_means, yerr=y_std,
            marker="o", capsize=4, label=label, color=colors.get(strat, "#999"),
            linewidth=2,
        )

    # Convert arrival_mean (seconds) to orders/hour on x-axis
    ax.set_xlabel("Mean Inter-Arrival Time (s)")
    ax.set_ylabel("Throughput (orders/hr)")
    ax.set_title("Throughput vs Order Arrival Rate")
    ax.legend()
    ax.grid(True, alpha=0.3)

    output_path = os.path.join(results_dir, output_name)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {output_path}")
    return output_path


def plot_picker_sensitivity(csv_path: str, output_name: str = "picker_sensitivity.png") -> str:
    """Heatmap/bar chart: performance vs number of pickers."""
    rows = load_csv(csv_path)
    results_dir = ensure_results_dir()

    grouped: dict[str, dict[int, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for row in rows:
        np_val = row.get("num_pickers", None)
        if np_val is None:
            continue
        grouped[row["strategy"]][int(np_val)].append(row["avg_distance_m"])

    if not grouped:
        print("No num_pickers data found in CSV.")
        return ""

    strategies = sorted(grouped.keys())
    picker_counts = sorted(
        {p for s in strategies for p in grouped[s].keys()}
    )

    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(picker_counts))
    width = 0.25
    colors = {"s_shape": "#3498db", "largest_gap": "#2ecc71", "genetic": "#e74c3c"}

    for i, strat in enumerate(strategies):
        means = [np.mean(grouped[strat].get(p, [0])) for p in picker_counts]
        stds = [np.std(grouped[strat].get(p, [0])) for p in picker_counts]
        bar = ax.bar(
            x + i * width, means, width,
            label=strat.replace("_", " ").title(),
            yerr=stds, capsize=3, color=colors.get(strat, "#999"),
        )

    ax.set_xlabel("Number of Pickers")
    ax.set_ylabel("Avg Distance (m)")
    ax.set_title("Average Distance vs Number of Pickers")
    ax.set_xticks(x + width)
    ax.set_xticklabels(picker_counts)
    ax.legend()
    ax.grid(axis="y", alpha=0.3)

    output_path = os.path.join(results_dir, output_name)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {output_path}")
    return output_path


def plot_scale_sensitivity(csv_path: str, output_name: str = "scale_sensitivity.png") -> str:
    """Bar chart: distance vs warehouse scale (num_aisles)."""
    rows = load_csv(csv_path)
    results_dir = ensure_results_dir()

    grouped: dict[str, dict[int, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for row in rows:
        na = row.get("num_aisles", None)
        if na is None:
            continue
        grouped[row["strategy"]][int(na)].append(row["avg_distance_m"])

    if not grouped:
        print("No num_aisles data found in CSV.")
        return ""

    strategies = sorted(grouped.keys())
    aisle_counts = sorted({a for s in strategies for a in grouped[s].keys()})

    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(aisle_counts))
    width = 0.35
    colors = {"s_shape": "#3498db", "largest_gap": "#2ecc71", "genetic": "#e74c3c"}

    for i, strat in enumerate(strategies):
        means = [np.mean(grouped[strat].get(a, [0])) for a in aisle_counts]
        stds = [np.std(grouped[strat].get(a, [0])) for a in aisle_counts]
        ax.bar(
            x + i * width, means, width,
            label=strat.replace("_", " ").title(),
            yerr=stds, capsize=3, color=colors.get(strat, "#999"),
        )

    ax.set_xlabel("Number of Aisles")
    ax.set_ylabel("Avg Distance (m)")
    ax.set_title("Average Distance vs Warehouse Scale")
    ax.set_xticks(x + width / 2)
    ax.set_xticklabels(aisle_counts)
    ax.legend()
    ax.grid(axis="y", alpha=0.3)

    output_path = os.path.join(results_dir, output_name)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {output_path}")
    return output_path


def plot_batch_comparison(csv_path: str, output_name: str = "batch_comparison.png") -> str:
    """Line chart: batch picking vs single-order (avg distance per order)."""
    rows = load_csv(csv_path)
    results_dir = ensure_results_dir()

    # Group by strategy x batch_window (only meaningful for batch_lg)
    grouped: dict[str, dict[float, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for row in rows:
        strat = row["strategy"]
        if strat == "batch_lg":
            bw = float(row.get("batch_window", 300))
        else:
            bw = 0  # single-order
        grouped[strat][bw].append(row["avg_distance_m"])

    if not grouped:
        return ""

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))

    # Subplot 1: distance per order
    colors = {"largest_gap": "#2ecc71", "batch_lg": "#e74c3c"}
    for strat in ["largest_gap", "batch_lg"]:
        if strat not in grouped:
            continue
        strat_grouped = grouped[strat]
        x_vals = sorted(strat_grouped.keys())
        y_means = [np.mean(strat_grouped[x]) for x in x_vals]
        y_std = [np.std(strat_grouped[x]) for x in x_vals]
        label = "单订单拣选 (LG)" if strat == "largest_gap" else "分批拣选 (LG)"
        ax1.errorbar(x_vals, y_means, yerr=y_std, marker="o", capsize=4,
                     label=label, color=colors[strat], linewidth=2)

    ax1.set_xlabel("Batch Window (s)")
    ax1.set_ylabel("Avg Distance per Order (m)")
    ax1.set_title("Distance per Order: Batch vs Single")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Subplot 2: throughput
    grouped_tp = defaultdict(lambda: defaultdict(list))
    for row in rows:
        strat = row["strategy"]
        if strat == "batch_lg":
            bw = float(row.get("batch_window", 300))
        else:
            bw = 0
        grouped_tp[strat][bw].append(row["throughput_orders_hr"])

    for strat in ["largest_gap", "batch_lg"]:
        if strat not in grouped_tp:
            continue
        strat_grouped = grouped_tp[strat]
        x_vals = sorted(strat_grouped.keys())
        y_means = [np.mean(strat_grouped[x]) for x in x_vals]
        y_std = [np.std(strat_grouped[x]) for x in x_vals]
        label = "单订单拣选 (LG)" if strat == "largest_gap" else "分批拣选 (LG)"
        ax2.errorbar(x_vals, y_means, yerr=y_std,
                     marker="s", capsize=4, label=label,
                     color=colors[strat], linewidth=2)

    ax2.set_xlabel("Batch Window (s)")
    ax2.set_ylabel("Throughput (orders/hr)")
    ax2.set_title("Throughput: Batch vs Single")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    fig.suptitle("Batch Picking Performance vs Single-Order Picking", fontsize=13, fontweight="bold")
    plt.tight_layout()

    output_path = os.path.join(results_dir, output_name)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {output_path}")
    return output_path


def generate_all_plots(csv_path: str) -> None:
    """Generate all standard plots from experiment CSV."""
    print(f"Loading: {csv_path}")
    rows = load_csv(csv_path)
    if not rows:
        print("No data found in CSV.")
        return
    print(f"  {len(rows)} data rows loaded")

    plot_strategy_comparison(csv_path)
    if "arrival_mean" in rows[0]:
        plot_arrival_sensitivity(csv_path)
        plot_picker_sensitivity(csv_path)
    if "num_aisles" in rows[0]:
        plot_scale_sensitivity(csv_path)
    if "batch_window" in rows[0]:
        plot_batch_comparison(csv_path)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        generate_all_plots(sys.argv[1])
    else:
        csv_files = [
            f for f in os.listdir(RESULTS_DIR) if f.endswith(".csv")
        ]
        if csv_files:
            latest = max(
                csv_files,
                key=lambda f: os.path.getmtime(
                    os.path.join(RESULTS_DIR, f)
                ),
            )
            generate_all_plots(os.path.join(RESULTS_DIR, latest))
        else:
            print("No CSV files found in results/. Run experiment.py first.")

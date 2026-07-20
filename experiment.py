"""Batch experiment runner with parameter sweeps and multiple replications.

Conducts full-factorial experiments over key parameters, recording KPIs
for statistical analysis and visualization.
"""

from __future__ import annotations

import csv
import os
import sys
import time
from itertools import product
from typing import Any

import numpy as np

from src.warehouse import Warehouse
from src.order_gen import OrderGenerator
from src.simulation import PickSimulation, SimulationStats
from src.algorithms.s_shape import SShapeStrategy
from src.algorithms.largest_gap import LargestGapStrategy
from src.algorithms.genetic import GeneticAlgorithm
from src.algorithms.hybrid_ga import HybridGA
from src.algorithms.batch_picking import BatchPickSimulation
from src.config import (
    NUM_PICKERS,
    SIMULATION_DURATION,
    NUM_REPLICATIONS,
)

RESULTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "results"
)


def ensure_results_dir() -> str:
    os.makedirs(RESULTS_DIR, exist_ok=True)
    return RESULTS_DIR


def run_experiment(
    parameter_grid: dict[str, list[Any]],
    strategies: list[str],
    common_params: dict[str, Any],
    replications: int = NUM_REPLICATIONS,
    output_csv: str = "experiment_results.csv",
    verbose: bool = True,
) -> str:
    """Run a full-factorial experiment.

    Args:
        parameter_grid: dict of parameter_name -> list of values
        strategies: list of strategy names to compare
        common_params: fixed parameters (warehouse size, etc.)
        replications: number of replications per parameter combination
        output_csv: output filename in results/ directory
        verbose: print progress

    Returns:
        Path to the generated CSV file.
    """
    results_dir = ensure_results_dir()
    csv_path = os.path.join(results_dir, output_csv)

    param_names = list(parameter_grid.keys())
    param_combos = list(product(*parameter_grid.values()))

    headers = (
        ["strategy", "replication"]
        + param_names
        + [
            "orders_completed",
            "throughput_orders_hr",
            "avg_distance_m",
            "avg_flow_time_s",
            "avg_wait_time_s",
            "utilization",
            "run_time_s",
        ]
    )

    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)

        total_runs = len(strategies) * len(param_combos) * replications
        run_idx = 0

        for strat_name in strategies:
            for combo_idx, combo in enumerate(param_combos):
                params = dict(zip(param_names, combo))

                for rep in range(replications):
                    t0 = time.time()

                    seed = (combo_idx + 1) * 1000 + rep
                    merged = {**common_params, **params}
                    stats = _run_single_trial(merged, strat_name, seed)

                    elapsed = time.time() - t0
                    row = (
                        [strat_name, rep]
                        + [params[p] for p in param_names]
                        + [
                            len(stats.orders),
                            round(stats.throughput(), 2),
                            round(stats.avg_distance(), 1),
                            round(stats.avg_flow_time(), 1),
                            round(stats.avg_wait_time(), 1),
                            round(
                                stats.avg_utilization(merged.get("duration", SIMULATION_DURATION)),
                                3,
                            ),
                            round(elapsed, 1),
                        ]
                    )
                    writer.writerow(row)

                    run_idx += 1
                    if verbose and run_idx % max(1, total_runs // 10) == 0:
                        print(
                            f"  [{run_idx}/{total_runs}] "
                            f"{strat_name} combos={combo_idx+1}/{len(param_combos)} "
                            f"rep={rep+1}/{replications}"
                        )

    if verbose:
        print(f"\nResults saved to: {csv_path}")
    return csv_path


def _run_single_trial(
    params: dict[str, Any], strategy_name: str, seed: int
) -> SimulationStats:
    """Execute one simulation trial."""
    warehouse = Warehouse(
        num_aisles=params.get("num_aisles", 10),
        positions_per_aisle=params.get("positions_per_aisle", 20),
        seed=seed,
    )

    order_gen = OrderGenerator(
        warehouse.sku_pick_weight,
        arrival_mean=params.get("arrival_mean", 300.0),
        skus_per_order=(
            params.get("skus_min", 5),
            params.get("skus_max", 15),
        ),
        seed=seed + 1,
    )

    if strategy_name == "s_shape":
        strategy = SShapeStrategy(warehouse)
    elif strategy_name == "largest_gap":
        strategy = LargestGapStrategy(warehouse)
    elif strategy_name == "genetic":
        strategy = GeneticAlgorithm(
            warehouse,
            seed=seed + 2,
            generations=params.get("ga_generations", 50),
            pop_size=params.get("ga_pop_size", 30),
        )
    elif strategy_name == "hybrid_ga":
        strategy = HybridGA(
            warehouse,
            seed=seed + 2,
            generations=params.get("ga_generations", 50),
            pop_size=params.get("ga_pop_size", 30),
        )
    elif strategy_name == "batch_lg":
        strategy = LargestGapStrategy(warehouse)
    else:
        raise ValueError(f"Unknown strategy: {strategy_name}")

    # Batch mode uses BatchPickSimulation
    if strategy_name.startswith("batch_"):
        batch_window = params.get("batch_window", 300.0)
        sim = BatchPickSimulation(
            warehouse=warehouse,
            order_gen=order_gen,
            strategy=strategy,
            num_pickers=params.get("num_pickers", NUM_PICKERS),
            batch_window=batch_window,
            warmup=params.get("warmup", 3600.0),
            seed=seed + 3,
        )
        return sim.run(duration=params.get("duration", SIMULATION_DURATION))

    sim = PickSimulation(
        warehouse=warehouse,
        order_gen=order_gen,
        strategy=strategy,
        num_pickers=params.get("num_pickers", NUM_PICKERS),
        warmup=params.get("warmup", 3600.0),
        seed=seed + 3,
    )
    return sim.run(duration=params.get("duration", SIMULATION_DURATION))


def default_productivity_experiment() -> str:
    """Run standard productivity comparison experiment."""
    print("Running default productivity comparison experiment...")
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
    return run_experiment(parameter_grid, strategies, common, replications=5,
                          output_csv="productivity_experiment.csv")


def default_scale_experiment() -> str:
    """Run warehouse scale sensitivity experiment."""
    print("Running warehouse scale sensitivity experiment...")
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
    return run_experiment(parameter_grid, strategies, common, replications=5,
                          output_csv="scale_experiment.csv")


def default_batch_experiment() -> str:
    """Run batch picking vs single-order picking experiment."""
    print("Running batch picking comparison experiment...")
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
    return run_experiment(parameter_grid, strategies, common, replications=5,
                          output_csv="batch_experiment.csv")


if __name__ == "__main__":
    path1 = default_productivity_experiment()
    path2 = default_scale_experiment()
    path3 = default_batch_experiment()
    print(f"\nProductivity results: {path1}")
    print(f"Scale results: {path2}")
    print(f"Batch results: {path3}")

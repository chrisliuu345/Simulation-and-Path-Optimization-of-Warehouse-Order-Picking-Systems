"""SimPy-based discrete-event simulation of warehouse order picking.

Models pickers as SimPy Resources that process incoming orders, computing
picking routes using a configurable strategy.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any

import simpy
import numpy as np

from src.warehouse import Warehouse
from src.order_gen import OrderGenerator
from src.algorithms.s_shape import SShapeStrategy
from src.algorithms.largest_gap import LargestGapStrategy
from src.algorithms.genetic import GeneticAlgorithm
from src.algorithms.hybrid_ga import HybridGA
from src.config import (
    PICKER_SPEED,
    PICK_TIME_PER_ITEM,
    SIMULATION_DURATION,
    NUM_PICKERS,
)


@dataclass
class OrderRecord:
    order_id: int
    arrival_time: float
    start_time: float
    finish_time: float
    num_items: int
    distance: float
    wait_time: float
    flow_time: float


@dataclass
class SimulationStats:
    orders: list[OrderRecord] = field(default_factory=list)
    picker_busy_time: dict[int, float] = field(default_factory=dict)

    def throughput(self) -> float:
        if not self.orders:
            return 0.0
        t0 = min(o.arrival_time for o in self.orders)
        t1 = max(o.finish_time for o in self.orders)
        dur = (t1 - t0) / 3600.0
        return len(self.orders) / dur if dur > 0 else 0.0

    def avg_distance(self) -> float:
        if not self.orders:
            return 0.0
        return sum(o.distance for o in self.orders) / len(self.orders)

    def avg_flow_time(self) -> float:
        if not self.orders:
            return 0.0
        return sum(o.flow_time for o in self.orders) / len(self.orders)

    def avg_wait_time(self) -> float:
        if not self.orders:
            return 0.0
        return sum(o.wait_time for o in self.orders) / len(self.orders)

    def avg_utilization(self, total_time: float) -> float:
        if not self.picker_busy_time:
            return 0.0
        total_busy = sum(self.picker_busy_time.values())
        return total_busy / (len(self.picker_busy_time) * total_time)


class PickSimulation:
    """Warehouse picking simulation."""

    def __init__(
        self,
        warehouse: Warehouse,
        order_gen: OrderGenerator,
        strategy: Any,
        num_pickers: int = NUM_PICKERS,
        warmup: float = 3600.0,
        seed: int | None = 42,
    ) -> None:
        self.warehouse = warehouse
        self.order_gen = order_gen
        self.strategy = strategy
        self.num_pickers = num_pickers
        self.warmup = warmup
        self.seed = seed
        self.env = simpy.Environment()
        self.picker_pool = simpy.Resource(self.env, capacity=num_pickers)
        self.stats = SimulationStats()
        self.order_counter = 0
        self.rng = random.Random(seed)

    def run(self, duration: float = SIMULATION_DURATION) -> SimulationStats:
        """Run the simulation and return statistics."""
        self.stats = SimulationStats()
        sim_seed = self.seed if self.seed is not None else 42
        self.env = simpy.Environment()
        self.picker_pool = simpy.Resource(self.env, capacity=self.num_pickers)
        self.order_counter = 0
        self.rng = random.Random(sim_seed)
        arr_gen = np.random.default_rng(sim_seed)

        self.env.process(self._order_arrival_process(duration, arr_gen))
        self.env.run(until=duration)
        return self.stats

    def _order_arrival_process(
        self, duration: float, arr_rng: np.random.Generator
    ):
        """Generate orders with Poisson inter-arrival times."""
        while True:
            gap = max(0.1, arr_rng.exponential(self.order_gen.arrival_mean))
            yield self.env.timeout(gap)
            if self.env.now >= duration:
                break
            order = self.order_gen.generate_order()
            self.order_counter += 1
            self.env.process(
                self._picker_process(self.env.now, self.order_counter, order)
            )

    def _picker_process(
        self, arrival: float, order_id: int, sku_ids: list[int]
    ):
        """Process a single order: wait for picker, walk, pick, record."""
        with self.picker_pool.request() as request:
            yield request

            start_time = self.env.now
            wait = start_time - arrival
            picker_id = id(request)

            locations = [self.warehouse.get_location(sku) for sku in sku_ids]
            try:
                _, distance, _ = self.strategy.calculate_path(locations)
            except Exception:
                distance = self.warehouse.compute_path_distance(locations)

            walk_time = distance / PICKER_SPEED
            yield self.env.timeout(walk_time)
            yield self.env.timeout(len(locations) * PICK_TIME_PER_ITEM)

            finish_time = self.env.now

            if self.warmup <= 0 or arrival >= self.warmup:
                record = OrderRecord(
                    order_id=order_id,
                    arrival_time=arrival,
                    start_time=start_time,
                    finish_time=finish_time,
                    num_items=len(sku_ids),
                    distance=distance,
                    wait_time=wait,
                    flow_time=finish_time - arrival,
                )
                self.stats.orders.append(record)

            busy = finish_time - start_time
            self.stats.picker_busy_time[picker_id] = (
                self.stats.picker_busy_time.get(picker_id, 0.0) + busy
            )


def create_strategy(name: str, warehouse: Warehouse) -> Any:
    """Factory for picking strategies."""
    strategies = {
        's_shape': SShapeStrategy,
        'largest_gap': LargestGapStrategy,
        'genetic': GeneticAlgorithm,
        'hybrid_ga': HybridGA,
    }
    cls = strategies.get(name)
    if cls is None:
        raise ValueError(f"Unknown strategy: {name}. "
                         f"Options: {list(strategies.keys())}")
    return cls(warehouse)


def run_single_simulation(
    warehouse: Warehouse,
    order_gen: OrderGenerator,
    strategy_name: str,
    num_pickers: int = NUM_PICKERS,
    duration: float = SIMULATION_DURATION,
    seed: int | None = 42,
) -> SimulationStats:
    """Convenience function to run one simulation."""
    strategy = create_strategy(strategy_name, warehouse)
    sim = PickSimulation(
        warehouse=warehouse,
        order_gen=order_gen,
        strategy=strategy,
        num_pickers=num_pickers,
        seed=seed,
    )
    return sim.run(duration)


def print_stats(stats: SimulationStats, label: str = "") -> None:
    """Pretty-print simulation statistics."""
    if label:
        print(f"\n{'='*50}")
        print(f"  {label}")
        print(f"{'='*50}")
    print(f"  Orders completed:     {len(stats.orders)}")
    print(f"  Throughput:           {stats.throughput():.2f} orders/hr")
    print(f"  Avg distance:         {stats.avg_distance():.1f} m")
    print(f"  Avg flow time:        {stats.avg_flow_time():.1f} s")
    print(f"  Avg wait time:        {stats.avg_wait_time():.1f} s")


if __name__ == "__main__":
    warehouse = Warehouse(seed=42)
    print(warehouse.describe())

    order_gen = OrderGenerator(warehouse.sku_pick_weight, seed=99)

    for strat_name in ["s_shape", "largest_gap"]:
        stats = run_single_simulation(
            warehouse, order_gen, strat_name, seed=42
        )
        print_stats(stats, f"Strategy: {strat_name}")

    print("\nRunning GA (this may take ~30s for 100 orders)...")
    ga_stats = run_single_simulation(
        warehouse, order_gen, "genetic", seed=42
    )
    print_stats(ga_stats, "Strategy: genetic")

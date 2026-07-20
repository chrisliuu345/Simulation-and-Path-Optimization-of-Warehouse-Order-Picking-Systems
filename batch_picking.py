"""Batch picking simulation — accumulates orders in time windows and picks jointly.

Instead of one-picker-per-order, orders arriving within a configurable time window
are merged into a batch. One picker picks the entire batch in a single trip,
dividing total distance across all orders in the batch.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

import simpy
import numpy as np

from src.warehouse import Warehouse
from src.order_gen import OrderGenerator
from src.simulation import SimulationStats, OrderRecord
from src.config import PICKER_SPEED, PICK_TIME_PER_ITEM, SIMULATION_DURATION, NUM_PICKERS


@dataclass
class BatchRecord:
    batch_id: int
    num_orders: int
    num_items: int
    distance: float
    arrival_earliest: float
    start_time: float
    finish_time: float


class BatchPickSimulation:
    """Simulation with batch picking — orders grouped by time window."""

    def __init__(
        self,
        warehouse: Warehouse,
        order_gen: OrderGenerator,
        strategy,
        num_pickers: int = NUM_PICKERS,
        batch_window: float = 300.0,
        warmup: float = 3600.0,
        seed: int | None = 42,
    ) -> None:
        self.warehouse = warehouse
        self.order_gen = order_gen
        self.strategy = strategy
        self.num_pickers = num_pickers
        self.batch_window = batch_window
        self.warmup = warmup
        self.seed = seed
        self.env = simpy.Environment()
        self.picker_pool = simpy.Resource(self.env, capacity=num_pickers)
        self.stats = SimulationStats()
        self.batch_stats: list[BatchRecord] = []
        self.order_counter = 0

    def run(self, duration: float = SIMULATION_DURATION) -> SimulationStats:
        self.stats = SimulationStats()
        self.batch_stats = []
        sim_seed = self.seed if self.seed is not None else 42
        self.env = simpy.Environment()
        self.picker_pool = simpy.Resource(self.env, capacity=self.num_pickers)
        self.order_counter = 0
        arr_gen = np.random.default_rng(sim_seed)

        self.env.process(self._batch_arrival_process(duration, arr_gen))
        self.env.run(until=duration)
        return self.stats

    def _batch_arrival_process(self, duration: float, arr_rng: np.random.Generator):
        """Accumulate orders in time windows and dispatch batches."""
        while True:
            batch_start = self.env.now
            if batch_start >= duration:
                break

            batch_end = min(batch_start + self.batch_window, duration)
            orders_in_batch: list[tuple[float, int, list[int]]] = []

            # Collect orders within the window
            while self.env.now < batch_end and self.env.now < duration:
                gap = max(0.1, arr_rng.exponential(self.order_gen.arrival_mean))
                if self.env.now + gap < batch_end:
                    yield self.env.timeout(gap)
                else:
                    yield self.env.timeout(batch_end - self.env.now)
                    break

                if self.env.now >= duration:
                    break

                order = self.order_gen.generate_order()
                self.order_counter += 1
                orders_in_batch.append((self.env.now, self.order_counter, order))

            if orders_in_batch:
                self.env.process(self._batch_picker_process(
                    batch_start, orders_in_batch
                ))

            yield self.env.timeout(max(0, batch_end - self.env.now))

    def _batch_picker_process(
        self, batch_start: float, orders_in_batch: list
    ):
        """Process a batch of orders with one picker."""
        with self.picker_pool.request() as request:
            yield request

            start_time = self.env.now
            picker_id = id(request)

            # Merge all SKU locations from all orders
            all_sku_ids: list[int] = []
            for _, _, skus in orders_in_batch:
                all_sku_ids.extend(skus)
            all_sku_ids = list(set(all_sku_ids))  # deduplicate

            locations = [self.warehouse.get_location(sku) for sku in all_sku_ids]
            try:
                _, distance, _ = self.strategy.calculate_path(locations)
            except Exception:
                distance = self.warehouse.compute_path_distance(locations)

            total_items = sum(len(ords[2]) for ords in orders_in_batch)
            walk_time = distance / PICKER_SPEED
            pick_time = len(all_sku_ids) * PICK_TIME_PER_ITEM

            yield self.env.timeout(walk_time)
            yield self.env.timeout(pick_time)

            finish_time = self.env.now
            num_orders = len(orders_in_batch)

            # Record per-order stats (distance divided equally among orders)
            distance_per_order = distance / num_orders if num_orders > 0 else distance

            for arrival, oid, skus in orders_in_batch:
                if self.warmup <= 0 or arrival >= self.warmup:
                    record = OrderRecord(
                        order_id=oid,
                        arrival_time=arrival,
                        start_time=start_time,
                        finish_time=finish_time,
                        num_items=len(skus),
                        distance=distance_per_order,
                        wait_time=start_time - arrival,
                        flow_time=finish_time - arrival,
                    )
                    self.stats.orders.append(record)

            # Record batch-level stats
            batch_record = BatchRecord(
                batch_id=len(self.batch_stats) + 1,
                num_orders=num_orders,
                num_items=len(all_sku_ids),
                distance=distance,
                arrival_earliest=min(o[0] for o in orders_in_batch),
                start_time=start_time,
                finish_time=finish_time,
            )
            self.batch_stats.append(batch_record)

            busy = finish_time - start_time
            self.stats.picker_busy_time[picker_id] = (
                self.stats.picker_busy_time.get(picker_id, 0.0) + busy
            )

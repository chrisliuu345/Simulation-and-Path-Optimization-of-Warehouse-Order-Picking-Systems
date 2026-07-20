"""Random order generator with Poisson arrivals and ABC-weighted SKU selection."""

import random
import numpy as np

from src.config import (
    ORDER_ARRIVAL_MEAN,
    ORDER_SKUS_MIN,
    ORDER_SKUS_MAX,
)


class OrderGenerator:
    """Generates random pick orders with Poisson inter-arrival times.

    Each order selects SKUs with probability proportional to their pick weight,
    simulating ABC-class demand patterns (A items picked more often).
    """

    def __init__(
        self,
        sku_pick_weights: dict[int, float],
        arrival_mean: float = ORDER_ARRIVAL_MEAN,
        skus_per_order: tuple[int, int] = (ORDER_SKUS_MIN, ORDER_SKUS_MAX),
        seed: int | None = 42,
    ) -> None:
        self.sku_ids = list(sku_pick_weights.keys())
        self.weights = np.array(
            [sku_pick_weights[sku] for sku in self.sku_ids], dtype=float
        )
        self.weights /= self.weights.sum()
        self.arrival_mean = arrival_mean
        self.skus_min, self.skus_max = skus_per_order
        self.rng = np.random.default_rng(seed)
        self.order_id = 0

    def inter_arrival_time(self) -> float:
        """Exponential inter-arrival time (Poisson process)."""
        return self.rng.exponential(self.arrival_mean)

    def generate_order(self) -> list[int]:
        """Generate a single order: list of unique SKU IDs."""
        n_skus = self.rng.integers(self.skus_min, self.skus_max + 1)
        chosen = list(
            self.rng.choice(
                self.sku_ids,
                size=min(n_skus, len(self.sku_ids)),
                p=self.weights,
                replace=False,
            )
        )
        return chosen

    def generate_order_stream(
        self, duration: float
    ) -> list[tuple[float, list[int]]]:
        """Generate a stream of orders over a time duration.

        Returns list of (arrival_time, sku_ids) sorted by arrival time.
        """
        orders = []
        t = 0.0
        while t < duration:
            t += max(0.001, self.inter_arrival_time())
            if t >= duration:
                break
            orders.append((t, self.generate_order()))
        return orders

"""Warehouse model with SKU layout and distance calculations."""

from collections import defaultdict
import numpy as np

from src.config import (
    NUM_AISLES,
    POSITIONS_PER_AISLE,
    LOCATION_SPACING,
    AISLE_SPACING,
    TOTAL_SKUS,
)

A_CLASS_RATIO = 0.2
B_CLASS_RATIO = 0.3


class Warehouse:
    """Rectangular warehouse with parallel aisles and two cross-aisles.

    Coordinate system: (aisle, position)
      - aisle: 0..num_aisles-1 (left to right)
      - position: 0..positions_per_aisle-1 (front=near I/O, back=far)
      - I/O point: front center, at the bottom of the warehouse
    """

    def __init__(
        self,
        num_aisles: int = NUM_AISLES,
        positions_per_aisle: int = POSITIONS_PER_AISLE,
        n_skus: int = TOTAL_SKUS,
        seed: int | None = 42,
    ) -> None:
        self.num_aisles = num_aisles
        self.positions_per_aisle = positions_per_aisle
        self.n_skus = n_skus
        self.location_spacing = LOCATION_SPACING
        self.aisle_spacing = AISLE_SPACING
        self.rng = np.random.default_rng(seed)

        self.sku_locations: dict[int, tuple[int, int]] = {}
        self.sku_class: dict[int, str] = {}
        self.sku_pick_weight: dict[int, float] = {}
        self.class_skus: dict[str, list[int]] = defaultdict(list)

        self._assign_sku_locations()

    def _assign_sku_locations(self) -> None:
        """Assign SKUs to locations with ABC classification.

        Multiple SKUs may share the same storage position.
        A-class (top 20%): placed near I/O — front positions, low aisle numbers.
        B-class (next 30%): mid-range positions.
        C-class (bottom 50%): far positions, high aisle numbers.
        """
        all_positions = [
            (a, p)
            for a in range(self.num_aisles)
            for p in range(self.positions_per_aisle)
        ]
        n_positions = len(all_positions)
        n_a = int(self.n_skus * A_CLASS_RATIO)
        n_b = int(self.n_skus * B_CLASS_RATIO)
        n_c = self.n_skus - n_a - n_b

        ranked_a = sorted(
            all_positions,
            key=lambda ap: ap[1] * 2.0 + ap[0] * 0.5,
        )
        a_candidates = ranked_a[:n_positions // 3]
        ranked_c = sorted(
            all_positions,
            key=lambda ap: -ap[1] * 2.0 - ap[0] * 0.5,
        )
        c_candidates = ranked_c[:n_positions // 3]
        b_candidates_set = set(all_positions) - set(a_candidates) - set(c_candidates)
        b_candidates = list(b_candidates_set)

        def pick_from(pool: list[tuple[int, int]], count: int) -> list[tuple[int, int]]:
            return [
                pool[self.rng.integers(0, len(pool))]
                for _ in range(count)
            ]

        a_assigned = pick_from(a_candidates, n_a)
        b_assigned = pick_from(b_candidates, n_b)
        c_assigned = pick_from(c_candidates, n_c)

        for i, (aisle, pos) in enumerate(a_assigned):
            self.sku_locations[i] = (aisle, pos)
            self.sku_class[i] = "A"
            self.sku_pick_weight[i] = 5.0
            self.class_skus["A"].append(i)
        for j, (aisle, pos) in enumerate(b_assigned):
            i = n_a + j
            self.sku_locations[i] = (aisle, pos)
            self.sku_class[i] = "B"
            self.sku_pick_weight[i] = 2.0
            self.class_skus["B"].append(i)
        for k, (aisle, pos) in enumerate(c_assigned):
            i = n_a + n_b + k
            self.sku_locations[i] = (aisle, pos)
            self.sku_class[i] = "C"
            self.sku_pick_weight[i] = 1.0
            self.class_skus["C"].append(i)

    def get_location(self, sku_id: int) -> tuple[int, int]:
        return self.sku_locations[sku_id]

    def get_io_point(self) -> tuple[float, float]:
        """I/O point at front center (bottom of warehouse)."""
        return ((self.num_aisles - 1) / 2.0, -1.0)

    def distance_to_io(self, aisle: int, position: int) -> float:
        """Distance from a location to the I/O point via the front."""
        io_aisle, _ = self.get_io_point()
        return abs(aisle - io_aisle) * self.aisle_spacing + position * self.location_spacing

    def distance_between_locations(
        self, loc1: tuple[int, int], loc2: tuple[int, int]
    ) -> float:
        """Shortest walking distance between two locations."""
        a1, p1 = loc1
        a2, p2 = loc2
        if a1 == a2:
            return abs(p1 - p2) * self.location_spacing
        via_front = (p1 + p2) * self.location_spacing + abs(a1 - a2) * self.aisle_spacing
        via_back = (
            (2 * self.positions_per_aisle - p1 - p2) * self.location_spacing
            + abs(a1 - a2) * self.aisle_spacing
        )
        return min(via_front, via_back)

    def compute_path_distance(
        self, location_sequence: list[tuple[int, int]]
    ) -> float:
        """Compute total walking distance for a sequence of locations.

        Starts at I/O, visits each location, returns to I/O.
        """
        if not location_sequence:
            return 0.0
        io_aisle, _ = self.get_io_point()
        current_aisle = None
        current_position = None
        total = 0.0
        for aisle, position in location_sequence:
            if current_aisle is None:
                total += self.distance_to_io(aisle, position)
            else:
                total += self.distance_between_locations(
                    (current_aisle, current_position), (aisle, position)
                )
            current_aisle, current_position = aisle, position
        if current_aisle is not None:
            total += self.distance_to_io(current_aisle, current_position)
        return total

    def get_aisle_locations(
        self, locations: list[tuple[int, int]]
    ) -> dict[int, list[int]]:
        """Group locations by aisle ID, returning positions per aisle."""
        groups: dict[int, list[int]] = defaultdict(list)
        for aisle, pos in locations:
            groups[aisle].append(pos)
        for positions in groups.values():
            positions.sort()
        return dict(groups)

    def describe(self) -> str:
        a_count = len(self.class_skus["A"])
        b_count = len(self.class_skus["B"])
        c_count = len(self.class_skus["C"])
        return (
            f"Warehouse({self.num_aisles} aisles x {self.positions_per_aisle} pos)\n"
            f"  SKUs: A={a_count}, B={b_count}, C={c_count}\n"
            f"  Total storage locations: {self.num_aisles * self.positions_per_aisle}"
        )

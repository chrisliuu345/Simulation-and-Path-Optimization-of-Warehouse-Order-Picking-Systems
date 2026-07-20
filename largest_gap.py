"""Largest Gap strategy — enters each aisle from the front, picks up to the
largest gap within the aisle, then returns to the front. Repeats for each aisle
that has picks. Always traverses via the front cross-aisle."""

from __future__ import annotations

from typing import Sequence

from src.warehouse import Warehouse


class LargestGapStrategy:
    """Largest Gap heuristic for order picking."""

    def __init__(self, warehouse: Warehouse) -> None:
        self.warehouse = warehouse

    def calculate_path(
        self, locations: Sequence[tuple[int, int]]
    ) -> tuple[list[tuple[int, int]], float, list[tuple[int, int]]]:
        wp = self.warehouse
        if not locations:
            return [], 0.0, []

        aisle_groups = wp.get_aisle_locations(list(locations))
        sorted_aisles = sorted(aisle_groups.keys())

        route: list[tuple[int, int]] = []
        current_position = (0.0, 0.0)  # I/O area

        for aisle in sorted_aisles:
            positions = aisle_groups[aisle]
            pick_points = self._largest_gap_route(aisle, positions)
            route.extend(pick_points)
            current_position = pick_points[-1]

        distance = wp.compute_path_distance(route)
        return route, distance, route

    def _largest_gap_route(
        self, aisle: int, positions: list[int]
    ) -> list[tuple[int, int]]:
        """Build a route for a single aisle using the largest gap heuristic.

        The picker enters from the front (position 0), walks to the farthest
        needed pick, then returns. Uses the largest gap between consecutive
        picks to determine whether to exit from front or back.
        """
        if len(positions) == 1:
            return [(aisle, positions[0])]

        # Compute gaps: (gap_start, gap_end, gap_size)
        max_aisle_len = self.warehouse.positions_per_aisle
        gaps = []

        # Gap from front (0) to first pick
        gaps.append((0, positions[0], positions[0]))

        # Gaps between consecutive picks
        for k in range(len(positions) - 1):
            gap_size = positions[k + 1] - positions[k]
            gaps.append((positions[k], positions[k + 1], gap_size))

        # Gap from last pick to back
        gaps.append(
            (positions[-1], max_aisle_len, max_aisle_len - positions[-1])
        )

        # Find the largest gap — don't traverse through it
        largest_gap_idx = max(range(len(gaps)), key=lambda i: gaps[i][2])

        # Walk from front to the largest gap start, then return
        if largest_gap_idx == 0:
            # Largest gap is at front — just walk to positions and return
            return [(aisle, p) for p in positions]

        # Walk to the start of the largest gap, picking along the way
        visited = [(aisle, p) for p in positions if p <= gaps[largest_gap_idx][0]]
        # Return same path
        return visited

    def name(self) -> str:
        return "Largest Gap"

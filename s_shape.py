"""S-shape (traversal) picking strategy — baseline.

The picker traverses the warehouse in a snake pattern:
enter the first aisle from the front, walk to the back, cross to the next aisle
via the back cross-aisle, walk from back to front, and so on alternately.
"""

from __future__ import annotations

from src.warehouse import Warehouse


class SShapeStrategy:
    """S-shape routing strategy for order picking."""

    def __init__(self, warehouse: Warehouse) -> None:
        self.warehouse = warehouse

    def calculate_path(
        self, locations: list[tuple[int, int]]
    ) -> tuple[list[tuple[int, int]], float, list[tuple[int, int]]]:
        """Calculate S-shape picking route.

        Returns (visited_order, total_distance, route_waypoints).
        route_waypoints includes aisle entry/exit points for visualization.
        """
        wp = self.warehouse
        if not locations:
            return [], 0.0, []

        aisle_groups = wp.get_aisle_locations(locations)
        sorted_aisles = sorted(aisle_groups.keys())

        route: list[tuple[int, int]] = []
        waypoints: list[tuple[int, int]] = []

        io_aisle, io_pos = wp.get_io_point()

        for i, aisle in enumerate(sorted_aisles):
            positions = aisle_groups[aisle]
            if i % 2 == 0:
                # Front to back (natural order)
                entry_pos = positions[0]
                exit_pos = positions[-1]
                visited = [(aisle, p) for p in positions]
            else:
                # Back to front (reverse order)
                entry_pos = positions[-1]
                exit_pos = positions[0]
                visited = [(aisle, p) for p in reversed(positions)]

            if i == 0:
                waypoints.append((io_aisle, io_pos))  # start
                waypoints.append((aisle, 0))  # front entrance
            else:
                prev_exit = route[-1]
                waypoints.append(prev_exit)
                waypoints.append((aisle, entry_pos))  # new aisle entry

            route.extend(visited)

        waypoints.append(route[-1])
        waypoints.append((io_aisle, io_pos))  # return to I/O

        distance = wp.compute_path_distance(route)
        return route, distance, waypoints

    def name(self) -> str:
        return "S-Shape"

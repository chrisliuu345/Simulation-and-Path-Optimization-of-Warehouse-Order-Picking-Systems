"""Hybrid S-GA (HSGA) — Largest Gap seeds initial GA population.

Unlike pure GA which starts from random permutations, HSGA seeds a fraction of
the initial population with the Largest Gap heuristic ordering. This jump-starts
the search near a known-good region, combining heuristic exploitation with
metaheuristic exploration.
"""

from __future__ import annotations

import copy
import random

from src.warehouse import Warehouse
from src.algorithms.largest_gap import LargestGapStrategy
from src.config import GA_TOURNAMENT_SIZE, GA_CROSSOVER_PROB, GA_MUTATION_PROB, GA_ELITISM


class HybridGA:
    """Hybrid Genetic Algorithm with Largest Gap population seeding."""

    def __init__(
        self,
        warehouse: Warehouse,
        pop_size: int = 50,
        generations: int = 100,
        tournament_size: int = GA_TOURNAMENT_SIZE,
        crossover_prob: float = GA_CROSSOVER_PROB,
        mutation_prob: float = GA_MUTATION_PROB,
        elitism: int = GA_ELITISM,
        seed_ratio: float = 0.4,
        seed: int | None = 42,
    ) -> None:
        self.warehouse = warehouse
        self.pop_size = pop_size
        self.generations = generations
        self.tournament_size = tournament_size
        self.crossover_prob = crossover_prob
        self.mutation_prob = mutation_prob
        self.elitism = elitism
        self.seed_ratio = seed_ratio
        self.rng = random.Random(seed)
        self._lg = LargestGapStrategy(warehouse)
        self._fitness_cache: dict[tuple[int, ...], float] = {}

    def name(self) -> str:
        return "Hybrid GA (HSGA)"

    def calculate_path(
        self, locations: list[tuple[int, int]]
    ) -> tuple[list[tuple[int, int]], float, list[tuple[int, int]]]:
        route, dist = self.optimize(locations)
        return route, dist, route

    def optimize(
        self, locations: list[tuple[int, int]]
    ) -> tuple[list[tuple[int, int]], float]:
        n = len(locations)
        if n == 0:
            return [], 0.0
        if n == 1:
            return [locations[0]], self.warehouse.compute_path_distance(locations)
        if n <= 3:
            return self._brute_force(locations)

        self._fitness_cache.clear()
        pop = self._init_population_hybrid(locations, n)

        for _gen in range(self.generations):
            fitnesses = [(ind, self._fitness(ind, locations)) for ind in pop]
            fitnesses.sort(key=lambda x: x[1])

            new_pop = [fitnesses[i][0].copy() for i in range(self.elitism)]

            while len(new_pop) < self.pop_size:
                parent1 = self._tournament_select(pop, locations)
                parent2 = self._tournament_select(pop, locations)

                if self.rng.random() < self.crossover_prob:
                    child1, child2 = self._pmx_crossover(parent1, parent2)
                    new_pop.append(child1)
                    if len(new_pop) < self.pop_size:
                        new_pop.append(child2)
                else:
                    new_pop.append(parent1.copy())
                    if len(new_pop) < self.pop_size:
                        new_pop.append(parent2.copy())

            new_pop = new_pop[:self.pop_size]

            for i in range(self.elitism, len(new_pop)):
                if self.rng.random() < self.mutation_prob:
                    new_pop[i] = self._swap_mutation(new_pop[i])

            pop = new_pop

        final = [(ind, self._fitness(ind, locations)) for ind in pop]
        best_ind, best_dist = min(final, key=lambda x: x[1])
        best_route = [locations[i] for i in best_ind]
        return best_route, best_dist

    # --- Initialization ---

    def _init_population_hybrid(
        self, locations: list[tuple[int, int]], n: int
    ) -> list[list[int]]:
        """Create initial population with LG-seeded individuals."""
        num_seeded = max(1, int(self.pop_size * self.seed_ratio))
        num_random = self.pop_size - num_seeded

        pop: list[list[int]] = []

        # Seed: get LG ordering and create variants by perturbation
        lg_route, _, _ = self._lg.calculate_path(locations)
        lg_indices = self._route_to_indices(lg_route, locations)

        # Add LG ordering itself
        pop.append(lg_indices.copy())

        # Add perturbed variants of LG ordering
        for _ in range(num_seeded - 1):
            variant = lg_indices.copy()
            swaps = max(1, n // 4)
            for _s in range(swaps):
                i = self.rng.randint(0, n - 1)
                j = self.rng.randint(0, n - 1)
                variant[i], variant[j] = variant[j], variant[i]
            pop.append(variant)

        # Rest: random permutations
        for _ in range(num_random):
            pop.append(self.rng.sample(range(n), n))

        self.rng.shuffle(pop)
        return pop

    def _route_to_indices(
        self, route: list[tuple[int, int]], locations: list[tuple[int, int]]
    ) -> list[int]:
        """Convert a location route to index ordering.
        
        Handles duplicate locations (multiple SKUs at same position).
        """
        from collections import defaultdict
        loc_to_indices: dict[tuple[int, int], list[int]] = defaultdict(list)
        for idx, loc in enumerate(locations):
            loc_to_indices[loc].append(idx)

        indices: list[int] = []
        used = set()
        for loc in route:
            candidates = [i for i in loc_to_indices.get(loc, []) if i not in used]
            if candidates:
                idx = candidates[0]
                indices.append(idx)
                used.add(idx)

        # Append any remaining indices
        for i in range(len(locations)):
            if i not in used:
                indices.append(i)

        return indices

    # --- GA core (reused from GeneticAlgorithm) ---

    def _fitness(self, individual: list[int], locations: list[tuple[int, int]]) -> float:
        key = tuple(individual)
        if key not in self._fitness_cache:
            seq = [locations[j] for j in individual]
            self._fitness_cache[key] = self.warehouse.compute_path_distance(seq)
        return self._fitness_cache[key]

    def _tournament_select(
        self, pop: list[list[int]], locations: list[tuple[int, int]]
    ) -> list[int]:
        candidates = self.rng.sample(pop, self.tournament_size)
        return min(candidates, key=lambda ind: self._fitness(ind, locations))

    def _pmx_crossover(
        self, p1: list[int], p2: list[int]
    ) -> tuple[list[int], list[int]]:
        n = len(p1)
        cx1 = self.rng.randint(0, n - 1)
        cx2 = self.rng.randint(cx1, n - 1)
        c1, c2 = [-1] * n, [-1] * n
        mapping1: dict[int, int] = {}
        mapping2: dict[int, int] = {}
        for i in range(cx1, cx2 + 1):
            c1[i] = p2[i]; c2[i] = p1[i]
            mapping1[p2[i]] = p1[i]; mapping2[p1[i]] = p2[i]
        for i in list(range(0, cx1)) + list(range(cx2 + 1, n)):
            val1 = p1[i]
            while val1 in mapping1: val1 = mapping1[val1]
            c1[i] = val1
            val2 = p2[i]
            while val2 in mapping2: val2 = mapping2[val2]
            c2[i] = val2
        return c1, c2

    def _swap_mutation(self, individual: list[int]) -> list[int]:
        i = self.rng.randint(0, len(individual) - 1)
        j = self.rng.randint(0, len(individual) - 1)
        individual[i], individual[j] = individual[j], individual[i]
        return individual

    def _brute_force(
        self, locations: list[tuple[int, int]]
    ) -> tuple[list[tuple[int, int]], float]:
        import itertools
        n = len(locations)
        best_route = list(locations)
        best_dist = self.warehouse.compute_path_distance(best_route)
        for perm in itertools.permutations(range(n)):
            seq = [locations[i] for i in perm]
            dist = self.warehouse.compute_path_distance(seq)
            if dist < best_dist:
                best_dist = dist; best_route = seq
        return best_route, best_dist

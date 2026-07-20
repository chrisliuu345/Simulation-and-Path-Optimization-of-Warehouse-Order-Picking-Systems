"""Genetic Algorithm for optimal pick-sequence ordering.

Encodes a picking route as a permutation of SKU locations. Uses PMX crossover,
swap mutation, tournament selection with elitism.
"""

from __future__ import annotations

import random
from typing import Callable

import numpy as np

from src.warehouse import Warehouse
from src.config import (
    GA_POP_SIZE,
    GA_GENERATIONS,
    GA_TOURNAMENT_SIZE,
    GA_CROSSOVER_PROB,
    GA_MUTATION_PROB,
    GA_ELITISM,
)


class GeneticAlgorithm:
    """Permutation-based Genetic Algorithm to minimize picking path distance."""

    def __init__(
        self,
        warehouse: Warehouse,
        pop_size: int = GA_POP_SIZE,
        generations: int = GA_GENERATIONS,
        tournament_size: int = GA_TOURNAMENT_SIZE,
        crossover_prob: float = GA_CROSSOVER_PROB,
        mutation_prob: float = GA_MUTATION_PROB,
        elitism: int = GA_ELITISM,
        seed: int | None = 42,
    ) -> None:
        self.warehouse = warehouse
        self.pop_size = pop_size
        self.generations = generations
        self.tournament_size = tournament_size
        self.crossover_prob = crossover_prob
        self.mutation_prob = mutation_prob
        self.elitism = elitism
        self.rng = random.Random(seed)
        self._fitness_cache: dict[tuple[int, ...], float] = {}

    def optimize(
        self, locations: list[tuple[int, int]]
    ) -> tuple[list[tuple[int, int]], float]:
        """Run GA to find the optimal picking sequence.

        Returns (best_route, best_distance).
        """
        n = len(locations)
        if n == 0:
            return [], 0.0
        if n == 1:
            return [locations[0]], self.warehouse.compute_path_distance(locations)
        if n <= 3:
            return self._brute_force(locations)

        self._fitness_cache.clear()
        pop = self._init_population(n)

        for gen in range(self.generations):
            fitnesses = [
                (ind, self._fitness(ind, locations))
                for ind in pop
            ]
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

        fitnesses = [
            (ind, self._fitness(ind, locations))
            for ind in pop
        ]
        best_ind, best_dist = min(fitnesses, key=lambda x: x[1])
        best_route = [locations[i] for i in best_ind]
        return best_route, best_dist

    def calculate_path(
        self, locations: list[tuple[int, int]]
    ) -> tuple[list[tuple[int, int]], float, list[tuple[int, int]]]:
        route, dist = self.optimize(locations)
        return route, dist, route

    def name(self) -> str:
        return "Genetic Algorithm"

    # --- internal helpers ---

    def _init_population(self, n: int) -> list[list[int]]:
        return [self.rng.sample(range(n), n) for _ in range(self.pop_size)]

    def _fitness(
        self, individual: list[int], locations: list[tuple[int, int]]
    ) -> float:
        key = tuple(individual)
        if key not in self._fitness_cache:
            seq = [locations[j] for j in individual]
            self._fitness_cache[key] = self.warehouse.compute_path_distance(seq)
        return self._fitness_cache[key]

    def _tournament_select(
        self, pop: list[list[int]], locations: list[tuple[int, int]]
    ) -> list[int]:
        candidates = self.rng.sample(pop, self.tournament_size)
        return min(
            candidates,
            key=lambda ind: self._fitness(ind, locations),
        )

    def _pmx_crossover(
        self, p1: list[int], p2: list[int]
    ) -> tuple[list[int], list[int]]:
        """Partially Mapped Crossover (PMX) for permutations."""
        n = len(p1)
        cx1 = self.rng.randint(0, n - 1)
        cx2 = self.rng.randint(cx1, n - 1)

        c1 = [-1] * n
        c2 = [-1] * n
        mapping1: dict[int, int] = {}
        mapping2: dict[int, int] = {}

        for i in range(cx1, cx2 + 1):
            c1[i] = p2[i]
            c2[i] = p1[i]
            mapping1[p2[i]] = p1[i]
            mapping2[p1[i]] = p2[i]

        for i in list(range(0, cx1)) + list(range(cx2 + 1, n)):
            val1 = p1[i]
            while val1 in mapping1:
                val1 = mapping1[val1]
            c1[i] = val1

            val2 = p2[i]
            while val2 in mapping2:
                val2 = mapping2[val2]
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
                best_dist = dist
                best_route = seq
        return best_route, best_dist

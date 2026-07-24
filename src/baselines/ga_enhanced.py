"""
Enhanced GA
Main differences from ga_baseline:
    1. Feasibility-aware penalty fitness:
        The fitness function penalizes different constraint violations with
        different weights instead of only using a generic checker-message count.
    2. Feasibility-aware best solution selection:
        During evolution, the selected best chromosome is not necessarily the
        one with the shortest distance. The solver first prefers feasible
        solutions, then fewer violations, and only then shorter distance.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import random
import time
from typing import Optional, Sequence

from src.solution import Solution

from src.baselines.ga_baseline import (
    GAResult,
    _decode_chromosome,
    _distance_between,
    _get_customer_ids,
    _get_depot_id,
    _get_node,
    _mutate,
    _nearest_neighbor_order,
    _ordered_crossover,
    _repair_permutation,
    _safe_check,
    _solution_distance,
)


@dataclass(frozen=True)
class ViolationSummary:
    """
    Parsed checker messages.

    The project checker returns a list of text messages. To make the GA more
    constraint-aware, this class categorizes messages into common EVRP-TW
    violation types.
    """

    total: int
    battery: int
    time_window: int
    capacity: int
    customer: int
    route: int
    other: int


class GAEnhanced:
    """
    Enhanced Genetic Algorithm for EVRP-TW.

    Chromosome:
        A permutation of customer node ids.

    Decoder:
        Uses the same route decoder as the baseline GA.

    Fitness:
        Lower is better.

        fitness =
            distance
            + feasibility penalty
            + weighted violation penalties
            + route count penalty

    Best solution selection:
        Uses a lexicographic key:
            feasible solution first;
            fewer total violations second;
            fewer battery/time-window violations third;
            shorter distance last.
    """

    name = "ga_enhanced"

    def __init__(
        self,
        population_size: int = 40,
        generations: int = 80,
        crossover_rate: float = 0.85,
        mutation_rate: float = 0.20,
        elite_size: int = 2,
        tournament_size: int = 3,
        random_seed: int = 0,
        infeasible_penalty: float = 100_000.0,
        battery_violation_penalty: float = 20_000.0,
        time_window_violation_penalty: float = 20_000.0,
        capacity_violation_penalty: float = 50_000.0,
        customer_violation_penalty: float = 80_000.0,
        route_violation_penalty: float = 10_000.0,
        other_violation_penalty: float = 5_000.0,
        route_count_penalty: float = 10.0,
    ) -> None:
        if population_size <= 0:
            raise ValueError("population_size must be positive.")
        if generations < 0:
            raise ValueError("generations cannot be negative.")
        if not 0.0 <= crossover_rate <= 1.0:
            raise ValueError("crossover_rate must be in [0, 1].")
        if not 0.0 <= mutation_rate <= 1.0:
            raise ValueError("mutation_rate must be in [0, 1].")
        if elite_size < 0:
            raise ValueError("elite_size cannot be negative.")
        if elite_size >= population_size:
            raise ValueError("elite_size must be smaller than population_size.")
        if tournament_size <= 0:
            raise ValueError("tournament_size must be positive.")

        self.population_size = population_size
        self.generations = generations
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.elite_size = elite_size
        self.tournament_size = tournament_size
        self.random_seed = random_seed

        self.infeasible_penalty = infeasible_penalty
        self.battery_violation_penalty = battery_violation_penalty
        self.time_window_violation_penalty = time_window_violation_penalty
        self.capacity_violation_penalty = capacity_violation_penalty
        self.customer_violation_penalty = customer_violation_penalty
        self.route_violation_penalty = route_violation_penalty
        self.other_violation_penalty = other_violation_penalty
        self.route_count_penalty = route_count_penalty

    def solve(self, instance) -> GAResult:
        """
        Solve one EVRP-TW instance using the enhanced GA.
        """

        start_time = time.perf_counter()
        rng = random.Random(self.random_seed)

        depot_id = _get_depot_id(instance)
        customers = _get_customer_ids(instance)

        if not customers:
            solution = Solution(routes=[])
            runtime = time.perf_counter() - start_time
            feasible, messages = _safe_check(instance, solution)

            return GAResult(
                solution=solution,
                objective=0.0,
                feasible=feasible,
                generation_count=0,
                population_size=self.population_size,
                runtime_seconds=runtime,
                best_fitness=0.0,
                feasibility_messages=messages,
            )

        population = self._initialize_population(instance, customers, depot_id, rng)

        best_chromosome: list[int] | None = None
        best_selection_key: tuple | None = None
        best_fitness = float("inf")

        for generation in range(self.generations + 1):
            evaluated = []

            for chromosome in population:
                solution = _decode_chromosome(instance, chromosome, depot_id)
                distance = _solution_distance(instance, solution)
                feasible, messages = _safe_check(instance, solution)
                summary = _summarize_messages(messages)
                fitness = self._fitness_from_components(
                    distance=distance,
                    feasible=feasible,
                    summary=summary,
                    route_count=len(solution.routes),
                )
                selection_key = _selection_key(
                    feasible=feasible,
                    summary=summary,
                    distance=distance,
                    route_count=len(solution.routes),
                )

                evaluated.append(
                    {
                        "chromosome": chromosome,
                        "fitness": fitness,
                        "selection_key": selection_key,
                    }
                )

            evaluated.sort(key=lambda item: item["fitness"])

            # Feasibility-aware best solution selection:
            # we do not blindly use the lowest scalar fitness. Instead, the
            # selected reporting solution is chosen by a lexicographic key that
            # prioritizes feasibility and lower violation counts.
            generation_best = min(evaluated, key=lambda item: item["selection_key"])

            if best_selection_key is None or generation_best["selection_key"] < best_selection_key:
                best_chromosome = generation_best["chromosome"][:]
                best_selection_key = generation_best["selection_key"]
                best_fitness = float(generation_best["fitness"])

            if generation == self.generations:
                break

            next_population: list[list[int]] = []

            # Elitism according to enhanced scalar fitness.
            for item in evaluated[: self.elite_size]:
                next_population.append(item["chromosome"][:])

            while len(next_population) < self.population_size:
                parent_a = self._tournament_select(evaluated, rng)
                parent_b = self._tournament_select(evaluated, rng)

                if rng.random() < self.crossover_rate:
                    child = _ordered_crossover(parent_a, parent_b, rng)
                else:
                    child = parent_a[:]

                if rng.random() < self.mutation_rate:
                    child = _mutate(child, rng)

                child = _repair_permutation(child, customers)
                next_population.append(child)

            population = next_population

        assert best_chromosome is not None

        best_solution = _decode_chromosome(instance, best_chromosome, depot_id)
        objective = _solution_distance(instance, best_solution)
        feasible, messages = _safe_check(instance, best_solution)
        runtime = time.perf_counter() - start_time

        return GAResult(
            solution=best_solution,
            objective=objective,
            feasible=feasible,
            generation_count=self.generations,
            population_size=self.population_size,
            runtime_seconds=runtime,
            best_fitness=best_fitness,
            feasibility_messages=messages,
        )

    def _initialize_population(
        self,
        instance,
        customers: list[int],
        depot_id: int,
        rng: random.Random,
    ) -> list[list[int]]:
        """
        Create initial population.

        Compared with the baseline, this keeps the baseline initialization and
        adds a time-window-oriented chromosome.
        """

        population: list[list[int]] = []

        # Baseline heuristic 1: nearest neighbor.
        nn_order = _nearest_neighbor_order(instance, customers, depot_id)
        population.append(nn_order)

        # Baseline heuristic 2: sorted by distance from depot.
        depot_sorted = sorted(
            customers,
            key=lambda customer_id: _distance_between(instance, depot_id, customer_id),
        )
        population.append(depot_sorted)

        # Enhanced heuristic: earlier due time first.
        due_time_sorted = sorted(
            customers,
            key=lambda customer_id: _get_due_time(instance, customer_id),
        )
        population.append(due_time_sorted)

        # Enhanced heuristic: earlier ready time first.
        ready_time_sorted = sorted(
            customers,
            key=lambda customer_id: _get_ready_time(instance, customer_id),
        )
        population.append(ready_time_sorted)

        while len(population) < self.population_size:
            chromosome = customers[:]
            rng.shuffle(chromosome)
            population.append(chromosome)

        return population[: self.population_size]

    def _fitness_from_components(
        self,
        distance: float,
        feasible: Optional[bool],
        summary: ViolationSummary,
        route_count: int,
    ) -> float:
        """
        Feasibility-aware penalty fitness.

        This is different from the baseline because it does not treat all
        checker messages equally. Battery, time-window, capacity, and customer
        violations receive explicit weights.
        """

        fitness = distance

        if feasible is False:
            fitness += self.infeasible_penalty
        elif feasible is None:
            # If checker is unavailable, keep distance-based search.
            fitness += 0.0

        fitness += summary.battery * self.battery_violation_penalty
        fitness += summary.time_window * self.time_window_violation_penalty
        fitness += summary.capacity * self.capacity_violation_penalty
        fitness += summary.customer * self.customer_violation_penalty
        fitness += summary.route * self.route_violation_penalty
        fitness += summary.other * self.other_violation_penalty
        fitness += route_count * self.route_count_penalty

        if not math.isfinite(fitness):
            return float("inf")

        return fitness

    def _tournament_select(
        self,
        evaluated_population: list[dict],
        rng: random.Random,
    ) -> list[int]:
        """
        Tournament selection using enhanced fitness.
        """

        k = min(self.tournament_size, len(evaluated_population))
        candidates = rng.sample(evaluated_population, k)
        candidates.sort(key=lambda item: item["fitness"])
        return candidates[0]["chromosome"][:]


def solve_ga_enhanced(
    instance,
    population_size: int = 40,
    generations: int = 80,
    crossover_rate: float = 0.85,
    mutation_rate: float = 0.20,
    elite_size: int = 2,
    tournament_size: int = 3,
    random_seed: int = 0,
) -> GAResult:
    """
    Functional API for enhanced GA.
    """

    solver = GAEnhanced(
        population_size=population_size,
        generations=generations,
        crossover_rate=crossover_rate,
        mutation_rate=mutation_rate,
        elite_size=elite_size,
        tournament_size=tournament_size,
        random_seed=random_seed,
    )

    return solver.solve(instance)


def solve(instance) -> Solution:
    """
    Compatibility wrapper for comparison runners.

    Returns only Solution.
    """

    return solve_ga_enhanced(instance).solution


def _summarize_messages(messages: Sequence[str]) -> ViolationSummary:
    """
    Categorize checker messages.

    This function is intentionally text-based because the current checker
    exposes violations as messages.
    """

    total = len(messages)

    battery = 0
    time_window = 0
    capacity = 0
    customer = 0
    route = 0
    other = 0

    for message in messages:
        text = str(message).lower()

        is_battery = any(
            keyword in text
            for keyword in (
                "battery",
                "energy",
                "charge",
                "charging",
                "recharge",
                "soc",
            )
        )

        is_time_window = any(
            keyword in text
            for keyword in (
                "time window",
                "time-window",
                "due",
                "ready",
                "late",
                "arrival",
                "service time",
            )
        )

        is_capacity = any(
            keyword in text
            for keyword in (
                "capacity",
                "load",
                "demand",
            )
        )

        is_customer = any(
            keyword in text
            for keyword in (
                "customer",
                "visited",
                "unserved",
                "missing",
                "duplicate",
                "once",
            )
        )

        is_route = any(
            keyword in text
            for keyword in (
                "route",
                "depot",
                "vehicle",
                "start",
                "end",
            )
        )

        if is_battery:
            battery += 1
        elif is_time_window:
            time_window += 1
        elif is_capacity:
            capacity += 1
        elif is_customer:
            customer += 1
        elif is_route:
            route += 1
        else:
            other += 1

    return ViolationSummary(
        total=total,
        battery=battery,
        time_window=time_window,
        capacity=capacity,
        customer=customer,
        route=route,
        other=other,
    )


def _selection_key(
    feasible: Optional[bool],
    summary: ViolationSummary,
    distance: float,
    route_count: int,
) -> tuple:
    """
    Feasibility-aware best solution key.

    Smaller is better.

    Priority:
        1. feasible solutions first;
        2. fewer total violations;
        3. fewer battery violations;
        4. fewer time-window violations;
        5. fewer capacity violations;
        6. fewer customer violations;
        7. shorter distance;
        8. fewer routes.
    """

    if feasible is True:
        feasible_rank = 0
    elif feasible is False:
        feasible_rank = 1
    else:
        feasible_rank = 2

    return (
        feasible_rank,
        summary.total,
        summary.battery,
        summary.time_window,
        summary.capacity,
        summary.customer,
        summary.route,
        summary.other,
        distance,
        route_count,
    )


def _get_due_time(instance, node_id: int) -> float:
    """
    Return node due_time for time-window-oriented initialization.
    """

    try:
        node = _get_node(instance, node_id)
    except Exception:
        return float("inf")

    try:
        return float(getattr(node, "due_time", float("inf")))
    except Exception:
        return float("inf")


def _get_ready_time(instance, node_id: int) -> float:
    """
    Return node ready_time for time-window-oriented initialization.
    """

    try:
        node = _get_node(instance, node_id)
    except Exception:
        return float("inf")

    try:
        return float(getattr(node, "ready_time", float("inf")))
    except Exception:
        return float("inf")
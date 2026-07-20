"""
EVRP-TW comparison.

Requirement mapping:
- POMO-style approach:
    Represented by a deterministic multi-start nearest-neighbor order generator.
    This recreates the main idea of POMO at a lightweight heuristic level:
    multiple rollouts from different starting customers and selecting the best
    decoded solution.

- GA-style approach:
    Represented by a permutation-based genetic algorithm over customer orders.
    The generated order is decoded by the shared multi-route EVRP-TW decoder.

- OR-style / UAV-Truck-inspired approach:
    Represented by an operations-research style sweep ordering heuristic.
    It clusters/customers implicitly by polar angle around the depot before
    decoding into multiple routes.

"""

from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass
from typing import Callable

from src.checker import check_solution
from src.decoders.multiroute_decoder import decode_customer_order_to_multiroute_solution
from src.distance import euclidean_distance
from src.evaluator import evaluate_solution
from src.instance import EVRPTWInstance
from src.solution import Solution


@dataclass
class BaselineRunResult:
    method: str
    feasible: bool
    checker_feasible: bool
    assigned_customers: int
    unassigned_customers: int
    route_count: int
    total_distance: float
    runtime_seconds: float
    decoder_message: str


def get_customer_ids(instance: EVRPTWInstance) -> list[int]:
    return [node.id for node in instance.nodes if node.node_type == "customer"]


def _node_by_id(instance: EVRPTWInstance):
    return {node.id: node for node in instance.nodes}


def nearest_neighbor_order(instance: EVRPTWInstance, start_customer_id: int | None = None) -> list[int]:
    """
    Greedy nearest-neighbor customer ordering.
    """
    node_by_id = _node_by_id(instance)
    unvisited = set(get_customer_ids(instance))
    order: list[int] = []

    if not unvisited:
        return order

    if start_customer_id is not None and start_customer_id in unvisited:
        current_id = start_customer_id
        order.append(current_id)
        unvisited.remove(current_id)
    else:
        current_id = instance.depot_id

    while unvisited:
        current_node = node_by_id[current_id]
        next_id = min(
            unvisited,
            key=lambda cid: euclidean_distance(current_node, node_by_id[cid]),
        )
        order.append(next_id)
        unvisited.remove(next_id)
        current_id = next_id

    return order


def pomo_style_order(instance: EVRPTWInstance, rollout_limit: int = 16) -> list[int]:
    """
    Lightweight POMO-style multi-start constructive baseline.

    Original POMO evaluates multiple starting actions in parallel. Here we
    recreate that idea by generating multiple nearest-neighbor rollouts from
    different starting customers and selecting the decoded solution with the
    best lexicographic score:
        1. fewer unassigned customers
        2. feasible checker result
        3. shorter total distance
    """
    customer_ids = get_customer_ids(instance)

    if not customer_ids:
        return []

    starts = customer_ids[: min(rollout_limit, len(customer_ids))]
    best_order = nearest_neighbor_order(instance, starts[0])
    best_score = None

    for start in starts:
        order = nearest_neighbor_order(instance, start)
        solution, report = decode_customer_order_to_multiroute_solution(
            instance,
            order,
            allow_partial=True,
        )
        check = check_solution(instance, solution)
        evaluation = evaluate_solution(instance, solution)

        score = (
            len(report.unassigned_customers),
            0 if check.feasible else 1,
            evaluation.total_distance,
        )

        if best_score is None or score < best_score:
            best_score = score
            best_order = order

    return best_order


def ga_style_order(
    instance: EVRPTWInstance,
    seed: int = 0,
    population_size: int = 24,
    generations: int = 30,
    mutation_rate: float = 0.20,
) -> list[int]:
    """
    Permutation-based GA baseline over customer orders.

    Chromosome:
        A permutation of customer IDs.

    Fitness:
        Decoded multi-route solution score based on:
        - unassigned customer penalty
        - checker infeasibility penalty
        - total travel distance

    This implements EVRP-TW constraints through the shared decoder/checker.
    """
    rng = random.Random(seed)
    customers = get_customer_ids(instance)

    if len(customers) <= 1:
        return customers[:]

    def initial_individual() -> list[int]:
        individual = customers[:]
        rng.shuffle(individual)
        return individual

    def fitness(order: list[int]) -> float:
        solution, report = decode_customer_order_to_multiroute_solution(
            instance,
            order,
            allow_partial=True,
        )
        check = check_solution(instance, solution)
        evaluation = evaluate_solution(instance, solution)

        penalty = 0.0
        penalty += len(report.unassigned_customers) * 1_000_000.0
        if not check.feasible:
            penalty += 500_000.0

        return penalty + evaluation.total_distance

    def tournament_select(population: list[list[int]], scores: list[float], k: int = 3) -> list[int]:
        candidates = rng.sample(range(len(population)), k=min(k, len(population)))
        best_idx = min(candidates, key=lambda idx: scores[idx])
        return population[best_idx][:]

    def ordered_crossover(parent_a: list[int], parent_b: list[int]) -> list[int]:
        n = len(parent_a)

        if n < 3:
            child = parent_a[:]
            return child

        left, right = sorted(rng.sample(range(n), 2))
        child: list[int | None] = [None] * n
        child[left:right + 1] = parent_a[left:right + 1]

        fill_values = [gene for gene in parent_b if gene not in child]
        fill_idx = 0

        for idx in range(n):
            if child[idx] is None:
                child[idx] = fill_values[fill_idx]
                fill_idx += 1

        return [int(gene) for gene in child]

    def mutate(order: list[int]) -> None:
        if rng.random() < mutation_rate and len(order) >= 2:
            i, j = rng.sample(range(len(order)), 2)
            order[i], order[j] = order[j], order[i]

        if rng.random() < mutation_rate and len(order) >= 3:
            i, j = sorted(rng.sample(range(len(order)), 2))
            order[i:j + 1] = reversed(order[i:j + 1])

    population = [initial_individual() for _ in range(population_size)]

    # Add a strong constructive individual.
    population[0] = nearest_neighbor_order(instance)

    best = population[0][:]
    best_score = fitness(best)

    for _generation in range(generations):
        scores = [fitness(individual) for individual in population]

        generation_best_idx = min(range(len(population)), key=lambda idx: scores[idx])
        if scores[generation_best_idx] < best_score:
            best_score = scores[generation_best_idx]
            best = population[generation_best_idx][:]

        new_population: list[list[int]] = [best[:]]

        while len(new_population) < population_size:
            parent_a = tournament_select(population, scores)
            parent_b = tournament_select(population, scores)
            child = ordered_crossover(parent_a, parent_b)
            mutate(child)
            new_population.append(child)

        population = new_population

    return best


def or_sweep_order(instance: EVRPTWInstance) -> list[int]:
    """
    OR-style sweep heuristic.

    Customers are sorted by polar angle around the depot, then by radial
    distance. Sweep heuristics are common constructive VRP baselines and are
    useful as a lightweight OR-style comparison method.
    """
    node_by_id = _node_by_id(instance)
    depot = node_by_id[instance.depot_id]

    def key(customer_id: int):
        customer = node_by_id[customer_id]
        angle = math.atan2(customer.y - depot.y, customer.x - depot.x)
        radius = euclidean_distance(depot, customer)
        return angle, radius

    return sorted(get_customer_ids(instance), key=key)


def random_order(instance: EVRPTWInstance, seed: int = 0) -> list[int]:
    rng = random.Random(seed)
    order = get_customer_ids(instance)
    rng.shuffle(order)
    return order


def run_order_based_baseline(
    instance: EVRPTWInstance,
    method_name: str,
    order_builder: Callable[[], list[int]],
) -> tuple[Solution, BaselineRunResult]:
    """
    Build order -> decode to multi-route solution -> check/evaluate.
    """
    start_time = time.perf_counter()

    order = order_builder()
    solution, report = decode_customer_order_to_multiroute_solution(
        instance,
        order,
        allow_partial=True,
    )
    check = check_solution(instance, solution)
    evaluation = evaluate_solution(instance, solution)

    runtime = time.perf_counter() - start_time

    result = BaselineRunResult(
        method=method_name,
        feasible=report.success and check.feasible and len(report.unassigned_customers) == 0,
        checker_feasible=check.feasible,
        assigned_customers=len(report.assigned_customers),
        unassigned_customers=len(report.unassigned_customers),
        route_count=report.route_count,
        total_distance=evaluation.total_distance,
        runtime_seconds=runtime,
        decoder_message=report.message,
    )

    return solution, result
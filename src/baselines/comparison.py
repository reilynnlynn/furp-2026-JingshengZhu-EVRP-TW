"""

The comparison output includes:
- method name
- total distance
- number of routes / vehicles used
- number of charging station visits
- feasibility status
- number of feasibility violations
- runtime

"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Iterable

from src.checker import check_solution
from src.distance import euclidean_distance
from src.solution import Solution


@dataclass(frozen=True)
class BaselineResult:
    """
    Result of running one baseline method on one EVRP-TW instance.
    """

    method: str
    total_distance: float
    vehicle_count: int
    charging_visits: int
    feasible: bool
    violation_count: int
    runtime_seconds: float
    routes: list[list[int]]
    messages: list[str]


@dataclass(frozen=True)
class BaselineMethod:
    """
    A named baseline method.

    The solver must be a callable:

        solver(instance) -> Solution
    """

    name: str
    solver: Callable[[object], Solution]


def calculate_route_distance(instance: object, node_ids: list[int]) -> float:
    """
    Calculate the total travel distance of one route.
    """

    if len(node_ids) < 2:
        return 0.0

    total = 0.0

    for from_id, to_id in zip(node_ids[:-1], node_ids[1:]):
        from_node = instance.get_node(from_id)
        to_node = instance.get_node(to_id)
        total += euclidean_distance(from_node, to_node)

    return total


def calculate_solution_distance(instance: object, solution: Solution) -> float:
    """
    Calculate total distance over all routes in a solution.
    """

    return sum(
        calculate_route_distance(instance, route.node_ids)
        for route in solution.routes
    )


def count_charging_visits(instance: object, solution: Solution) -> int:
    """
    Count how many charging station visits appear in a solution.

    Depot and customer nodes are not counted. Only nodes with node_type == "station"
    are counted.
    """

    charging_visits = 0

    for route in solution.routes:
        for node_id in route.node_ids:
            node = instance.get_node(node_id)
            if getattr(node, "node_type", None) == "station":
                charging_visits += 1

    return charging_visits


def extract_routes(solution: Solution) -> list[list[int]]:
    """
    Convert a Solution object into plain list-of-list route representation.
    """

    return [list(route.node_ids) for route in solution.routes]


def evaluate_baseline(
    instance: object,
    method: BaselineMethod,
    *,
    round_digits: int = 4,
) -> BaselineResult:
    """
    Run and evaluate a single baseline method.
    """

    start_time = time.perf_counter()
    solution = method.solver(instance)
    runtime_seconds = time.perf_counter() - start_time

    check_result = check_solution(instance, solution)

    total_distance = calculate_solution_distance(instance, solution)
    charging_visits = count_charging_visits(instance, solution)

    return BaselineResult(
        method=method.name,
        total_distance=round(total_distance, round_digits),
        vehicle_count=len(solution.routes),
        charging_visits=charging_visits,
        feasible=check_result.feasible,
        violation_count=len(check_result.messages),
        runtime_seconds=round(runtime_seconds, 6),
        routes=extract_routes(solution),
        messages=list(check_result.messages),
    )


def compare_baselines(
    instance: object,
    methods: Iterable[BaselineMethod],
) -> list[BaselineResult]:
    """
    Run multiple baseline methods on the same instance.
    """

    results: list[BaselineResult] = []

    for method in methods:
        result = evaluate_baseline(instance, method)
        results.append(result)

    return results


def results_to_markdown(results: list[BaselineResult]) -> str:
    """
    Convert comparison results to a Markdown table.

    This is useful for weekly reports and final report.
    """

    lines = [
        "| Method | Total Distance | Vehicles | Charging Visits | Feasible | Violations | Runtime (s) |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]

    for result in results:
        lines.append(
            "| "
            f"{result.method} | "
            f"{result.total_distance:.4f} | "
            f"{result.vehicle_count} | "
            f"{result.charging_visits} | "
            f"{result.feasible} | "
            f"{result.violation_count} | "
            f"{result.runtime_seconds:.6f} |"
        )

    return "\n".join(lines)


def results_to_csv(results: list[BaselineResult]) -> str:
    """
    Convert comparison results to CSV text.
    """

    lines = [
        "method,total_distance,vehicle_count,charging_visits,feasible,violation_count,runtime_seconds"
    ]

    for result in results:
        lines.append(
            ",".join(
                [
                    result.method,
                    f"{result.total_distance:.4f}",
                    str(result.vehicle_count),
                    str(result.charging_visits),
                    str(result.feasible),
                    str(result.violation_count),
                    f"{result.runtime_seconds:.6f}",
                ]
            )
        )

    return "\n".join(lines)
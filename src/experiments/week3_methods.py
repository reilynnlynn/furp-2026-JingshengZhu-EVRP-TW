"""
This module standardizes algorithm outputs for Week 3 experiments.

Currently supported method: ga_baseline
"""

from __future__ import annotations

from dataclasses import dataclass
import importlib
import time
from typing import Any, Callable


@dataclass(frozen=True)
class MethodRunResult:
    """
    Standard output format for Week 3 experimental methods.

    Attributes:
        method_name:
            Standard method name.
        routes:
            Routes represented as lists of node ids.

            The evaluator expects route format like:

                [[1, 5, 8], [2, 3], [4, 6, 7]]

            The depot is removed by default because the Week 3 evaluator assumes
            depot -> route -> depot internally.
        runtime_seconds:
            Wall-clock runtime in seconds.
        raw_objective:
            Objective reported by the original method, if available.
        raw_feasible:
            Feasibility reported by the original method/checker, if available.
        raw_messages:
            Messages reported by the original method/checker.
        metadata:
            Extra method-specific information.
        raw_result:
            Original solver result object for debugging.
    """

    method_name: str
    routes: list[list[int]]
    runtime_seconds: float
    raw_objective: float | None
    raw_feasible: bool | None
    raw_messages: list[str]
    metadata: dict[str, Any]
    raw_result: Any | None = None


def get_depot_id(instance: Any) -> int:
    """
    Return the depot id from an instance object.

    Your project uses EVRPTWInstance with depot_id, but this helper is defensive
    so the experiment code stays stable if the instance implementation changes.
    """

    if hasattr(instance, "depot_id"):
        return int(getattr(instance, "depot_id"))

    if hasattr(instance, "depot"):
        depot = getattr(instance, "depot")
        if isinstance(depot, int):
            return int(depot)
        if hasattr(depot, "id"):
            return int(depot.id)

    nodes = getattr(instance, "nodes", None)

    if nodes is not None:
        if isinstance(nodes, dict):
            iterable_nodes = nodes.values()
        else:
            iterable_nodes = nodes

        for node in iterable_nodes:
            node_type = str(
                getattr(node, "node_type", getattr(node, "type", ""))
            ).lower()

            if node_type == "depot":
                if hasattr(node, "id"):
                    return int(node.id)

    return 0


def solution_to_routes(
    solution: Any,
    depot_id: int | None = None,
    remove_depot: bool = True,
) -> list[list[int]]:
    """
    Convert a project Solution object to simple route lists.

    Your GA baseline normally returns a Solution object containing Route objects:

        Solution(routes=[Route(node_ids=[0, 1, 2, 0]), ...])

    Week 3 evaluation code uses a cleaner representation:

        [[1, 2], ...]

    Therefore this function removes depot markers by default.
    """

    if solution is None:
        return []

    raw_routes = getattr(solution, "routes", None)

    if raw_routes is None:
        if isinstance(solution, list):
            raw_routes = solution
        else:
            raise ValueError("Solution object does not have a 'routes' attribute.")

    converted_routes: list[list[int]] = []

    for route in raw_routes:
        if hasattr(route, "node_ids"):
            node_ids = list(route.node_ids)
        elif isinstance(route, list):
            node_ids = list(route)
        elif isinstance(route, tuple):
            node_ids = list(route)
        else:
            raise ValueError(
                "Each route must either have 'node_ids' or be a list/tuple."
            )

        cleaned_route: list[int] = []

        for node_id in node_ids:
            node_id_int = int(node_id)

            if remove_depot and depot_id is not None and node_id_int == depot_id:
                continue

            cleaned_route.append(node_id_int)

        if cleaned_route:
            converted_routes.append(cleaned_route)

    return converted_routes


def _import_first_available_module(module_names: list[str]) -> Any:
    """
    Import the first available module from a list of candidate module names.
    """

    errors: list[str] = []

    for module_name in module_names:
        try:
            return importlib.import_module(module_name)
        except Exception as exc:
            errors.append(f"{module_name}: {exc}")

    error_message = "\n".join(errors)

    raise ImportError(
        "Could not import GA baseline module from any known path.\n"
        "Tried:\n"
        f"{error_message}\n\n"
        "Expected location for this project: src.baselines.ga_baseline"
    )


BASELINE_GA_MODULE_CANDIDATES = [
    "src.baselines.ga_baseline",
]


def load_baseline_ga_solver() -> Callable[..., Any]:
    """
    Load the baseline GA solver function from src.baselines.ga_baseline.

    Expected function name:

        solve_ga(instance, ..., random_seed=seed)
    """

    module = _import_first_available_module(BASELINE_GA_MODULE_CANDIDATES)

    if hasattr(module, "solve_ga"):
        return getattr(module, "solve_ga")

    raise AttributeError(
        "src.baselines.ga_baseline was imported, but no solve_ga function was "
        "found. Please check that your GA baseline exposes solve_ga(...)."
    )


def run_baseline_ga(
    instance: Any,
    seed: int,
    population_size: int = 40,
    generations: int = 80,
    crossover_rate: float = 0.85,
    mutation_rate: float = 0.20,
    elite_size: int = 2,
    tournament_size: int = 3,
    remove_depot: bool = True,
) -> MethodRunResult:
    """
    Run the existing baseline GA and convert its result to Week 3 format.

    This function does not change the GA itself. It only standardizes the output
    so that the experiment runner can evaluate all methods in the same way.
    """

    solver = load_baseline_ga_solver()
    depot_id = get_depot_id(instance)

    start_time = time.perf_counter()

    raw_result = solver(
        instance,
        population_size=population_size,
        generations=generations,
        crossover_rate=crossover_rate,
        mutation_rate=mutation_rate,
        elite_size=elite_size,
        tournament_size=tournament_size,
        random_seed=seed,
    )

    measured_runtime = time.perf_counter() - start_time

    solution = getattr(raw_result, "solution", raw_result)

    routes = solution_to_routes(
        solution=solution,
        depot_id=depot_id,
        remove_depot=remove_depot,
    )

    runtime_seconds = getattr(raw_result, "runtime_seconds", measured_runtime)
    runtime_seconds = float(runtime_seconds)

    raw_objective = getattr(raw_result, "objective", None)
    if raw_objective is not None:
        raw_objective = float(raw_objective)

    raw_feasible = getattr(raw_result, "feasible", None)

    raw_messages = getattr(raw_result, "feasibility_messages", [])
    if raw_messages is None:
        raw_messages = []

    metadata = {
        "seed": seed,
        "population_size": getattr(raw_result, "population_size", population_size),
        "generations": getattr(raw_result, "generation_count", generations),
        "crossover_rate": crossover_rate,
        "mutation_rate": mutation_rate,
        "elite_size": elite_size,
        "tournament_size": tournament_size,
        "best_fitness": getattr(raw_result, "best_fitness", None),
        "adapter": "week3_baseline_ga_adapter",
        "source_module": "src.baselines.ga_baseline",
    }

    return MethodRunResult(
        method_name="ga_baseline",
        routes=routes,
        runtime_seconds=runtime_seconds,
        raw_objective=raw_objective,
        raw_feasible=raw_feasible,
        raw_messages=list(raw_messages),
        metadata=metadata,
        raw_result=raw_result,
    )


def run_week3_method(
    instance: Any,
    method_name: str,
    seed: int,
    **kwargs: Any,
) -> MethodRunResult:
    """
    Unified method entry point for Week 3 experiments.

    Currently supported names:

        - ga_baseline
        - baseline_ga
        - baseline
        - existing_ga

    Later we can extend this function to support ga_enhanced and ablation
    variants without changing the experiment runner.
    """

    normalized_name = method_name.strip().lower()

    if normalized_name in {
        "ga_baseline",
        "baseline_ga",
        "baseline",
        "existing_ga",
    }:
        return run_baseline_ga(
            instance=instance,
            seed=seed,
            **kwargs,
        )

    raise ValueError(
        f"Unknown Week 3 method: {method_name}. "
        "Currently supported methods: ga_baseline."
    )
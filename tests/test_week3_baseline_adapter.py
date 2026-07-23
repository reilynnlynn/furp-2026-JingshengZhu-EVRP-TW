from __future__ import annotations

from src.experiments.week3_methods import (
    MethodRunResult,
    run_baseline_ga,
    run_week3_method,
    solution_to_routes,
)
from src.evaluation.week3_metrics import evaluate_solution
from src.generator import generate_random_evrptw_instance
from src.solution import Route, Solution


def make_adapter_test_instance():
    return generate_random_evrptw_instance(
        name="test_week3_baseline_adapter",
        num_customers=6,
        num_stations=2,
        vehicle_count=3,
        vehicle_capacity=100.0,
        battery_capacity=500.0,
        energy_consumption_rate=1.0,
        charging_rate=1.0,
        coordinate_limit=30.0,
        demand_min=1.0,
        demand_max=10.0,
        time_window_start_min=0.0,
        time_window_start_max=20.0,
        time_window_width_min=300.0,
        time_window_width_max=500.0,
        service_time_min=0.0,
        service_time_max=2.0,
        seed=2026,
    )


def test_solution_to_routes_removes_depot_markers() -> None:
    solution = Solution(
        routes=[
            Route(node_ids=[0, 1, 2, 0]),
            Route(node_ids=[0, 3, 4, 0]),
        ]
    )

    routes = solution_to_routes(
        solution=solution,
        depot_id=0,
        remove_depot=True,
    )

    assert routes == [
        [1, 2],
        [3, 4],
    ]


def test_solution_to_routes_can_keep_depot_markers() -> None:
    solution = Solution(
        routes=[
            Route(node_ids=[0, 1, 2, 0]),
        ]
    )

    routes = solution_to_routes(
        solution=solution,
        depot_id=0,
        remove_depot=False,
    )

    assert routes == [
        [0, 1, 2, 0],
    ]


def test_run_baseline_ga_returns_standard_result() -> None:
    instance = make_adapter_test_instance()

    result = run_baseline_ga(
        instance=instance,
        seed=11,
        population_size=10,
        generations=5,
        crossover_rate=0.85,
        mutation_rate=0.20,
        elite_size=1,
        tournament_size=2,
    )

    assert isinstance(result, MethodRunResult)
    assert result.method_name == "ga_baseline"
    assert isinstance(result.routes, list)
    assert result.runtime_seconds >= 0.0
    assert result.metadata["seed"] == 11
    assert result.metadata["population_size"] == 10
    assert result.metadata["generations"] == 5
    assert result.metadata["source_module"] == "src.baselines.ga_baseline"

    customer_ids = {customer.id for customer in instance.customers}
    visited_customer_ids = {
        node_id
        for route in result.routes
        for node_id in route
        if node_id in customer_ids
    }

    assert visited_customer_ids == customer_ids


def test_run_week3_method_dispatches_baseline_ga() -> None:
    instance = make_adapter_test_instance()

    result = run_week3_method(
        instance=instance,
        method_name="ga_baseline",
        seed=12,
        population_size=10,
        generations=5,
        elite_size=1,
        tournament_size=2,
    )

    assert result.method_name == "ga_baseline"
    assert result.metadata["seed"] == 12


def test_baseline_adapter_output_can_be_evaluated_by_week3_metrics() -> None:
    instance = make_adapter_test_instance()

    method_result = run_baseline_ga(
        instance=instance,
        seed=13,
        population_size=10,
        generations=5,
        elite_size=1,
        tournament_size=2,
    )

    evaluation = evaluate_solution(
        instance=instance,
        routes=method_result.routes,
        method_name=method_result.method_name,
        run_seed=13,
        runtime_seconds=method_result.runtime_seconds,
    )

    assert evaluation.instance_name == "test_week3_baseline_adapter"
    assert evaluation.method_name == "ga_baseline"
    assert evaluation.run_seed == 13
    assert evaluation.runtime_seconds >= 0.0
    assert evaluation.total_distance >= 0.0

    assert evaluation.violations.total >= 0
    assert isinstance(evaluation.notes, list)
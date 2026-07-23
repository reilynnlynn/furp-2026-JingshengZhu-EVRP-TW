from __future__ import annotations

from src.evaluation.week3_metrics import (
    count_customer_coverage,
    evaluate_solution,
    flatten_evaluation_for_csv,
)
from src.generator import generate_random_evrptw_instance


def make_small_test_instance():
    return generate_random_evrptw_instance(
        name="test_eval_instance",
        num_customers=3,
        num_stations=1,
        vehicle_count=2,
        vehicle_capacity=100.0,
        battery_capacity=500.0,
        energy_consumption_rate=1.0,
        charging_rate=1.0,
        coordinate_limit=20.0,
        demand_min=1.0,
        demand_max=5.0,
        time_window_start_min=0.0,
        time_window_start_max=10.0,
        time_window_width_min=500.0,
        time_window_width_max=600.0,
        service_time_min=0.0,
        service_time_max=1.0,
        seed=123,
    )


def test_count_customer_coverage_detects_missing_and_duplicate() -> None:
    instance = make_small_test_instance()

    customer_ids = [customer.id for customer in instance.customers]
    routes = [
        [customer_ids[0], customer_ids[1]],
        [customer_ids[1]],
    ]

    duplicate_customers, missing_customers = count_customer_coverage(
        instance=instance,
        routes=routes,
    )

    assert duplicate_customers == 1
    assert missing_customers == 1


def test_evaluate_solution_feasible_simple_case() -> None:
    instance = make_small_test_instance()
    customer_ids = [customer.id for customer in instance.customers]

    routes = [
        [customer_ids[0], customer_ids[1]],
        [customer_ids[2]],
    ]

    evaluation = evaluate_solution(
        instance=instance,
        routes=routes,
        method_name="test_method",
        run_seed=7,
        runtime_seconds=0.5,
    )

    assert evaluation.instance_name == "test_eval_instance"
    assert evaluation.method_name == "test_method"
    assert evaluation.run_seed == 7
    assert evaluation.runtime_seconds == 0.5
    assert evaluation.feasible is True
    assert evaluation.violations.total == 0
    assert evaluation.vehicles_used == 2
    assert evaluation.total_distance > 0.0
    assert evaluation.objective_value == evaluation.total_distance


def test_evaluate_solution_detects_missing_customer() -> None:
    instance = make_small_test_instance()
    customer_ids = [customer.id for customer in instance.customers]

    routes = [
        [customer_ids[0]],
    ]

    evaluation = evaluate_solution(
        instance=instance,
        routes=routes,
        method_name="test_method",
    )

    assert evaluation.feasible is False
    assert evaluation.violations.missing_customers == 2
    assert evaluation.violations.total >= 2
    assert evaluation.objective_value > evaluation.total_distance


def test_evaluate_solution_detects_vehicle_count_violation() -> None:
    instance = make_small_test_instance()
    customer_ids = [customer.id for customer in instance.customers]

    routes = [
        [customer_ids[0]],
        [customer_ids[1]],
        [customer_ids[2]],
    ]

    evaluation = evaluate_solution(
        instance=instance,
        routes=routes,
        method_name="test_method",
    )

    assert evaluation.feasible is False
    assert evaluation.violations.vehicle_count_violation == 1


def test_flatten_evaluation_for_csv_contains_required_week3_fields() -> None:
    instance = make_small_test_instance()
    customer_ids = [customer.id for customer in instance.customers]

    routes = [
        [customer_ids[0], customer_ids[1]],
        [customer_ids[2]],
    ]

    evaluation = evaluate_solution(
        instance=instance,
        routes=routes,
        method_name="test_method",
        run_seed=10,
        runtime_seconds=1.25,
    )

    row = flatten_evaluation_for_csv(evaluation)

    required_fields = {
        "instance_name",
        "method_name",
        "run_seed",
        "num_customers",
        "vehicles_used",
        "feasible",
        "objective_value",
        "total_distance",
        "runtime_seconds",
        "total_violations",
        "capacity_violations",
        "battery_violations",
        "time_window_violations",
        "notes",
    }

    assert required_fields.issubset(set(row.keys()))
    assert row["method_name"] == "test_method"
    assert row["run_seed"] == 10
    assert row["runtime_seconds"] == 1.25
from src.checker import check_solution
from src.generator import generate_random_evrptw_instance
from src.solution import Route, Solution


def test_simple_generated_solution_is_feasible_for_basic_checks():
    instance = generate_random_evrptw_instance(
        name="checker_test",
        num_customers=3,
        num_stations=1,
        vehicle_count=3,
        vehicle_capacity=100.0,
        battery_capacity=10000.0,
        energy_consumption_rate=1.0,
        seed=42,
    )

    solution = Solution(
        routes=[
            Route([0, 1, 0]),
            Route([0, 2, 0]),
            Route([0, 3, 0]),
        ]
    )

    result = check_solution(instance, solution)

    assert result.feasible, result.messages


def test_duplicate_customer_is_infeasible():
    instance = generate_random_evrptw_instance(
        name="checker_test_duplicate",
        num_customers=3,
        num_stations=1,
        vehicle_count=3,
        vehicle_capacity=100.0,
        battery_capacity=10000.0,
        energy_consumption_rate=1.0,
        seed=42,
    )

    solution = Solution(
        routes=[
            Route([0, 1, 0]),
            Route([0, 1, 2, 3, 0]),
        ]
    )

    result = check_solution(instance, solution)

    assert not result.feasible
    assert any("Duplicated customer" in message for message in result.messages)


def test_missing_customer_is_infeasible():
    instance = generate_random_evrptw_instance(
        name="checker_test_missing",
        num_customers=3,
        num_stations=1,
        vehicle_count=3,
        vehicle_capacity=100.0,
        battery_capacity=10000.0,
        energy_consumption_rate=1.0,
        seed=42,
    )

    solution = Solution(
        routes=[
            Route([0, 1, 0]),
            Route([0, 2, 0]),
        ]
    )

    result = check_solution(instance, solution)

    assert not result.feasible
    assert any("Customer visit mismatch" in message for message in result.messages)


def test_route_without_return_to_depot_is_infeasible():
    instance = generate_random_evrptw_instance(
        name="checker_test_depot",
        num_customers=1,
        num_stations=1,
        vehicle_count=1,
        vehicle_capacity=100.0,
        battery_capacity=10000.0,
        energy_consumption_rate=1.0,
        seed=42,
    )

    solution = Solution(
        routes=[
            Route([0, 1]),
        ]
    )

    result = check_solution(instance, solution)

    assert not result.feasible
    assert any("does not end at depot" in message for message in result.messages)
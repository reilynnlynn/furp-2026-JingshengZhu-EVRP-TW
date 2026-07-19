from src.evaluator import (
    calculate_total_distance,
    count_charging_visits,
    evaluate_solution,
)
from src.generator import generate_random_evrptw_instance
from src.solution import Route, Solution


def test_calculate_total_distance_positive():
    instance = generate_random_evrptw_instance(
        num_customers=3,
        num_stations=1,
        seed=1,
    )

    solution = Solution(
        routes=[
            Route(node_ids=[0, 1, 2, 3, 0])
        ]
    )

    total_distance = calculate_total_distance(instance, solution)

    assert total_distance > 0


def test_count_charging_visits():
    instance = generate_random_evrptw_instance(
        num_customers=3,
        num_stations=1,
        seed=1,
    )

    station_id = instance.stations[0].id

    solution = Solution(
        routes=[
            Route(node_ids=[0, 1, station_id, 2, 3, 0])
        ]
    )

    charging_count = count_charging_visits(instance, solution)

    assert charging_count == 1


def test_evaluate_solution_returns_required_fields():
    instance = generate_random_evrptw_instance(
        num_customers=3,
        num_stations=1,
        seed=1,
    )

    solution = Solution(
        routes=[
            Route(node_ids=[0, 1, 0]),
            Route(node_ids=[0, 2, 0]),
            Route(node_ids=[0, 3, 0]),
        ]
    )

    result = evaluate_solution(instance, solution)

    assert result.total_distance >= 0
    assert result.vehicle_count == 3
    assert result.charging_count == 0
    assert isinstance(result.feasible, bool)
    assert result.objective >= result.total_distance
    assert result.num_violations == len(result.messages)
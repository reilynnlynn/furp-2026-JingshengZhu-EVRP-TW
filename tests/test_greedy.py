from src.checker import check_solution
from src.generator import generate_random_evrptw_instance
from src.greedy import build_greedy_solution


def test_build_greedy_solution_returns_solution():
    instance = generate_random_evrptw_instance(
        num_customers=5,
        num_stations=2,
        seed=42,
    )

    solution = build_greedy_solution(instance)

    assert len(solution.routes) == 5


def test_greedy_solution_has_valid_route_structure():
    instance = generate_random_evrptw_instance(
        num_customers=5,
        num_stations=2,
        seed=42,
    )

    solution = build_greedy_solution(instance)

    result = check_solution(instance, solution)

    assert isinstance(result.feasible, bool)
    assert len(solution.routes) > 0
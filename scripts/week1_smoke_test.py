import time

from src.evaluator import evaluate_solution
from src.generator import generate_random_evrptw_instance
from src.solution import Route, Solution


def main():
    start_time = time.perf_counter()

    instance = generate_random_evrptw_instance(
        num_customers=3,
        num_stations=1,
        seed=42222,
    )

    solution = Solution(
        routes=[
            Route(node_ids=[0, 1, 0]),
            Route(node_ids=[0, 2, 0]),
            Route(node_ids=[0, 3, 0]),
        ]
    )

    result = evaluate_solution(instance, solution)

    runtime = time.perf_counter() - start_time

    print("Week 1 Smoke Test")
    print("=================")
    print(f"Instance name: {instance.name}")
    print("Instance size: 3 customers, 1 charging station")
    print("Command: python scripts/week1_smoke_test.py")
    print(f"Objective value: {result.objective:.4f}")
    print(f"Total distance: {result.total_distance:.4f}")
    print(f"Feasible: {result.feasible}")
    print(f"Runtime (s): {runtime:.6f}")
    print(f"Vehicles used: {result.vehicle_count}")
    print(f"Charging visits: {result.charging_count}")
    print("Routes:")

    for route_index, route in enumerate(solution.routes):
        print(f"  Route {route_index}: {route.node_ids}")

    if result.messages:
        print("Constraint messages:")
        for message in result.messages:
            print(f"  - {message}")
    else:
        print("Constraint messages: none")


if __name__ == "__main__":
    main()
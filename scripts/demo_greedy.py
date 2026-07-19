from src.evaluator import evaluate_solution
from src.generator import generate_random_evrptw_instance
from src.greedy import build_greedy_solution


def main():
    instance = generate_random_evrptw_instance(
        num_customers=5,
        num_stations=2,
        seed=42,
    )

    solution = build_greedy_solution(instance)
    result = evaluate_solution(instance, solution)

    print("Greedy Baseline Demo")
    print("====================")
    print(f"Instance: {instance.name}")
    print(f"Routes: {len(solution.routes)}")
    print(f"Total distance: {result.total_distance:.4f}")
    print(f"Feasible: {result.feasible}")
    print(f"Objective: {result.objective:.4f}")
    print("Routes:")
    for i, route in enumerate(solution.routes):
        print(f"  Route {i}: {route.node_ids}")


if __name__ == "__main__":
    main()
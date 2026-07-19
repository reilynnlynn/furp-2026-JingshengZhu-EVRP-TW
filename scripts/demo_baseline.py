from src.baselines import run_baseline
from src.generator import generate_random_evrptw_instance


def print_solution_routes(solution) -> None:
    """
    Print routes in a readable format.

    This helper is intentionally kept flexible because the exact Route/Solution
    implementation may evolve during the project.
    """

    print("\nRoutes:")

    for route_index, route in enumerate(solution.routes, start=1):
        if hasattr(route, "node_ids"):
            node_sequence = route.node_ids
        elif hasattr(route, "nodes"):
            node_sequence = route.nodes
        else:
            node_sequence = route

        print(f"  Route {route_index}: {node_sequence}")


def print_evaluation_summary(evaluation) -> None:
    """
    Print evaluation result in a robust way.

    This function supports both dataclass-style evaluation objects and
    dictionary-style evaluation results.
    """

    print("\nEvaluation:")

    if hasattr(evaluation, "__dict__"):
        for key, value in evaluation.__dict__.items():
            print(f"  {key}: {value}")
    elif isinstance(evaluation, dict):
        for key, value in evaluation.items():
            print(f"  {key}: {value}")
    else:
        print(f"  {evaluation}")


def main() -> None:
    """
    Generate an EVRP-TW instance and run the greedy baseline.
    """

    instance = generate_random_evrptw_instance(
        name="week2_demo_instance",
        num_customers=10,
        num_stations=3,
        vehicle_count=5,
        vehicle_capacity=100.0,
        battery_capacity=120.0,
        energy_consumption_rate=1.0,
        charging_rate=1.0,
        seed=42,
    )

    result = run_baseline("greedy", instance)

    print("=" * 70)
    print("Week 2 Baseline Demo")
    print("=" * 70)

    print(f"Instance name: {instance.name}")
    print(f"Number of customers: {len(instance.customers)}")
    print(f"Number of charging stations: {len(instance.stations)}")
    print(f"Vehicle count: {instance.vehicle_count}")

    print("\nBaseline:")
    print(f"  Method: {result.method_name}")
    print(f"  Runtime seconds: {result.runtime_seconds:.6f}")

    print_evaluation_summary(result.evaluation)
    print_solution_routes(result.solution)

    print("\nMetadata:")
    for key, value in result.metadata.items():
        print(f"  {key}: {value}")

    print("=" * 70)


if __name__ == "__main__":
    main()
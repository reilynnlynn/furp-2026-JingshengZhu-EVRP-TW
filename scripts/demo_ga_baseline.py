from dataclasses import dataclass

from src.baselines.ga_baseline import solve_ga


@dataclass
class DemoNode:
    id: int
    x: float
    y: float
    demand: float = 0.0
    type: str = "customer"


@dataclass
class DemoInstance:
    nodes: list[DemoNode]
    depot_id: int = 0
    vehicle_capacity: float = 10.0
    vehicle_speed: float = 1.0
    battery_range: float = 8.0


def make_demo_instance() -> DemoInstance:
    nodes = [
        DemoNode(id=0, x=0.0, y=0.0, demand=0.0, type="depot"),
        DemoNode(id=1, x=1.0, y=1.0, demand=1.0, type="customer"),
        DemoNode(id=2, x=2.0, y=1.0, demand=1.0, type="customer"),
        DemoNode(id=3, x=1.0, y=3.0, demand=1.0, type="customer"),
        DemoNode(id=4, x=4.0, y=3.0, demand=1.0, type="customer"),
        DemoNode(id=5, x=5.0, y=2.0, demand=1.0, type="customer"),
        DemoNode(id=6, x=3.0, y=5.0, demand=1.0, type="customer"),
        DemoNode(id=100, x=2.5, y=2.5, demand=0.0, type="charging_station"),
        DemoNode(id=101, x=4.5, y=4.0, demand=0.0, type="charging_station"),
    ]

    return DemoInstance(nodes=nodes)


def main() -> None:
    instance = make_demo_instance()

    result = solve_ga(
        instance,
        population_size=40,
        generations=60,
        crossover_rate=0.85,
        mutation_rate=0.20,
        elite_size=2,
        tournament_size=3,
        random_seed=42,
    )

    print("=== GA-style EVRP-TW Baseline Demo ===")
    print("Method: ga_baseline")
    print(f"Population size: {result.population_size}")
    print(f"Generations: {result.generation_count}")
    print(f"Objective distance: {result.objective:.4f}")
    print(f"Best fitness: {result.best_fitness:.4f}")
    print(f"Feasible: {result.feasible}")
    print(f"Runtime seconds: {result.runtime_seconds:.6f}")

    if result.feasibility_messages:
        print("\nFeasibility messages:")
        for message in result.feasibility_messages:
            print(f"- {message}")

    print("\nRoutes:")
    for idx, route in enumerate(result.solution.routes, start=1):
        print(f"Route {idx}: {route.node_ids}")


if __name__ == "__main__":
    main()
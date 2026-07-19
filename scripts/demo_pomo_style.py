from dataclasses import dataclass

from src.baselines.pomo_style import solve_pomo_style


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


def make_demo_instance() -> DemoInstance:
    nodes = [
        DemoNode(id=0, x=0.0, y=0.0, demand=0.0, type="depot"),
        DemoNode(id=1, x=1.0, y=1.0, demand=1.0, type="customer"),
        DemoNode(id=2, x=2.0, y=1.0, demand=1.0, type="customer"),
        DemoNode(id=3, x=1.0, y=3.0, demand=1.0, type="customer"),
        DemoNode(id=4, x=4.0, y=3.0, demand=1.0, type="customer"),
        DemoNode(id=5, x=5.0, y=2.0, demand=1.0, type="customer"),
        DemoNode(id=6, x=3.0, y=5.0, demand=1.0, type="customer"),
    ]

    return DemoInstance(nodes=nodes)


def main() -> None:
    instance = make_demo_instance()

    result = solve_pomo_style(
        instance,
        rollout_count=12,
        random_seed=42,
    )

    print("=== POMO-style EVRP-TW Baseline Demo ===")
    print(f"Method: pomo_style")
    print(f"Rollouts: {result.rollout_count}")
    print(f"Selected rollout: {result.selected_rollout}")
    print(f"Objective distance: {result.objective:.4f}")
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
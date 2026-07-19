"""

This script compares:
- greedy baseline, if available
- nearest-neighbor baseline

The output includes:
- objective value / total distance
- feasibility status
- runtime
- number of routes
- number of charging station visits

"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.baselines.comparison import (  # noqa: E402
    BaselineMethod,
    compare_baselines,
    results_to_csv,
    results_to_markdown,
)
from src.baselines.nearest_neighbor import (  # noqa: E402
    NearestNeighborConfig,
    solve_nearest_neighbor,
)
from src.solution import Route, Solution  # noqa: E402


@dataclass
class ComparisonNode:
    id: int
    x: float
    y: float
    demand: float
    ready_time: float
    due_time: float
    service_time: float
    node_type: str


class ComparisonInstance:
    """
    Deterministic EVRP-TW-like instance used for baseline comparison.

    The instance is deliberately small and reproducible:
    - one depot
    - six customers
    - one charging station
    - loose time windows

    This is not meant to be a benchmark-scale instance. It is a clean smoke-test
    instance for comparing baseline behavior.
    """

    def __init__(self) -> None:
        self.depot = ComparisonNode(
            id=0,
            x=0.0,
            y=0.0,
            demand=0.0,
            ready_time=0.0,
            due_time=1000.0,
            service_time=0.0,
            node_type="depot",
        )

        self.customers = [
            ComparisonNode(
                id=1,
                x=2.0,
                y=1.0,
                demand=1.0,
                ready_time=0.0,
                due_time=1000.0,
                service_time=1.0,
                node_type="customer",
            ),
            ComparisonNode(
                id=2,
                x=4.0,
                y=1.5,
                demand=1.0,
                ready_time=0.0,
                due_time=1000.0,
                service_time=1.0,
                node_type="customer",
            ),
            ComparisonNode(
                id=3,
                x=6.0,
                y=2.0,
                demand=1.0,
                ready_time=0.0,
                due_time=1000.0,
                service_time=1.0,
                node_type="customer",
            ),
            ComparisonNode(
                id=4,
                x=3.0,
                y=5.0,
                demand=1.0,
                ready_time=0.0,
                due_time=1000.0,
                service_time=1.0,
                node_type="customer",
            ),
            ComparisonNode(
                id=5,
                x=7.0,
                y=5.0,
                demand=1.0,
                ready_time=0.0,
                due_time=1000.0,
                service_time=1.0,
                node_type="customer",
            ),
            ComparisonNode(
                id=6,
                x=8.0,
                y=1.0,
                demand=1.0,
                ready_time=0.0,
                due_time=1000.0,
                service_time=1.0,
                node_type="customer",
            ),
        ]

        self.stations = [
            ComparisonNode(
                id=100,
                x=4.0,
                y=0.0,
                demand=0.0,
                ready_time=0.0,
                due_time=1000.0,
                service_time=2.0,
                node_type="station",
            )
        ]

        self.depot_id = self.depot.id
        self.vehicle_count = 3
        self.vehicle_capacity = 10.0
        self.battery_capacity = 100.0
        self.energy_consumption_rate = 1.0
        self.vehicle_speed = 1.0

        self._nodes = {self.depot.id: self.depot}

        for node in self.customers:
            self._nodes[node.id] = node

        for node in self.stations:
            self._nodes[node.id] = node

    def get_node(self, node_id: int) -> ComparisonNode:
        return self._nodes[node_id]


def solve_simple_greedy_one_customer_per_route(instance: ComparisonInstance) -> Solution:
    """
    Very simple greedy baseline.

    Each customer gets its own route:

        depot -> customer -> depot

    This is intentionally basic. It acts as a weak but reliable baseline.
    Nearest-neighbor should usually use fewer vehicles or shorter distance.
    """

    routes: list[Route] = []

    for customer in instance.customers:
        routes.append(
            Route(
                node_ids=[
                    instance.depot_id,
                    customer.id,
                    instance.depot_id,
                ]
            )
        )

    return Solution(routes=routes)


def solve_nearest_neighbor_adapter(instance: ComparisonInstance) -> Solution:
    """
    Adapter for the nearest-neighbor baseline.

    The adapter keeps the comparison framework clean because all methods follow
    the same interface:

        solver(instance) -> Solution
    """

    config = NearestNeighborConfig(
        use_charging_stations=True,
        allow_infeasible_fallback=True,
        max_routes=None,
    )

    return solve_nearest_neighbor(instance, config=config)


def format_route(instance: ComparisonInstance, node_ids: list[int]) -> str:
    """
    Format a route using D/C/S labels.
    """

    labels = []

    for node_id in node_ids:
        node = instance.get_node(node_id)

        if node.node_type == "depot":
            labels.append(f"D{node.id}")
        elif node.node_type == "customer":
            labels.append(f"C{node.id}")
        elif node.node_type == "station":
            labels.append(f"S{node.id}")
        else:
            labels.append(str(node.id))

    return " -> ".join(labels)


def main() -> None:
    instance = ComparisonInstance()

    methods = [
        BaselineMethod(
            name="greedy_one_customer_per_route",
            solver=solve_simple_greedy_one_customer_per_route,
        ),
        BaselineMethod(
            name="nearest_neighbor",
            solver=solve_nearest_neighbor_adapter,
        ),
    ]

    results = compare_baselines(instance, methods)

    print("=" * 88)
    print("Week 2 Baseline Comparison")
    print("=" * 88)

    print()
    print("Instance")
    print(f"- customers: {len(instance.customers)}")
    print(f"- charging stations: {len(instance.stations)}")
    print(f"- vehicle count limit: {instance.vehicle_count}")
    print(f"- vehicle capacity: {instance.vehicle_capacity}")
    print(f"- battery capacity: {instance.battery_capacity}")

    print()
    print("Comparison Table")
    print(results_to_markdown(results))

    print()
    print("CSV Output")
    print(results_to_csv(results))

    print()
    print("Routes")
    for result in results:
        print(f"\nMethod: {result.method}")
        for route_index, route in enumerate(result.routes, start=1):
            print(f"- route {route_index}: {format_route(instance, route)}")

        if result.messages:
            print("- feasibility messages:")
            for message in result.messages:
                print(f"  - {message}")

    print()
    print("=" * 88)


if __name__ == "__main__":
    main()
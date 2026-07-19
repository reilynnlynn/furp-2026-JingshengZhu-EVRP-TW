from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.baselines.nearest_neighbor import (  # noqa: E402
    NearestNeighborConfig,
    solve_nearest_neighbor,
    summarize_nearest_neighbor_solution,
)
from src.checker import check_solution  # noqa: E402


@dataclass
class DemoNode:
    id: int
    x: float
    y: float
    demand: float
    ready_time: float
    due_time: float
    service_time: float
    node_type: str


class DemoInstance:
    """
    Small deterministic EVRP-TW-like instance for demo purpose.

    The geometry is simple:
    depot:      0
    customers: 1, 2, 3, 4
    station:   100

    The time windows and battery are loose enough that the nearest-neighbor
    baseline should find a feasible route.
    """

    def __init__(self) -> None:
        self.depot = DemoNode(
            id=0,
            x=0.0,
            y=0.0,
            demand=0.0,
            ready_time=0.0,
            due_time=999.0,
            service_time=0.0,
            node_type="depot",
        )

        self.customers = [
            DemoNode(
                id=1,
                x=2.0,
                y=1.0,
                demand=1.0,
                ready_time=0.0,
                due_time=999.0,
                service_time=1.0,
                node_type="customer",
            ),
            DemoNode(
                id=2,
                x=4.0,
                y=1.0,
                demand=1.0,
                ready_time=0.0,
                due_time=999.0,
                service_time=1.0,
                node_type="customer",
            ),
            DemoNode(
                id=3,
                x=6.0,
                y=2.0,
                demand=1.0,
                ready_time=0.0,
                due_time=999.0,
                service_time=1.0,
                node_type="customer",
            ),
            DemoNode(
                id=4,
                x=7.0,
                y=0.0,
                demand=1.0,
                ready_time=0.0,
                due_time=999.0,
                service_time=1.0,
                node_type="customer",
            ),
        ]

        self.stations = [
            DemoNode(
                id=100,
                x=3.5,
                y=0.0,
                demand=0.0,
                ready_time=0.0,
                due_time=999.0,
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

    def get_node(self, node_id: int) -> DemoNode:
        return self._nodes[node_id]


def format_route(instance: DemoInstance, node_ids: list[int]) -> str:
    """
    Format one route with node type labels.
    """

    parts = []

    for node_id in node_ids:
        node = instance.get_node(node_id)

        if node.node_type == "depot":
            label = f"D{node.id}"
        elif node.node_type == "customer":
            label = f"C{node.id}"
        elif node.node_type == "station":
            label = f"S{node.id}"
        else:
            label = str(node.id)

        parts.append(label)

    return " -> ".join(parts)


def main() -> None:
    instance = DemoInstance()

    config = NearestNeighborConfig(
        use_charging_stations=True,
        allow_infeasible_fallback=True,
        max_routes=None,
    )

    solution = solve_nearest_neighbor(instance, config=config)
    check_result = check_solution(instance, solution)
    summary = summarize_nearest_neighbor_solution(instance, solution)

    print("=" * 72)
    print("Nearest-Neighbor Baseline Demo")
    print("=" * 72)

    print()
    print("Instance")
    print(f"- customers: {len(instance.customers)}")
    print(f"- stations: {len(instance.stations)}")
    print(f"- vehicle_count: {instance.vehicle_count}")
    print(f"- vehicle_capacity: {instance.vehicle_capacity}")
    print(f"- battery_capacity: {instance.battery_capacity}")

    print()
    print("Routes")
    for route_index, route in enumerate(solution.routes, start=1):
        print(f"- route {route_index}: {format_route(instance, route.node_ids)}")

    print()
    print("Feasibility")
    print(f"- feasible: {check_result.feasible}")
    print(f"- violation_count: {len(check_result.messages)}")

    if check_result.messages:
        print("- messages:")
        for message in check_result.messages:
            print(f"  - {message}")

    print()
    print("Summary")
    print(f"- method: {summary['method']}")
    print(f"- total_distance: {summary['total_distance']}")
    print(f"- vehicle_count: {summary['vehicle_count']}")
    print(f"- charging_visits: {summary['charging_visits']}")
    print(f"- feasible: {summary['feasible']}")
    print(f"- violation_count: {summary['violation_count']}")

    print()
    print("=" * 72)


if __name__ == "__main__":
    main()
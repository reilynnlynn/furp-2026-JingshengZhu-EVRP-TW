"""
Tests for the nearest-neighbor EVRP-TW baseline.

These tests use a small deterministic toy instance so that the baseline can be
checked without depending on random generation.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.baselines.nearest_neighbor import (
    NearestNeighborConfig,
    solve_nearest_neighbor,
    summarize_nearest_neighbor_solution,
)
from src.checker import check_solution


@dataclass
class ToyNode:
    id: int
    x: float
    y: float
    demand: float
    ready_time: float
    due_time: float
    service_time: float
    node_type: str


class ToyInstance:
    """
    Small deterministic EVRP-TW-like instance for unit tests.

    This class intentionally exposes the same attributes/methods used by the
    project code:
    - depot
    - customers
    - stations
    - depot_id
    - vehicle_count
    - vehicle_capacity
    - battery_capacity
    - energy_consumption_rate
    - vehicle_speed
    - get_node(...)
    """

    def __init__(self) -> None:
        self.depot = ToyNode(
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
            ToyNode(
                id=1,
                x=2.0,
                y=0.0,
                demand=1.0,
                ready_time=0.0,
                due_time=999.0,
                service_time=0.0,
                node_type="customer",
            ),
            ToyNode(
                id=2,
                x=4.0,
                y=0.0,
                demand=1.0,
                ready_time=0.0,
                due_time=999.0,
                service_time=0.0,
                node_type="customer",
            ),
            ToyNode(
                id=3,
                x=6.0,
                y=0.0,
                demand=1.0,
                ready_time=0.0,
                due_time=999.0,
                service_time=0.0,
                node_type="customer",
            ),
        ]

        self.stations = [
            ToyNode(
                id=100,
                x=3.0,
                y=0.0,
                demand=0.0,
                ready_time=0.0,
                due_time=999.0,
                service_time=0.0,
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

    def get_node(self, node_id: int) -> ToyNode:
        return self._nodes[node_id]


def test_nearest_neighbor_returns_solution_covering_all_customers() -> None:
    instance = ToyInstance()

    solution = solve_nearest_neighbor(instance)

    visited_customer_ids = []
    for route in solution.routes:
        for node_id in route.node_ids:
            node = instance.get_node(node_id)
            if node.node_type == "customer":
                visited_customer_ids.append(node_id)

    expected_customer_ids = sorted(customer.id for customer in instance.customers)

    assert sorted(visited_customer_ids) == expected_customer_ids


def test_nearest_neighbor_solution_starts_and_ends_at_depot() -> None:
    instance = ToyInstance()

    solution = solve_nearest_neighbor(instance)

    assert len(solution.routes) > 0

    for route in solution.routes:
        assert route.node_ids[0] == instance.depot_id
        assert route.node_ids[-1] == instance.depot_id


def test_nearest_neighbor_solution_is_feasible_on_toy_instance() -> None:
    instance = ToyInstance()

    solution = solve_nearest_neighbor(
        instance,
        config=NearestNeighborConfig(
            use_charging_stations=True,
            allow_infeasible_fallback=False,
        ),
    )

    result = check_solution(instance, solution)

    assert result.feasible, result.messages


def test_nearest_neighbor_summary_contains_required_fields() -> None:
    instance = ToyInstance()

    solution = solve_nearest_neighbor(instance)
    summary = summarize_nearest_neighbor_solution(instance, solution)

    assert summary["method"] == "nearest_neighbor"
    assert "total_distance" in summary
    assert "vehicle_count" in summary
    assert "charging_visits" in summary
    assert "feasible" in summary
    assert "violation_count" in summary
    assert "messages" in summary

    assert summary["total_distance"] >= 0
    assert summary["vehicle_count"] == len(solution.routes)
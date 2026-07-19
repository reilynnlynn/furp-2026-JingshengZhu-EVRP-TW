from __future__ import annotations

from dataclasses import dataclass

from src.baselines.comparison import (
    BaselineMethod,
    calculate_solution_distance,
    compare_baselines,
    count_charging_visits,
    evaluate_baseline,
    results_to_csv,
    results_to_markdown,
)
from src.solution import Route, Solution


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
                x=3.0,
                y=4.0,
                demand=1.0,
                ready_time=0.0,
                due_time=999.0,
                service_time=0.0,
                node_type="customer",
            ),
            ToyNode(
                id=2,
                x=6.0,
                y=8.0,
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
                x=1.0,
                y=1.0,
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


def toy_solver_without_station(instance: ToyInstance) -> Solution:
    return Solution(
        routes=[
            Route(
                node_ids=[
                    instance.depot_id,
                    1,
                    2,
                    instance.depot_id,
                ]
            )
        ]
    )


def toy_solver_with_station(instance: ToyInstance) -> Solution:
    return Solution(
        routes=[
            Route(
                node_ids=[
                    instance.depot_id,
                    1,
                    100,
                    2,
                    instance.depot_id,
                ]
            )
        ]
    )


def test_calculate_solution_distance() -> None:
    instance = ToyInstance()
    solution = toy_solver_without_station(instance)

    distance = calculate_solution_distance(instance, solution)

    # Route: 0 -> 1 -> 2 -> 0
    # 0 -> 1 = 5
    # 1 -> 2 = 5
    # 2 -> 0 = 10
    assert distance == 20.0


def test_count_charging_visits() -> None:
    instance = ToyInstance()
    solution = toy_solver_with_station(instance)

    charging_visits = count_charging_visits(instance, solution)

    assert charging_visits == 1


def test_evaluate_baseline_returns_expected_fields() -> None:
    instance = ToyInstance()

    method = BaselineMethod(
        name="toy_solver",
        solver=toy_solver_without_station,
    )

    result = evaluate_baseline(instance, method)

    assert result.method == "toy_solver"
    assert result.total_distance == 20.0
    assert result.vehicle_count == 1
    assert result.charging_visits == 0
    assert isinstance(result.feasible, bool)
    assert isinstance(result.violation_count, int)
    assert result.runtime_seconds >= 0
    assert result.routes == [[0, 1, 2, 0]]
    assert isinstance(result.messages, list)


def test_compare_baselines_returns_multiple_results() -> None:
    instance = ToyInstance()

    methods = [
        BaselineMethod(
            name="without_station",
            solver=toy_solver_without_station,
        ),
        BaselineMethod(
            name="with_station",
            solver=toy_solver_with_station,
        ),
    ]

    results = compare_baselines(instance, methods)

    assert len(results) == 2
    assert results[0].method == "without_station"
    assert results[1].method == "with_station"


def test_results_to_markdown_contains_methods() -> None:
    instance = ToyInstance()

    methods = [
        BaselineMethod(
            name="without_station",
            solver=toy_solver_without_station,
        ),
        BaselineMethod(
            name="with_station",
            solver=toy_solver_with_station,
        ),
    ]

    results = compare_baselines(instance, methods)
    markdown = results_to_markdown(results)

    assert "| Method | Total Distance | Vehicles | Charging Visits | Feasible | Violations | Runtime (s) |" in markdown
    assert "without_station" in markdown
    assert "with_station" in markdown


def test_results_to_csv_contains_methods() -> None:
    instance = ToyInstance()

    methods = [
        BaselineMethod(
            name="without_station",
            solver=toy_solver_without_station,
        ),
        BaselineMethod(
            name="with_station",
            solver=toy_solver_with_station,
        ),
    ]

    results = compare_baselines(instance, methods)
    csv_text = results_to_csv(results)

    assert "method,total_distance,vehicle_count,charging_visits,feasible,violation_count,runtime_seconds" in csv_text
    assert "without_station" in csv_text
    assert "with_station" in csv_text
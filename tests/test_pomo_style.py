from dataclasses import dataclass

from src.baselines.pomo_style import POMOStyleBaseline, solve_pomo_style


@dataclass
class DummyNode:
    id: int
    x: float
    y: float
    demand: float = 0.0
    type: str = "customer"


@dataclass
class DummyInstance:
    nodes: list[DummyNode]
    depot_id: int = 0
    vehicle_capacity: float = 100.0
    vehicle_speed: float = 1.0


def _make_dummy_instance() -> DummyInstance:
    nodes = [
        DummyNode(id=0, x=0.0, y=0.0, demand=0.0, type="depot"),
        DummyNode(id=1, x=1.0, y=0.0, demand=1.0, type="customer"),
        DummyNode(id=2, x=2.0, y=0.0, demand=1.0, type="customer"),
        DummyNode(id=3, x=0.0, y=2.0, demand=1.0, type="customer"),
        DummyNode(id=4, x=2.0, y=2.0, demand=1.0, type="customer"),
    ]
    return DummyInstance(nodes=nodes)


def _visited_customers(solution):
    visited = []

    for route in solution.routes:
        for node_id in route.node_ids:
            if node_id != 0:
                visited.append(node_id)

    return visited


def test_pomo_style_returns_solution_covering_all_customers_once():
    instance = _make_dummy_instance()

    result = solve_pomo_style(
        instance,
        rollout_count=8,
        random_seed=123,
    )

    assert result.solution is not None
    assert len(result.solution.routes) >= 1

    visited = _visited_customers(result.solution)

    assert sorted(visited) == [1, 2, 3, 4]
    assert len(visited) == len(set(visited))


def test_pomo_style_routes_start_and_end_at_depot():
    instance = _make_dummy_instance()

    result = solve_pomo_style(
        instance,
        rollout_count=8,
        random_seed=123,
    )

    for route in result.solution.routes:
        assert route.node_ids[0] == 0
        assert route.node_ids[-1] == 0


def test_pomo_style_objective_is_positive():
    instance = _make_dummy_instance()

    result = solve_pomo_style(
        instance,
        rollout_count=8,
        random_seed=123,
    )

    assert result.objective > 0.0
    assert result.rollout_count == 8
    assert result.runtime_seconds >= 0.0


def test_pomo_style_class_api():
    instance = _make_dummy_instance()

    solver = POMOStyleBaseline(
        rollout_count=4,
        random_seed=1,
    )
    result = solver.solve(instance)

    assert result.solution is not None
    assert result.rollout_count == 4
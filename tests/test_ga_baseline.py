from dataclasses import dataclass

from src.baselines.ga_baseline import GABaseline, solve_ga


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
    battery_range: float = 100.0


def _make_dummy_instance() -> DummyInstance:
    nodes = [
        DummyNode(id=0, x=0.0, y=0.0, demand=0.0, type="depot"),
        DummyNode(id=1, x=1.0, y=0.0, demand=1.0, type="customer"),
        DummyNode(id=2, x=2.0, y=0.0, demand=1.0, type="customer"),
        DummyNode(id=3, x=0.0, y=2.0, demand=1.0, type="customer"),
        DummyNode(id=4, x=2.0, y=2.0, demand=1.0, type="customer"),
    ]
    return DummyInstance(nodes=nodes)


def _make_dummy_instance_with_station() -> DummyInstance:
    nodes = [
        DummyNode(id=0, x=0.0, y=0.0, demand=0.0, type="depot"),
        DummyNode(id=1, x=10.0, y=0.0, demand=1.0, type="customer"),
        DummyNode(id=2, x=20.0, y=0.0, demand=1.0, type="customer"),
        DummyNode(id=100, x=5.0, y=0.0, demand=0.0, type="charging_station"),
        DummyNode(id=101, x=15.0, y=0.0, demand=0.0, type="charging_station"),
    ]
    return DummyInstance(
        nodes=nodes,
        depot_id=0,
        vehicle_capacity=100.0,
        vehicle_speed=1.0,
        battery_range=7.5,
    )


def _visited_customers(solution):
    visited = []

    for route in solution.routes:
        for node_id in route.node_ids:
            if node_id not in {0, 100, 101}:
                visited.append(node_id)

    return visited


def test_ga_returns_solution_covering_all_customers_once():
    instance = _make_dummy_instance()

    result = solve_ga(
        instance,
        population_size=20,
        generations=20,
        random_seed=123,
    )

    assert result.solution is not None
    assert len(result.solution.routes) >= 1

    visited = _visited_customers(result.solution)

    assert sorted(visited) == [1, 2, 3, 4]
    assert len(visited) == len(set(visited))


def test_ga_routes_start_and_end_at_depot():
    instance = _make_dummy_instance()

    result = solve_ga(
        instance,
        population_size=20,
        generations=20,
        random_seed=123,
    )

    for route in result.solution.routes:
        assert route.node_ids[0] == 0
        assert route.node_ids[-1] == 0


def test_ga_objective_and_runtime_are_valid():
    instance = _make_dummy_instance()

    result = solve_ga(
        instance,
        population_size=20,
        generations=20,
        random_seed=123,
    )

    assert result.objective > 0.0
    assert result.population_size == 20
    assert result.generation_count == 20
    assert result.runtime_seconds >= 0.0


def test_ga_class_api():
    instance = _make_dummy_instance()

    solver = GABaseline(
        population_size=16,
        generations=10,
        random_seed=1,
    )
    result = solver.solve(instance)

    assert result.solution is not None
    assert result.population_size == 16
    assert result.generation_count == 10


def test_ga_can_insert_charging_station_for_long_edges():
    instance = _make_dummy_instance_with_station()

    result = solve_ga(
        instance,
        population_size=16,
        generations=10,
        random_seed=1,
    )

    route_node_ids = []
    for route in result.solution.routes:
        route_node_ids.extend(route.node_ids)

    assert 1 in route_node_ids
    assert 2 in route_node_ids

    # With the small battery range and available stations, the repair step
    # should try to insert at least one charging station.
    assert 100 in route_node_ids or 101 in route_node_ids
"""
1. Start each vehicle route from the depot.
2. Repeatedly select the nearest feasible unvisited customer.
3. If direct travel is impossible due to battery, optionally insert one
   charging station.
4. Close each route by returning to the depot.
5. Optionally add fallback single-customer routes for customers not inserted
   by the heuristic.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.checker import check_solution
from src.distance import euclidean_distance
from src.instance import EVRPTWInstance, Node
from src.solution import Route, Solution


EPS = 1e-9


@dataclass
class NearestNeighborConfig:
    """
    Configuration for nearest-neighbor baseline.
    """

    use_charging_stations: bool = True
    allow_infeasible_fallback: bool = True
    max_routes: int | None = None


@dataclass
class RouteState:
    """
    Internal state used while constructing one route.
    """

    current_node_id: int
    current_time: float
    current_load: float
    current_battery: float


def solve_nearest_neighbor(
    instance: EVRPTWInstance,
    config: NearestNeighborConfig | None = None,
) -> Solution:
    """
    Solve an EVRP-TW instance using a nearest-neighbor heuristic.

    Parameters
    ----------
    instance:
        EVRP-TW instance.

    config:
        Optional nearest-neighbor configuration.

    Returns
    -------
    Solution
        Constructed solution.
    """

    if config is None:
        config = NearestNeighborConfig()

    max_routes = config.max_routes
    if max_routes is None:
        max_routes = instance.vehicle_count

    depot_id = instance.depot_id
    unvisited_customer_ids = {customer.id for customer in instance.customers}
    routes: list[Route] = []

    for _ in range(max_routes):
        if not unvisited_customer_ids:
            break

        route_node_ids, served_customer_ids = _build_one_route(
            instance=instance,
            remaining_customer_ids=unvisited_customer_ids,
            config=config,
        )

        if not served_customer_ids:
            break

        routes.append(Route(node_ids=route_node_ids))
        unvisited_customer_ids -= served_customer_ids

    if unvisited_customer_ids and config.allow_infeasible_fallback:
        for customer_id in sorted(unvisited_customer_ids):
            routes.append(Route(node_ids=[depot_id, customer_id, depot_id]))

    return Solution(routes=routes)


def _build_one_route(
    instance: EVRPTWInstance,
    remaining_customer_ids: set[int],
    config: NearestNeighborConfig,
) -> tuple[list[int], set[int]]:
    """
    Build one route using nearest-neighbor selection.
    """

    route_node_ids = [instance.depot_id]
    served_customer_ids: set[int] = set()

    state = RouteState(
        current_node_id=instance.depot_id,
        current_time=0.0,
        current_load=0.0,
        current_battery=instance.battery_capacity,
    )

    while True:
        candidate_ids = sorted(
            remaining_customer_ids - served_customer_ids,
            key=lambda customer_id: euclidean_distance(
                instance.get_node(state.current_node_id),
                instance.get_node(customer_id),
            ),
        )

        selected_customer_id: int | None = None
        selected_route_node_ids: list[int] | None = None
        selected_state: RouteState | None = None

        for candidate_id in candidate_ids:
            candidate_node = instance.get_node(candidate_id)

            if state.current_load + candidate_node.demand > instance.vehicle_capacity:
                continue

            trial_route_node_ids = list(route_node_ids)
            trial_state = RouteState(
                current_node_id=state.current_node_id,
                current_time=state.current_time,
                current_load=state.current_load,
                current_battery=state.current_battery,
            )

            can_reach_customer = _travel_to_node(
                instance=instance,
                route_node_ids=trial_route_node_ids,
                state=trial_state,
                target_node=candidate_node,
                config=config,
            )

            if not can_reach_customer:
                continue

            trial_state.current_load += candidate_node.demand

            if not _can_return_to_depot(
                instance=instance,
                state=trial_state,
                route_node_ids=trial_route_node_ids,
                config=config,
            ):
                continue

            selected_customer_id = candidate_id
            selected_route_node_ids = trial_route_node_ids
            selected_state = trial_state
            break

        if selected_customer_id is None:
            break

        route_node_ids = selected_route_node_ids
        state = selected_state
        served_customer_ids.add(selected_customer_id)

    _travel_to_node(
        instance=instance,
        route_node_ids=route_node_ids,
        state=state,
        target_node=instance.depot,
        config=config,
    )

    return route_node_ids, served_customer_ids


def _can_return_to_depot(
    instance: EVRPTWInstance,
    state: RouteState,
    route_node_ids: list[int],
    config: NearestNeighborConfig,
) -> bool:
    """
    Check if the current trial route can return to depot.
    """

    trial_route_node_ids = list(route_node_ids)
    trial_state = RouteState(
        current_node_id=state.current_node_id,
        current_time=state.current_time,
        current_load=state.current_load,
        current_battery=state.current_battery,
    )

    return _travel_to_node(
        instance=instance,
        route_node_ids=trial_route_node_ids,
        state=trial_state,
        target_node=instance.depot,
        config=config,
    )


def _travel_to_node(
    instance: EVRPTWInstance,
    route_node_ids: list[int],
    state: RouteState,
    target_node: Node,
    config: NearestNeighborConfig,
) -> bool:
    """
    Try to travel from the current node to the target node.

    If direct travel is impossible due to battery, this function may insert
    one charging station if config.use_charging_stations is True.
    """

    current_node = instance.get_node(state.current_node_id)

    if _is_direct_travel_feasible(
        instance=instance,
        state=state,
        from_node=current_node,
        to_node=target_node,
    ):
        _apply_direct_travel(
            instance=instance,
            route_node_ids=route_node_ids,
            state=state,
            from_node=current_node,
            to_node=target_node,
        )
        return True

    if not config.use_charging_stations:
        return False

    station = _find_best_reachable_station(
        instance=instance,
        state=state,
        from_node=current_node,
        target_node=target_node,
    )

    if station is None:
        return False

    if not _is_direct_travel_feasible(
        instance=instance,
        state=state,
        from_node=current_node,
        to_node=station,
    ):
        return False

    _apply_direct_travel(
        instance=instance,
        route_node_ids=route_node_ids,
        state=state,
        from_node=current_node,
        to_node=station,
    )

    state.current_battery = instance.battery_capacity

    if not _is_direct_travel_feasible(
        instance=instance,
        state=state,
        from_node=station,
        to_node=target_node,
    ):
        return False

    _apply_direct_travel(
        instance=instance,
        route_node_ids=route_node_ids,
        state=state,
        from_node=station,
        to_node=target_node,
    )

    return True


def _is_direct_travel_feasible(
    instance: EVRPTWInstance,
    state: RouteState,
    from_node: Node,
    to_node: Node,
) -> bool:
    """
    Check whether direct travel from from_node to to_node is feasible.
    """

    distance = euclidean_distance(from_node, to_node)
    energy_needed = distance * instance.energy_consumption_rate

    if energy_needed > state.current_battery + EPS:
        return False

    arrival_time = state.current_time + distance / instance.vehicle_speed

    if arrival_time < to_node.ready_time:
        arrival_time = to_node.ready_time

    if arrival_time > to_node.due_time + EPS:
        return False

    return True


def _apply_direct_travel(
    instance: EVRPTWInstance,
    route_node_ids: list[int],
    state: RouteState,
    from_node: Node,
    to_node: Node,
) -> None:
    """
    Apply direct travel and update route state.
    """

    distance = euclidean_distance(from_node, to_node)
    energy_needed = distance * instance.energy_consumption_rate

    arrival_time = state.current_time + distance / instance.vehicle_speed

    if arrival_time < to_node.ready_time:
        arrival_time = to_node.ready_time

    state.current_time = arrival_time + to_node.service_time
    state.current_battery -= energy_needed
    state.current_node_id = to_node.id

    route_node_ids.append(to_node.id)

    if to_node.node_type == "station":
        state.current_battery = instance.battery_capacity


def _find_best_reachable_station(
    instance: EVRPTWInstance,
    state: RouteState,
    from_node: Node,
    target_node: Node,
) -> Node | None:
    """
    Find the best charging station that can help reach the target node.
    """

    best_station: Node | None = None
    best_extra_distance = float("inf")

    direct_distance = euclidean_distance(from_node, target_node)

    for station in instance.stations:
        distance_to_station = euclidean_distance(from_node, station)
        energy_to_station = distance_to_station * instance.energy_consumption_rate

        if energy_to_station > state.current_battery + EPS:
            continue

        arrival_at_station = state.current_time + distance_to_station / instance.vehicle_speed

        if arrival_at_station < station.ready_time:
            arrival_at_station = station.ready_time

        if arrival_at_station > station.due_time + EPS:
            continue

        distance_station_to_target = euclidean_distance(station, target_node)
        energy_station_to_target = (
            distance_station_to_target * instance.energy_consumption_rate
        )

        if energy_station_to_target > instance.battery_capacity + EPS:
            continue

        arrival_at_target = (
            arrival_at_station
            + station.service_time
            + distance_station_to_target / instance.vehicle_speed
        )

        if arrival_at_target < target_node.ready_time:
            arrival_at_target = target_node.ready_time

        if arrival_at_target > target_node.due_time + EPS:
            continue

        extra_distance = (
            distance_to_station + distance_station_to_target - direct_distance
        )

        if extra_distance < best_extra_distance:
            best_extra_distance = extra_distance
            best_station = station

    return best_station


def summarize_nearest_neighbor_solution(
    instance: EVRPTWInstance,
    solution: Solution,
) -> dict:
    """
    Summarize nearest-neighbor solution for reports and comparison tables.
    """

    check_result = check_solution(instance, solution)

    total_distance = 0.0
    charging_visits = 0

    for route in solution.routes:
        for i in range(len(route.node_ids) - 1):
            from_node = instance.get_node(route.node_ids[i])
            to_node = instance.get_node(route.node_ids[i + 1])
            total_distance += euclidean_distance(from_node, to_node)

        for node_id in route.node_ids:
            node = instance.get_node(node_id)
            if node.node_type == "station":
                charging_visits += 1

    return {
        "method": "nearest_neighbor",
        "total_distance": round(total_distance, 4),
        "vehicle_count": len(solution.routes),
        "charging_visits": charging_visits,
        "feasible": check_result.feasible,
        "violation_count": len(check_result.messages),
        "messages": check_result.messages,
    }
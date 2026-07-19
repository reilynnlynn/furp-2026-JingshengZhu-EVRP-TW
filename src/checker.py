from dataclasses import dataclass

from src.distance import euclidean_distance
from src.instance import EVRPTWInstance, Node
from src.solution import Route, Solution


@dataclass
class CheckResult:

    feasible: bool
    messages: list[str]


def check_solution(instance: EVRPTWInstance, solution: Solution) -> CheckResult:

    messages: list[str] = []

    _check_vehicle_count(instance, solution, messages)
    _check_route_depots(instance, solution, messages)
    _check_customer_visits(instance, solution, messages)
    _check_route_capacity(instance, solution, messages)
    _check_time_windows(instance, solution, messages)
    _check_battery(instance, solution, messages)

    return CheckResult(feasible=len(messages) == 0, messages=messages)


def _check_vehicle_count(
    instance: EVRPTWInstance,
    solution: Solution,
    messages: list[str],
) -> None:
    if len(solution.routes) > instance.vehicle_count:
        messages.append(
            f"Too many routes: {len(solution.routes)} used, "
            f"but only {instance.vehicle_count} vehicles available."
        )


def _check_route_depots(
    instance: EVRPTWInstance,
    solution: Solution,
    messages: list[str],
) -> None:
    depot_id = instance.depot_id

    for route_index, route in enumerate(solution.routes):
        if len(route.node_ids) < 2:
            messages.append(f"Route {route_index} is too short.")
            continue

        if route.node_ids[0] != depot_id:
            messages.append(
                f"Route {route_index} does not start at depot {depot_id}."
            )

        if route.node_ids[-1] != depot_id:
            messages.append(
                f"Route {route_index} does not end at depot {depot_id}."
            )


def _check_customer_visits(
    instance: EVRPTWInstance,
    solution: Solution,
    messages: list[str],
) -> None:
    expected_customer_ids = sorted(node.id for node in instance.customers)

    visited_customer_ids = []
    for route in solution.routes:
        for node_id in route.node_ids:
            node = instance.get_node(node_id)
            if node.node_type == "customer":
                visited_customer_ids.append(node_id)

    visited_customer_ids_sorted = sorted(visited_customer_ids)

    if visited_customer_ids_sorted != expected_customer_ids:
        messages.append(
            "Customer visit mismatch. "
            f"Expected {expected_customer_ids}, "
            f"but visited {visited_customer_ids_sorted}."
        )

    duplicated_customers = _find_duplicates(visited_customer_ids)
    if duplicated_customers:
        messages.append(
            f"Duplicated customer visits: {duplicated_customers}."
        )


def _check_route_capacity(
    instance: EVRPTWInstance,
    solution: Solution,
    messages: list[str],
) -> None:
    for route_index, route in enumerate(solution.routes):
        total_demand = 0.0

        for node_id in route.node_ids:
            node = instance.get_node(node_id)
            if node.node_type == "customer":
                total_demand += node.demand

        if total_demand > instance.vehicle_capacity:
            messages.append(
                f"Route {route_index} exceeds vehicle capacity: "
                f"demand {total_demand}, capacity {instance.vehicle_capacity}."
            )


def _check_time_windows(
    instance: EVRPTWInstance,
    solution: Solution,
    messages: list[str],
) -> None:
    for route_index, route in enumerate(solution.routes):
        current_time = 0.0

        for position in range(len(route.node_ids) - 1):
            current_node = instance.get_node(route.node_ids[position])
            next_node = instance.get_node(route.node_ids[position + 1])

            travel_time = _travel_time(instance, current_node, next_node)
            arrival_time = current_time + travel_time

            if arrival_time < next_node.ready_time:
                arrival_time = next_node.ready_time

            if arrival_time > next_node.due_time:
                messages.append(
                    f"Route {route_index} violates time window at node {next_node.id}: "
                    f"arrival {arrival_time:.2f}, due time {next_node.due_time:.2f}."
                )

            current_time = arrival_time + next_node.service_time


def _check_battery(
    instance: EVRPTWInstance,
    solution: Solution,
    messages: list[str],
) -> None:
    for route_index, route in enumerate(solution.routes):
        battery = instance.battery_capacity

        for position in range(len(route.node_ids) - 1):
            current_node = instance.get_node(route.node_ids[position])
            next_node = instance.get_node(route.node_ids[position + 1])

            distance = euclidean_distance(current_node, next_node)
            energy_used = distance * instance.energy_consumption_rate
            battery -= energy_used

            if battery < -1e-9:
                messages.append(
                    f"Route {route_index} violates battery constraint when traveling "
                    f"from node {current_node.id} to node {next_node.id}. "
                    f"Remaining battery: {battery:.2f}."
                )

            if next_node.node_type == "station":
                battery = instance.battery_capacity


def _travel_time(
    instance: EVRPTWInstance,
    from_node: Node,
    to_node: Node,
) -> float:
    distance = euclidean_distance(from_node, to_node)
    return distance / instance.vehicle_speed


def _find_duplicates(values: list[int]) -> list[int]:
    seen = set()
    duplicates = set()

    for value in values:
        if value in seen:
            duplicates.add(value)
        else:
            seen.add(value)

    return sorted(duplicates)
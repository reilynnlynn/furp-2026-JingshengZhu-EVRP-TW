from __future__ import annotations

from dataclasses import dataclass, field

from src.distance import euclidean_distance
from src.instance import EVRPTWInstance, Node
from src.solution import Route, Solution


@dataclass
class DecodeReport:
    success: bool
    message: str
    assigned_customers: list[int] = field(default_factory=list)
    unassigned_customers: list[int] = field(default_factory=list)
    route_count: int = 0
    split_reasons: list[str] = field(default_factory=list)


def decode_customer_order_to_multiroute_solution(
    instance: EVRPTWInstance,
    customer_order: list[int],
    allow_partial: bool = False,
) -> tuple[Solution, DecodeReport]:
    """
    Convert a customer visiting order into a feasible-ish multi-route solution.

    Parameters
    ----------
    instance:
        EVRP-TW instance.
    customer_order:
        Ordered list of customer node IDs.
    allow_partial:
        If False, unassigned customers make report.success False.
        If True, the decoder returns routes for assigned customers only.

    Returns
    -------
    (solution, report)
    """

    depot_id = instance.depot_id
    vehicle_limit = instance.vehicle_count

    node_by_id = {node.id: node for node in instance.nodes}
    customer_ids = {
        node.id for node in instance.nodes if node.node_type == "customer"
    }

    filtered_order = []
    seen = set()

    for node_id in customer_order:
        if node_id in customer_ids and node_id not in seen:
            filtered_order.append(node_id)
            seen.add(node_id)

    # Include omitted customers at the end so that methods returning partial
    # permutations are still comparable on full-instance coverage.
    for node_id in sorted(customer_ids):
        if node_id not in seen:
            filtered_order.append(node_id)
            seen.add(node_id)

    routes: list[Route] = []
    assigned: list[int] = []
    unassigned: list[int] = []
    split_reasons: list[str] = []

    current_route = [depot_id]
    current_load = 0.0
    current_time = 0.0
    current_battery = instance.battery_capacity
    current_node_id = depot_id

    def close_current_route(reason: str) -> None:
        nonlocal current_route, current_load, current_time, current_battery, current_node_id

        if len(current_route) > 1:
            current_route.append(depot_id)
            routes.append(Route(node_ids=list(current_route)))
            split_reasons.append(reason)

        current_route = [depot_id]
        current_load = 0.0
        current_time = 0.0
        current_battery = instance.battery_capacity
        current_node_id = depot_id

    def can_append_customer(customer: Node) -> tuple[bool, str, float, float, float]:
        """
        Check whether adding customer to the current route is possible.

        Returns:
            feasible, reason, arrival_time, departure_time, remaining_battery
        """
        nonlocal current_load, current_time, current_battery, current_node_id

        previous = node_by_id[current_node_id]
        depot = node_by_id[depot_id]

        travel_to_customer = euclidean_distance(previous, customer)
        energy_to_customer = travel_to_customer * instance.energy_consumption_rate

        if current_load + customer.demand > instance.vehicle_capacity:
            return False, "capacity", 0.0, 0.0, 0.0

        if energy_to_customer > current_battery:
            return False, "battery_to_customer", 0.0, 0.0, 0.0

        arrival = current_time + travel_to_customer
        service_start = max(arrival, customer.ready_time)

        if service_start > customer.due_time:
            return False, "time_window", 0.0, 0.0, 0.0

        departure = service_start + customer.service_time
        battery_after_customer = current_battery - energy_to_customer

        travel_back_depot = euclidean_distance(customer, depot)
        energy_back_depot = travel_back_depot * instance.energy_consumption_rate

        if energy_back_depot > battery_after_customer:
            return False, "battery_return_depot", 0.0, 0.0, 0.0

        return True, "ok", arrival, departure, battery_after_customer

    for customer_id in filtered_order:
        customer = node_by_id[customer_id]

        feasible, reason, _arrival, departure, remaining_battery = can_append_customer(customer)

        if not feasible:
            if len(current_route) > 1:
                close_current_route(f"split before customer {customer_id}: {reason}")
            else:
                # The customer cannot be served even as the first customer
                # under this simplified no-charging decoder.
                unassigned.append(customer_id)
                continue

            if len(routes) >= vehicle_limit:
                unassigned.append(customer_id)
                continue

            feasible, reason, _arrival, departure, remaining_battery = can_append_customer(customer)

            if not feasible:
                unassigned.append(customer_id)
                continue

        current_route.append(customer_id)
        assigned.append(customer_id)
        current_load += customer.demand
        current_time = departure
        current_battery = remaining_battery
        current_node_id = customer_id

    if len(current_route) > 1 and len(routes) < vehicle_limit:
        close_current_route("end of customer order")
    elif len(current_route) > 1 and len(routes) >= vehicle_limit:
        unassigned.extend([node_id for node_id in current_route if node_id != depot_id])

    success = len(unassigned) == 0 or allow_partial

    if success:
        message = "Decoded customer order into multi-route solution."
    else:
        message = (
            "Decoded partial solution; some customers are unassigned. "
            "This may happen because of vehicle count, capacity, time-window, "
            "or battery constraints."
        )

    report = DecodeReport(
        success=success,
        message=message,
        assigned_customers=assigned,
        unassigned_customers=unassigned,
        route_count=len(routes),
        split_reasons=split_reasons,
    )

    return Solution(routes=routes), report
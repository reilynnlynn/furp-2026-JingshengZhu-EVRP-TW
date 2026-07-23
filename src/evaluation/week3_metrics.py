from __future__ import annotations

from dataclasses import dataclass, asdict
import math
from typing import Any

from src.instance import EVRPTWInstance, Node


BIG_M = 1_000_000.0


@dataclass(frozen=True)
class ConstraintViolationSummary:
    """
    Attributes:
        duplicate_customers:
            Number of duplicated customer visits.
        missing_customers:
            Number of customers not served.
        unknown_nodes:
            Number of node IDs that do not exist in the instance.
        capacity_violations:
            Number of routes whose total demand exceeds vehicle capacity.
        battery_violations:
            Number of travel legs where required energy exceeds available battery.
        time_window_violations:
            Number of customer/station visits arriving after due_time.
        vehicle_count_violation:
            1 if number of used routes exceeds available vehicles, otherwise 0.
    """

    duplicate_customers: int = 0
    missing_customers: int = 0
    unknown_nodes: int = 0
    capacity_violations: int = 0
    battery_violations: int = 0
    time_window_violations: int = 0
    vehicle_count_violation: int = 0

    @property
    def total(self) -> int:
        return (
            self.duplicate_customers
            + self.missing_customers
            + self.unknown_nodes
            + self.capacity_violations
            + self.battery_violations
            + self.time_window_violations
            + self.vehicle_count_violation
        )


@dataclass(frozen=True)
class RouteEvaluation:
    """
    Attributes:
        route_index:
            Index of the route in the solution.
        route:
            Original route node ID list.
        cleaned_route:
            Route after removing depot markers.
        distance:
            Total route distance including depot departure and return.
        load:
            Total customer demand served by this route.
        vehicles_used:
            1 if this route is non-empty, otherwise 0.
        charging_visits:
            Number of station visits in this route.
        capacity_violation:
            Whether route demand exceeds vehicle capacity.
        battery_violations:
            Number of battery infeasible travel legs in this route.
        time_window_violations:
            Number of late arrivals in this route.
        unknown_nodes:
            Number of unknown node IDs in this route.
        timeline:
            Arrival/departure records for debugging and report explanation.
    """

    route_index: int
    route: list[int]
    cleaned_route: list[int]
    distance: float
    load: float
    vehicles_used: int
    charging_visits: int
    capacity_violation: bool
    battery_violations: int
    time_window_violations: int
    unknown_nodes: int
    timeline: list[dict[str, Any]]


@dataclass(frozen=True)
class SolutionEvaluation:
    """
    Attributes:
        instance_name:
            Name of the EVRP-TW instance.
        method_name:
            Name of the evaluated method.
        run_seed:
            Random seed used by the method.
        num_customers:
            Number of customers in the instance.
        num_stations:
            Number of charging stations in the instance.
        num_routes:
            Number of non-empty routes.
        vehicles_available:
            Number of vehicles available in the instance.
        vehicles_used:
            Number of vehicles used by the solution.
        total_distance:
            Total route distance.
        objective_value:
            Penalized objective value. Feasible solutions have objective equal
            to total distance. Infeasible solutions receive penalties.
        feasible:
            True if all checked constraints are satisfied.
        violations:
            ConstraintViolationSummary.
        runtime_seconds:
            Runtime measured by experiment runner.
        route_evaluations:
            Detailed route-level evaluations.
        notes:
            Optional explanation or warning messages.
    """

    instance_name: str
    method_name: str
    run_seed: int | None
    num_customers: int
    num_stations: int
    num_routes: int
    vehicles_available: int
    vehicles_used: int
    total_distance: float
    objective_value: float
    feasible: bool
    violations: ConstraintViolationSummary
    runtime_seconds: float | None
    route_evaluations: list[RouteEvaluation]
    notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["total_violations"] = self.violations.total
        return data


def euclidean_distance(node_a: Node, node_b: Node) -> float:
    """
    Args:
        node_a:
            First node.
        node_b:
            Second node.

    Returns:
        Euclidean distance.
    """

    return math.hypot(node_a.x - node_b.x, node_a.y - node_b.y)


def build_node_lookup(instance: EVRPTWInstance) -> dict[int, Node]:
    """
    Args:
        instance:
            EVRP-TW instance.

    Returns:
        Dictionary mapping node ID to Node.
    """

    return {node.id: node for node in instance.nodes}


def clean_route(route: list[int], depot_id: int) -> list[int]:
    """
    Args:
        route:
            Raw route node IDs.
        depot_id:
            Depot node ID.

    Returns:
        Route without depot markers.
    """

    return [node_id for node_id in route if node_id != depot_id]


def evaluate_single_route(
    instance: EVRPTWInstance,
    route: list[int],
    route_index: int,
) -> RouteEvaluation:
    """
    Args:
        instance:
            EVRP-TW instance.
        route:
            Route node IDs without required depot endpoints.
        route_index:
            Route index.

    Returns:
        RouteEvaluation.
    """

    node_lookup = build_node_lookup(instance)
    depot = node_lookup[instance.depot_id]
    cleaned = clean_route(route, instance.depot_id)

    if len(cleaned) == 0:
        return RouteEvaluation(
            route_index=route_index,
            route=list(route),
            cleaned_route=[],
            distance=0.0,
            load=0.0,
            vehicles_used=0,
            charging_visits=0,
            capacity_violation=False,
            battery_violations=0,
            time_window_violations=0,
            unknown_nodes=0,
            timeline=[],
        )

    distance = 0.0
    load = 0.0
    battery = instance.battery_capacity
    current_time = 0.0
    current_node = depot

    charging_visits = 0
    battery_violations = 0
    time_window_violations = 0
    unknown_nodes = 0
    timeline: list[dict[str, Any]] = []

    for node_id in cleaned:
        next_node = node_lookup.get(node_id)

        if next_node is None:
            unknown_nodes += 1
            timeline.append(
                {
                    "node_id": node_id,
                    "status": "unknown_node",
                }
            )
            continue

        leg_distance = euclidean_distance(current_node, next_node)
        required_energy = leg_distance * instance.energy_consumption_rate

        if required_energy > battery + 1e-9:
            battery_violations += 1
            battery = 0.0
        else:
            battery -= required_energy

        travel_time = leg_distance / instance.vehicle_speed
        arrival_time = current_time + travel_time
        service_start_time = max(arrival_time, next_node.ready_time)

        if service_start_time > next_node.due_time + 1e-9:
            time_window_violations += 1

        departure_time = service_start_time + next_node.service_time

        if next_node.node_type == "customer":
            load += next_node.demand

        if next_node.node_type == "station":
            charging_visits += 1
            missing_energy = instance.battery_capacity - battery
            charging_time = missing_energy / instance.charging_rate
            departure_time += charging_time
            battery = instance.battery_capacity

        timeline.append(
            {
                "node_id": next_node.id,
                "node_type": next_node.node_type,
                "arrival_time": arrival_time,
                "service_start_time": service_start_time,
                "departure_time": departure_time,
                "ready_time": next_node.ready_time,
                "due_time": next_node.due_time,
                "leg_distance": leg_distance,
                "battery_after_arrival": battery,
                "load_after_visit": load,
            }
        )

        distance += leg_distance
        current_time = departure_time
        current_node = next_node

    return_distance = euclidean_distance(current_node, depot)
    required_energy_to_depot = return_distance * instance.energy_consumption_rate

    if required_energy_to_depot > battery + 1e-9:
        battery_violations += 1

    distance += return_distance

    capacity_violation = load > instance.vehicle_capacity + 1e-9

    timeline.append(
        {
            "node_id": depot.id,
            "node_type": depot.node_type,
            "arrival_time": current_time + return_distance / instance.vehicle_speed,
            "service_start_time": current_time + return_distance / instance.vehicle_speed,
            "departure_time": current_time + return_distance / instance.vehicle_speed,
            "ready_time": depot.ready_time,
            "due_time": depot.due_time,
            "leg_distance": return_distance,
            "battery_after_arrival": max(
                0.0,
                battery - required_energy_to_depot,
            ),
            "load_after_visit": load,
        }
    )

    return RouteEvaluation(
        route_index=route_index,
        route=list(route),
        cleaned_route=cleaned,
        distance=distance,
        load=load,
        vehicles_used=1,
        charging_visits=charging_visits,
        capacity_violation=capacity_violation,
        battery_violations=battery_violations,
        time_window_violations=time_window_violations,
        unknown_nodes=unknown_nodes,
        timeline=timeline,
    )


def count_customer_coverage(
    instance: EVRPTWInstance,
    routes: list[list[int]],
) -> tuple[int, int]:
    """
    Count duplicate and missing customer visits.

    Args:
        instance:
            EVRP-TW instance.
        routes:
            Solution routes.

    Returns:
        A tuple:
            duplicate_customers, missing_customers
    """

    customer_ids = {customer.id for customer in instance.customers}
    visit_counts = {customer_id: 0 for customer_id in customer_ids}

    for route in routes:
        for node_id in clean_route(route, instance.depot_id):
            if node_id in visit_counts:
                visit_counts[node_id] += 1

    duplicate_customers = sum(max(0, count - 1) for count in visit_counts.values())
    missing_customers = sum(1 for count in visit_counts.values() if count == 0)

    return duplicate_customers, missing_customers


def compute_objective(
    total_distance: float,
    violations: ConstraintViolationSummary,
    penalty_per_violation: float = BIG_M,
) -> float:
    """
    Args:
        total_distance:
            Total travel distance.
        violations:
            Constraint violations.
        penalty_per_violation:
            Penalty for each violation.

    Returns:
        Penalized objective value.
    """

    return total_distance + penalty_per_violation * violations.total


def evaluate_solution(
    instance: EVRPTWInstance,
    routes: list[list[int]],
    method_name: str,
    run_seed: int | None = None,
    runtime_seconds: float | None = None,
    penalty_per_violation: float = BIG_M,
) -> SolutionEvaluation:
    """
    Args:
        instance:
            EVRP-TW instance.
        routes:
            List of vehicle routes.
        method_name:
            Name of the evaluated method.
        run_seed:
            Random seed used by stochastic method.
        runtime_seconds:
            Runtime measured by the experiment runner.
        penalty_per_violation:
            Penalty weight for infeasible solutions.

    Returns:
        SolutionEvaluation.
    """

    route_evaluations = [
        evaluate_single_route(
            instance=instance,
            route=route,
            route_index=index,
        )
        for index, route in enumerate(routes)
    ]

    total_distance = sum(route_eval.distance for route_eval in route_evaluations)
    vehicles_used = sum(route_eval.vehicles_used for route_eval in route_evaluations)

    duplicate_customers, missing_customers = count_customer_coverage(instance, routes)

    capacity_violations = sum(
        1 for route_eval in route_evaluations if route_eval.capacity_violation
    )
    battery_violations = sum(
        route_eval.battery_violations for route_eval in route_evaluations
    )
    time_window_violations = sum(
        route_eval.time_window_violations for route_eval in route_evaluations
    )
    unknown_nodes = sum(route_eval.unknown_nodes for route_eval in route_evaluations)

    vehicle_count_violation = 1 if vehicles_used > instance.vehicle_count else 0

    violations = ConstraintViolationSummary(
        duplicate_customers=duplicate_customers,
        missing_customers=missing_customers,
        unknown_nodes=unknown_nodes,
        capacity_violations=capacity_violations,
        battery_violations=battery_violations,
        time_window_violations=time_window_violations,
        vehicle_count_violation=vehicle_count_violation,
    )

    feasible = violations.total == 0

    notes: list[str] = []
    if duplicate_customers > 0:
        notes.append(f"duplicate_customers={duplicate_customers}")
    if missing_customers > 0:
        notes.append(f"missing_customers={missing_customers}")
    if unknown_nodes > 0:
        notes.append(f"unknown_nodes={unknown_nodes}")
    if capacity_violations > 0:
        notes.append(f"capacity_violations={capacity_violations}")
    if battery_violations > 0:
        notes.append(f"battery_violations={battery_violations}")
    if time_window_violations > 0:
        notes.append(f"time_window_violations={time_window_violations}")
    if vehicle_count_violation > 0:
        notes.append("vehicle_count_violation=1")

    objective_value = compute_objective(
        total_distance=total_distance,
        violations=violations,
        penalty_per_violation=penalty_per_violation,
    )

    return SolutionEvaluation(
        instance_name=instance.name,
        method_name=method_name,
        run_seed=run_seed,
        num_customers=len(instance.customers),
        num_stations=len(instance.stations),
        num_routes=len(routes),
        vehicles_available=instance.vehicle_count,
        vehicles_used=vehicles_used,
        total_distance=total_distance,
        objective_value=objective_value,
        feasible=feasible,
        violations=violations,
        runtime_seconds=runtime_seconds,
        route_evaluations=route_evaluations,
        notes=notes,
    )


def flatten_evaluation_for_csv(evaluation: SolutionEvaluation) -> dict[str, Any]:
    """
    Convert SolutionEvaluation to one flat CSV-friendly row.

    Args:
        evaluation:
            SolutionEvaluation object.

    Returns:
        Flat dictionary.
    """

    return {
        "instance_name": evaluation.instance_name,
        "method_name": evaluation.method_name,
        "run_seed": evaluation.run_seed,
        "num_customers": evaluation.num_customers,
        "num_stations": evaluation.num_stations,
        "vehicles_available": evaluation.vehicles_available,
        "vehicles_used": evaluation.vehicles_used,
        "num_routes": evaluation.num_routes,
        "feasible": evaluation.feasible,
        "objective_value": evaluation.objective_value,
        "total_distance": evaluation.total_distance,
        "runtime_seconds": evaluation.runtime_seconds,
        "total_violations": evaluation.violations.total,
        "duplicate_customers": evaluation.violations.duplicate_customers,
        "missing_customers": evaluation.violations.missing_customers,
        "unknown_nodes": evaluation.violations.unknown_nodes,
        "capacity_violations": evaluation.violations.capacity_violations,
        "battery_violations": evaluation.violations.battery_violations,
        "time_window_violations": evaluation.violations.time_window_violations,
        "vehicle_count_violation": evaluation.violations.vehicle_count_violation,
        "notes": "; ".join(evaluation.notes),
    }
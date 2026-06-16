import math
from typing import List, Dict, Tuple


# smoke-test
def build_instance():
    depot = {
        "id": 0,
        "x": 50,
        "y": 50,
        "ready_time": 0,
        "due_time": 1000,
        "service_time": 0,
        "demand": 0,
    }

    customers = [
        {"id": 1, "x": 20, "y": 60, "demand": 4, "ready_time": 0,   "due_time": 200, "service_time": 10},
        {"id": 2, "x": 18, "y": 54, "demand": 3, "ready_time": 20,  "due_time": 220, "service_time": 10},
        {"id": 3, "x": 80, "y": 65, "demand": 5, "ready_time": 0,   "due_time": 240, "service_time": 10},
        {"id": 4, "x": 75, "y": 20, "demand": 4, "ready_time": 50,  "due_time": 260, "service_time": 10},
        {"id": 5, "x": 30, "y": 20, "demand": 2, "ready_time": 30,  "due_time": 180, "service_time": 10},
        {"id": 6, "x": 60, "y": 80, "demand": 3, "ready_time": 0,   "due_time": 210, "service_time": 10},
    ]

    vehicle_capacity = 10
    num_vehicles = 4

    # battery settings
    battery_capacity = 120.0
    energy_consumption_rate = 1.0

    return depot, customers, vehicle_capacity, num_vehicles, battery_capacity, energy_consumption_rate


# distance between a and b
def distance(a: Dict, b: Dict) -> float:
    return math.hypot(a["x"] - b["x"], a["y"] - b["y"])


# route check
def check_route(
    route: List[Dict],
    depot: Dict,
    vehicle_capacity: int,
    battery_capacity: float,
    energy_consumption_rate: float
) -> Tuple[bool, Dict]:
    """
    Check if a route is feasible:
    - load <= capacity
    - time windows respected (including return to depot)
    - battery feasibility respected (including return to depot)
    """

    # check load and capacity
    load = sum(node["demand"] for node in route)
    if load > vehicle_capacity:
        return False, {"reason": "capacity exceeded"}

    total_distance = 0.0
    schedule = []

    current = depot
    current_time = 0.0
    remaining_battery = battery_capacity

    # check each customer in the route
    for customer in route:
        travel = distance(current, customer)
        energy_needed = travel * energy_consumption_rate

        # battery check before reaching customer
        if energy_needed > remaining_battery:
            return False, {
                "reason": f"battery infeasible before customer {customer['id']}",
                "remaining_battery": remaining_battery,
                "energy_needed": energy_needed,
            }

        arrival = current_time + travel
        start_service = max(arrival, customer["ready_time"])

        if start_service > customer["due_time"]:
            return False, {"reason": f"time window out of time in customer {customer['id']}"}

        departure = start_service + customer["service_time"]

        if departure > customer["due_time"]:
            return False, {"reason": f"time window out of time in customer {customer['id']}"}

        remaining_battery -= energy_needed
        total_distance += travel

        schedule.append({
            "id": customer["id"],
            "arrival": round(arrival, 2),
            "start_service": round(start_service, 2),
            "departure": round(departure, 2),
            "battery_after_arrival": round(remaining_battery, 2),
        })

        current = customer
        current_time = departure

    # return to depot
    back_distance = distance(current, depot) if route else 0.0
    back_energy = back_distance * energy_consumption_rate

    if back_energy > remaining_battery:
        return False, {
            "reason": "battery infeasible when returning to depot",
            "remaining_battery": remaining_battery,
            "energy_needed_to_depot": back_energy,
        }

    return_time = current_time + back_distance
    total_distance += back_distance
    remaining_battery -= back_energy

    # check depot due time
    if return_time > depot["due_time"]:
        return False, {"reason": "return to depot too late"}

    info = {
        "load": load,
        "total_distance": round(total_distance, 2),
        "schedule": schedule,
        "return_to_depot_time": round(return_time, 2),
        "battery_remaining_at_depot": round(remaining_battery, 2),
    }
    return True, info


# Simple sequential construction heuristic
# Sorted by:
# 1. farther from depot first
# 2. earlier due_time first
def construct_initial_solution(
    customers: List[Dict],
    depot: Dict,
    vehicle_capacity: int,
    num_vehicles: int,
    battery_capacity: float,
    energy_consumption_rate: float
):
    """
    Simple baseline:
    - try appending each customer to current route
    - if infeasible, close current route and start a new one
    """

    customers_sorted = sorted(
        customers,
        key=lambda c: (-distance(depot, c), c["due_time"])
    )

    routes = []
    current_route = []

    for customer in customers_sorted:
        trial_route = current_route + [customer]
        feasible, _ = check_route(
            trial_route,
            depot,
            vehicle_capacity,
            battery_capacity,
            energy_consumption_rate
        )

        if feasible:
            current_route.append(customer)
        else:
            if current_route:
                routes.append(current_route)

            current_route = [customer]

            feasible_single, _ = check_route(
                current_route,
                depot,
                vehicle_capacity,
                battery_capacity,
                energy_consumption_rate
            )
            if not feasible_single:
                raise ValueError(f"Customer {customer['id']} cannot be served even alone.")

    if current_route:
        routes.append(current_route)

    if len(routes) > num_vehicles:
        raise ValueError(
            f"Need {len(routes)} vehicles, but only {num_vehicles} available."
        )

    return routes


# Summarize solution
def summarize_solution(
    routes: List[List[Dict]],
    depot: Dict,
    vehicle_capacity: int,
    battery_capacity: float,
    energy_consumption_rate: float
):
    solution = []
    total_distance = 0.0

    for idx, route in enumerate(routes, start=1):
        feasible, info = check_route(
            route,
            depot,
            vehicle_capacity,
            battery_capacity,
            energy_consumption_rate
        )
        if not feasible:
            raise ValueError(f"Route {idx} infeasible: {info}")

        route_ids = [0] + [c["id"] for c in route] + [0]

        solution.append({
            "vehicle_id": idx,
            "route_ids": route_ids,
            "load": info["load"],
            "distance": info["total_distance"],
            "schedule": info["schedule"],
            "return_to_depot_time": info["return_to_depot_time"],
            "battery_remaining_at_depot": info["battery_remaining_at_depot"],
        })

        total_distance += info["total_distance"]

    return {
        "num_vehicles_used": len(routes),
        "total_distance": round(total_distance, 2),
        "routes": solution,
    }


# Print solution
def print_solution(result: Dict):
    print(f"Vehicles used: {result['num_vehicles_used']}")
    print(f"Total distance: {result['total_distance']}")
    print()

    for route_info in result["routes"]:
        print(f"Vehicle {route_info['vehicle_id']}")
        print(f"  Route: {' -> '.join(map(str, route_info['route_ids']))}")
        print(f"  Load: {route_info['load']}")
        print(f"  Distance: {route_info['distance']}")
        print(f"  Return to depot time: {route_info['return_to_depot_time']}")
        print(f"  Battery remaining at depot: {route_info['battery_remaining_at_depot']}")
        print("  Schedule:")
        for s in route_info["schedule"]:
            print(
                f"    Customer {s['id']}: "
                f"arrival={s['arrival']}, "
                f"start={s['start_service']}, "
                f"departure={s['departure']}, "
                f"battery_after_arrival={s['battery_after_arrival']}"
            )
        print()


# Main
def main():
    depot, customers, vehicle_capacity, num_vehicles, battery_capacity, energy_consumption_rate = build_instance()

    routes = construct_initial_solution(
        customers=customers,
        depot=depot,
        vehicle_capacity=vehicle_capacity,
        num_vehicles=num_vehicles,
        battery_capacity=battery_capacity,
        energy_consumption_rate=energy_consumption_rate
    )

    result = summarize_solution(
        routes=routes,
        depot=depot,
        vehicle_capacity=vehicle_capacity,
        battery_capacity=battery_capacity,
        energy_consumption_rate=energy_consumption_rate
    )
    print_solution(result)


if __name__ == "__main__":
    main()
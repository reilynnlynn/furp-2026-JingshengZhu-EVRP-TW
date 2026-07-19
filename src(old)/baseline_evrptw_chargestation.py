import math
from typing import List, Dict, Tuple, Optional


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
        "type": "depot",
    }

    customers = [
        {"id": 1, "x": 20, "y": 60, "demand": 4, "ready_time": 0,   "due_time": 200, "service_time": 10, "type": "customer"},
        {"id": 2, "x": 18, "y": 54, "demand": 3, "ready_time": 20,  "due_time": 220, "service_time": 10, "type": "customer"},
        {"id": 3, "x": 80, "y": 65, "demand": 5, "ready_time": 0,   "due_time": 240, "service_time": 10, "type": "customer"},
        {"id": 4, "x": 75, "y": 20, "demand": 4, "ready_time": 50,  "due_time": 260, "service_time": 10, "type": "customer"},
        {"id": 5, "x": 30, "y": 20, "demand": 2, "ready_time": 30,  "due_time": 180, "service_time": 10, "type": "customer"},
        {"id": 6, "x": 60, "y": 80, "demand": 3, "ready_time": 0,   "due_time": 210, "service_time": 10, "type": "customer"},
    ]

    stations = [
        {"id": 101, "x": 35, "y": 50, "ready_time": 0, "due_time": 1000, "service_time": 0, "demand": 0, "type": "station"},
        {"id": 102, "x": 65, "y": 50, "ready_time": 0, "due_time": 1000, "service_time": 0, "demand": 0, "type": "station"},
        {"id": 103, "x": 50, "y": 25, "ready_time": 0, "due_time": 1000, "service_time": 0, "demand": 0, "type": "station"},
    ]

    vehicle_capacity = 10
    num_vehicles = 4

    # battery settings
    battery_capacity = 70.0
    energy_consumption_rate = 1.0

    return depot, customers, stations, vehicle_capacity, num_vehicles, battery_capacity, energy_consumption_rate


# distance between a and b
def distance(a: Dict, b: Dict) -> float:
    return math.hypot(a["x"] - b["x"], a["y"] - b["y"])

# check battery feasibility between a and b
def can_travel(a: Dict, b: Dict, remaining_battery: float, energy_consumption_rate: float) -> bool:
    return distance(a, b) * energy_consumption_rate <= remaining_battery

# when find this route need more battery, find the nearest reachable station and insert it into the route
def find_nearest_reachable_station(
    current_node: Dict,
    stations: List[Dict],
    remaining_battery: float,
    energy_consumption_rate: float
) -> Optional[Dict]:
    reachable = []
    for station in stations:
        energy_needed = distance(current_node, station) * energy_consumption_rate
        if energy_needed <= remaining_battery:
            reachable.append((distance(current_node, station), station))

    if not reachable:
        return None

    reachable.sort(key=lambda x: x[0])
    return reachable[0][1]


def try_insert_stations_for_route(
    customer_route: List[Dict],
    depot: Dict,
    stations: List[Dict],
    vehicle_capacity: int,
    battery_capacity: float,
    energy_consumption_rate: float
) -> Tuple[bool, List[Dict], Dict]:
    """
    Build a feasible route by inserting charging stations when needed.
    Rules:
    - full recharge at station
    - same station can be revisited
    - if battery is insufficient to next customer, insert nearest reachable station
    - if battery is insufficient to return depot, insert nearest reachable station
    """

    load = sum(node["demand"] for node in customer_route if node["type"] == "customer")
    if load > vehicle_capacity:
        return False, [], {"reason": "capacity exceeded"}

    final_route = []
    schedule = []
    total_distance = 0.0

    current = depot
    current_time = 0.0
    remaining_battery = battery_capacity

    for customer in customer_route:
        # insert station(s) until current -> customer is reachable
        safety_counter = 0
        while not can_travel(current, customer, remaining_battery, energy_consumption_rate):
            safety_counter += 1
            if safety_counter > 20:
                return False, [], {"reason": f"too many station insertions before customer {customer['id']}"}

            station = find_nearest_reachable_station(
                current_node=current,
                stations=stations,
                remaining_battery=remaining_battery,
                energy_consumption_rate=energy_consumption_rate
            )

            if station is None:
                return False, [], {"reason": f"no reachable station before customer {customer['id']}"}

            travel = distance(current, station)
            energy_needed = travel * energy_consumption_rate
            arrival = current_time + travel
            start_service = max(arrival, station["ready_time"])
            departure = start_service + station["service_time"]

            remaining_battery -= energy_needed
            total_distance += travel

            final_route.append(station)
            schedule.append({
                "id": station["id"],
                "type": "station",
                "arrival": round(arrival, 2),
                "start_service": round(start_service, 2),
                "departure": round(departure, 2),
                "battery_after_arrival_before_recharge": round(remaining_battery, 2),
                "battery_after_recharge": round(battery_capacity, 2),
            })

            # full recharge
            remaining_battery = battery_capacity
            current = station
            current_time = departure

        # now current -> customer is reachable
        travel = distance(current, customer)
        energy_needed = travel * energy_consumption_rate
        arrival = current_time + travel
        start_service = max(arrival, customer["ready_time"])

        if start_service > customer["due_time"]:
            return False, [], {"reason": f"time window out of time in customer {customer['id']}"}

        departure = start_service + customer["service_time"]

        if departure > customer["due_time"]:
            return False, [], {"reason": f"time window out of time in customer {customer['id']}"}

        remaining_battery -= energy_needed
        total_distance += travel

        final_route.append(customer)
        schedule.append({
            "id": customer["id"],
            "type": "customer",
            "arrival": round(arrival, 2),
            "start_service": round(start_service, 2),
            "departure": round(departure, 2),
            "battery_after_arrival": round(remaining_battery, 2),
        })

        current = customer
        current_time = departure

    # before returning to depot, insert station(s) if needed
    safety_counter = 0
    while not can_travel(current, depot, remaining_battery, energy_consumption_rate):
        safety_counter += 1
        if safety_counter > 20:
            return False, [], {"reason": "too many station insertions before returning to depot"}

        station = find_nearest_reachable_station(
            current_node=current,
            stations=stations,
            remaining_battery=remaining_battery,
            energy_consumption_rate=energy_consumption_rate
        )

        if station is None:
            return False, [], {"reason": "no reachable station before returning to depot"}

        travel = distance(current, station)
        energy_needed = travel * energy_consumption_rate
        arrival = current_time + travel
        start_service = max(arrival, station["ready_time"])
        departure = start_service + station["service_time"]

        remaining_battery -= energy_needed
        total_distance += travel

        final_route.append(station)
        schedule.append({
            "id": station["id"],
            "type": "station",
            "arrival": round(arrival, 2),
            "start_service": round(start_service, 2),
            "departure": round(departure, 2),
            "battery_after_arrival_before_recharge": round(remaining_battery, 2),
            "battery_after_recharge": round(battery_capacity, 2),
        })

        remaining_battery = battery_capacity
        current = station
        current_time = departure

    # return to depot
    back_distance = distance(current, depot)
    back_energy = back_distance * energy_consumption_rate
    return_time = current_time + back_distance

    if return_time > depot["due_time"]:
        return False, [], {"reason": "return to depot too late"}

    remaining_battery -= back_energy
    total_distance += back_distance

    info = {
        "load": load,
        "total_distance": round(total_distance, 2),
        "schedule": schedule,
        "return_to_depot_time": round(return_time, 2),
        "battery_remaining_at_depot": round(remaining_battery, 2),
    }

    return True, final_route, info


# route check
def check_route(
    route: List[Dict],
    depot: Dict,
    stations: List[Dict],
    vehicle_capacity: int,
    battery_capacity: float,
    energy_consumption_rate: float
) -> Tuple[bool, Dict]:
    feasible, expanded_route, info = try_insert_stations_for_route(
        customer_route=route,
        depot=depot,
        stations=stations,
        vehicle_capacity=vehicle_capacity,
        battery_capacity=battery_capacity,
        energy_consumption_rate=energy_consumption_rate
    )

    if not feasible:
        return False, info

    info["expanded_route"] = expanded_route
    return True, info


# Simple sequential construction heuristic
# Sorted by:
# 1. farther from depot first
# 2. earlier due_time first
def construct_initial_solution(
    customers: List[Dict],
    depot: Dict,
    stations: List[Dict],
    vehicle_capacity: int,
    num_vehicles: int,
    battery_capacity: float,
    energy_consumption_rate: float
):
    """
    Simple baseline:
    - try appending each customer to current route
    - if infeasible, close current route and start a new one
    - charging stations are inserted automatically during feasibility check
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
            stations,
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

            feasible_single, info_single = check_route(
                current_route,
                depot,
                stations,
                vehicle_capacity,
                battery_capacity,
                energy_consumption_rate
            )
            if not feasible_single:
                raise ValueError(f"Customer {customer['id']} cannot be served even alone. Details: {info_single}")

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
    stations: List[Dict],
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
            stations,
            vehicle_capacity,
            battery_capacity,
            energy_consumption_rate
        )
        if not feasible:
            raise ValueError(f"Route {idx} infeasible: {info}")

        expanded_route = info["expanded_route"]
        route_ids = [0] + [node["id"] for node in expanded_route] + [0]

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
            if s["type"] == "customer":
                print(
                    f"    Customer {s['id']}: "
                    f"arrival={s['arrival']}, "
                    f"start={s['start_service']}, "
                    f"departure={s['departure']}, "
                    f"battery_after_arrival={s['battery_after_arrival']}"
                )
            else:
                print(
                    f"    Station {s['id']}: "
                    f"arrival={s['arrival']}, "
                    f"start={s['start_service']}, "
                    f"departure={s['departure']}, "
                    f"battery_before_recharge={s['battery_after_arrival_before_recharge']}, "
                    f"battery_after_recharge={s['battery_after_recharge']}"
                )
        print()


# Main
def main():
    depot, customers, stations, vehicle_capacity, num_vehicles, battery_capacity, energy_consumption_rate = build_instance()

    routes = construct_initial_solution(
        customers=customers,
        depot=depot,
        stations=stations,
        vehicle_capacity=vehicle_capacity,
        num_vehicles=num_vehicles,
        battery_capacity=battery_capacity,
        energy_consumption_rate=energy_consumption_rate
    )

    result = summarize_solution(
        routes=routes,
        depot=depot,
        stations=stations,
        vehicle_capacity=vehicle_capacity,
        battery_capacity=battery_capacity,
        energy_consumption_rate=energy_consumption_rate
    )
    print_solution(result)


if __name__ == "__main__":
    main()
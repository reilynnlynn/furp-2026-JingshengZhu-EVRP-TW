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

    return depot, customers, vehicle_capacity, num_vehicles


# distance between a and b (sqrt of a^2 + b^2)
def distance(a: Dict, b: Dict) -> float:
    return math.hypot(a["x"] - b["x"], a["y"] - b["y"])


# route check 
def check_route(route: List[Dict], depot: Dict, vehicle_capacity: int) -> Tuple[bool, Dict]:
    """
    Check if a route is feasible:
    - load <= capacity  
    - time windows respected (including return to depot)
    """

    # check load and capacity
    load = sum(node["demand"] for node in route)
    if load > vehicle_capacity:
        return False, {"reason": "capacity exceeded"}

    total_distance = 0.0
    schedule = []

    current = depot
    current_time = 0.0
    
    # check time windows for each customer in the route
    for customer in route:
        travel = distance(current, customer)
        arrival = current_time + travel
        start_service = max(arrival, customer["ready_time"])

        if start_service > customer["due_time"]:
            return False, {"reason": f"time window out of time in customer {customer['id']}"}

        departure = start_service + customer["service_time"]

        if departure > customer["due_time"]:
            return False, {"reason": f"time window out of time in customer {customer['id']}"}
        
        total_distance += travel
        schedule.append({
            "id": customer["id"],
            "arrival": arrival,
            "start_service": start_service,
            "departure": departure,
        })

        current = customer
        current_time = departure

    # return to depot
    back_distance = distance(current, depot) if route else 0.0
    return_time = current_time + back_distance
    total_distance += back_distance

    # check depot due time
    if return_time > depot["due_time"]:
        return False, {"reason": "return to depot too late"}

    info = {
        "load": load,
        "total_distance": total_distance,
        "schedule": schedule,
        "return_to_depot_time": return_time,
    }
    return True, info



# Simple sequential construction heuristic
# Sorted by : 1.farther from depot first  2.earlier due_time first
def construct_initial_solution(customers: List[Dict], depot: Dict, vehicle_capacity: int, num_vehicles: int):
    """
    Simple baseline:
    - try appending each customer to current route
    - if infeasible, close current route and start a new one
    """
    
    # sort customers by distance from depot (descending) and due time (ascending)
    customers_sorted = sorted(
        customers,
        key=lambda c: (-distance(depot, c), c["due_time"])
    )

    routes = []
    current_route = []
    
    # if new customer can be added to current route, do it
    # else, close current route and start a new one with this customer
    for customer in customers_sorted:
        trial_route = current_route + [customer]
        feasible, _ = check_route(trial_route, depot, vehicle_capacity)

        if feasible:
            current_route.append(customer)
        else:
            # close current route
            if current_route:
                routes.append(current_route)

            current_route = [customer]

            # check if single-customer route is feasible
            feasible_single, _ = check_route(current_route, depot, vehicle_capacity)
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
def summarize_solution(routes: List[List[Dict]], depot: Dict, vehicle_capacity: int):
    solution = []
    total_distance = 0.0

    for idx, route in enumerate(routes, start=1):
        feasible, info = check_route(route, depot, vehicle_capacity)
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
        print("  Schedule:")
        for s in route_info["schedule"]:
            print(
                f"    Customer {s['id']}: "
                f"arrival={s['arrival']}, "
                f"start={s['start_service']}, "
                f"departure={s['departure']}"
            )
        print()


# Main
def main():
    depot, customers, vehicle_capacity, num_vehicles = build_instance()

    routes = construct_initial_solution(
        customers=customers,
        depot=depot,
        vehicle_capacity=vehicle_capacity,
        num_vehicles=num_vehicles
    )

    result = summarize_solution(routes, depot, vehicle_capacity)
    print_solution(result)


if __name__ == "__main__":
    main()
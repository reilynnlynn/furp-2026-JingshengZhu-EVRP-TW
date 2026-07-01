import os
import math
import time
import csv
import random
import matplotlib.pyplot as plt
from ortools.constraint_solver import pywrapcp, routing_enums_pb2

RESULT_DIR = "../results/week2_compare"

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def euclidean(a, b):
    return int(round(math.hypot(a[0] - b[0], a[1] - b[1])))

def build_instance(seed=42):
    random.seed(seed)

    depot = (50, 50)
    locations = [depot]
    time_windows = [(0, 500)]

    cluster_specs = [
        ((20, 20), (20, 120)),
        ((80, 20), (140, 240)),
        ((50, 80), (260, 360)),
    ]

    customer_id = 1
    for center, tw in cluster_specs:
        cx, cy = center
        for _ in range(6):
            x = cx + random.randint(-8, 8)
            y = cy + random.randint(-8, 8)
            locations.append((x, y))
            start = tw[0] + random.randint(0, 15)
            end = tw[1] + random.randint(0, 15)
            time_windows.append((start, end))
            customer_id += 1

    n = len(locations)
    time_matrix = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            time_matrix[i][j] = euclidean(locations[i], locations[j])

    data = {
        "locations": locations,
        "time_matrix": time_matrix,
        "time_windows": time_windows,
        "num_vehicles": 3,
        "depot": 0,
        "max_visits_per_vehicle": 6,
    }
    return data

def copy_data(data):
    return {
        "locations": list(data["locations"]),
        "time_matrix": [row[:] for row in data["time_matrix"]],
        "time_windows": list(data["time_windows"]),
        "num_vehicles": data["num_vehicles"],
        "depot": data["depot"],
        "max_visits_per_vehicle": data["max_visits_per_vehicle"],
    }

def solve_ortools(data, strategy_name="PATH_CHEAPEST_ARC", use_customer_time_windows=True, time_limit_sec=5):
    manager = pywrapcp.RoutingIndexManager(
        len(data["time_matrix"]),
        data["num_vehicles"],
        data["depot"]
    )
    routing = pywrapcp.RoutingModel(manager)

    def transit_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data["time_matrix"][from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(transit_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    routing.AddDimension(
        transit_callback_index,
        500,
        500,
        False,
        "Time"
    )
    time_dimension = routing.GetDimensionOrDie("Time")

    depot_tw = data["time_windows"][data["depot"]]
    for vehicle_id in range(data["num_vehicles"]):
        start_index = routing.Start(vehicle_id)
        end_index = routing.End(vehicle_id)
        time_dimension.CumulVar(start_index).SetRange(depot_tw[0], depot_tw[1])
        time_dimension.CumulVar(end_index).SetRange(depot_tw[0], depot_tw[1])

    if use_customer_time_windows:
        for node in range(1, len(data["time_windows"])):
            index = manager.NodeToIndex(node)
            tw = data["time_windows"][node]
            time_dimension.CumulVar(index).SetRange(tw[0], tw[1])

    def demand_callback(from_index):
        from_node = manager.IndexToNode(from_index)
        return 0 if from_node == data["depot"] else 1

    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,
        [data["max_visits_per_vehicle"]] * data["num_vehicles"],
        True,
        "Visits"
    )

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    if strategy_name == "PATH_CHEAPEST_ARC":
        search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    elif strategy_name == "PARALLEL_CHEAPEST_INSERTION":
        search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PARALLEL_CHEAPEST_INSERTION
    else:
        search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC

    search_parameters.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    search_parameters.time_limit.seconds = time_limit_sec

    t0 = time.time()
    solution = routing.SolveWithParameters(search_parameters)
    runtime = time.time() - t0

    if solution is None:
        return {
            "method": f"ORTools_{strategy_name}" + ("" if use_customer_time_windows else "_NoCustomerTW"),
            "feasible": False,
            "served_customers": 0,
            "total_customers": len(data["locations"]) - 1,
            "vehicles_used": 0,
            "total_distance": None,
            "runtime_sec": round(runtime, 4),
            "routes": [],
            "arrival_times": [],
        }

    routes = []
    arrival_times = []
    total_distance = 0
    served = set()

    for vehicle_id in range(data["num_vehicles"]):
        index = routing.Start(vehicle_id)
        route = [data["depot"]]
        times = [solution.Value(time_dimension.CumulVar(index))]

        while not routing.IsEnd(index):
            next_index = solution.Value(routing.NextVar(index))
            from_node = manager.IndexToNode(index)
            to_node = manager.IndexToNode(next_index)
            total_distance += data["time_matrix"][from_node][to_node]
            route.append(to_node)
            times.append(solution.Value(time_dimension.CumulVar(next_index)))
            if to_node != data["depot"]:
                served.add(to_node)
            index = next_index

        routes.append(route)
        arrival_times.append(times)

    vehicles_used = sum(1 for r in routes if len(r) > 2)

    return {
        "method": f"ORTools_{strategy_name}" + ("" if use_customer_time_windows else "_NoCustomerTW"),
        "feasible": len(served) == len(data["locations"]) - 1,
        "served_customers": len(served),
        "total_customers": len(data["locations"]) - 1,
        "vehicles_used": vehicles_used,
        "total_distance": total_distance,
        "runtime_sec": round(runtime, 4),
        "routes": routes,
        "arrival_times": arrival_times,
    }

def solve_greedy(data):
    t0 = time.time()

    unserved = set(range(1, len(data["locations"])))
    routes = []
    arrival_times = []
    total_distance = 0

    for _ in range(data["num_vehicles"]):
        route = [0]
        times = [0]
        current = 0
        current_time = 0
        visits = 0

        while visits < data["max_visits_per_vehicle"]:
            feasible_candidates = []

            for customer in unserved:
                travel = data["time_matrix"][current][customer]
                arrival = current_time + travel
                start_service = max(arrival, data["time_windows"][customer][0])
                return_to_depot = start_service + data["time_matrix"][customer][0]

                if start_service <= data["time_windows"][customer][1] and return_to_depot <= data["time_windows"][0][1]:
                    feasible_candidates.append((travel, start_service, customer))

            if not feasible_candidates:
                break

            feasible_candidates.sort(key=lambda x: (x[0], x[1], x[2]))
            travel, start_service, chosen = feasible_candidates[0]

            total_distance += data["time_matrix"][current][chosen]
            current = chosen
            current_time = start_service
            route.append(chosen)
            times.append(current_time)
            unserved.remove(chosen)
            visits += 1

        total_distance += data["time_matrix"][current][0]
        current_time += data["time_matrix"][current][0]
        route.append(0)
        times.append(current_time)

        routes.append(route)
        arrival_times.append(times)

    runtime = time.time() - t0
    served_customers = sum(len(r) - 2 for r in routes if len(r) > 2)
    vehicles_used = sum(1 for r in routes if len(r) > 2)

    return {
        "method": "Greedy_NearestFeasible",
        "feasible": len(unserved) == 0,
        "served_customers": served_customers,
        "total_customers": len(data["locations"]) - 1,
        "vehicles_used": vehicles_used,
        "total_distance": total_distance,
        "runtime_sec": round(runtime, 4),
        "routes": routes,
        "arrival_times": arrival_times,
    }

def plot_routes(data, result, save_path):
    locations = data["locations"]
    routes = result["routes"]

    plt.figure(figsize=(8, 8))
    xs = [p[0] for p in locations]
    ys = [p[1] for p in locations]

    plt.scatter(xs[1:], ys[1:], c="blue", s=50, label="Customers")
    plt.scatter(xs[0], ys[0], c="red", s=150, marker="s", label="Depot")

    for i, (x, y) in enumerate(locations):
        plt.text(x + 0.8, y + 0.8, str(i), fontsize=8)

    colors = ["green", "orange", "purple", "brown", "cyan", "magenta"]

    for vehicle_id, route in enumerate(routes):
        if len(route) <= 1:
            continue
        color = colors[vehicle_id % len(colors)]
        rx = [locations[node][0] for node in route]
        ry = [locations[node][1] for node in route]
        plt.plot(rx, ry, marker="o", linewidth=2, color=color, label=f"Vehicle {vehicle_id}")

    plt.title(result["method"])
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(save_path, dpi=200)
    plt.close()

def save_summary_csv(results, save_path):
    with open(save_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "method",
            "feasible",
            "served_customers",
            "total_customers",
            "vehicles_used",
            "total_distance",
            "runtime_sec"
        ])
        for r in results:
            writer.writerow([
                r["method"],
                r["feasible"],
                r["served_customers"],
                r["total_customers"],
                r["vehicles_used"],
                r["total_distance"],
                r["runtime_sec"]
            ])

def print_result(result):
    print("=" * 70)
    print("Method:", result["method"])
    print("Feasible:", result["feasible"])
    print("Served customers:", f"{result['served_customers']}/{result['total_customers']}")
    print("Vehicles used:", result["vehicles_used"])
    print("Total distance:", result["total_distance"])
    print("Runtime (sec):", result["runtime_sec"])
    for i, route in enumerate(result["routes"]):
        print(f"Vehicle {i}: route={route}")
        if i < len(result["arrival_times"]):
            print(f"Vehicle {i}: times={result['arrival_times'][i]}")

def main():
    ensure_dir(RESULT_DIR)

    data = build_instance(seed=42)

    result_a = solve_ortools(data, strategy_name="PATH_CHEAPEST_ARC", use_customer_time_windows=True, time_limit_sec=5)
    result_b = solve_ortools(data, strategy_name="PARALLEL_CHEAPEST_INSERTION", use_customer_time_windows=True, time_limit_sec=5)
    result_c = solve_greedy(data)

    ablation_data = copy_data(data)
    result_d = solve_ortools(ablation_data, strategy_name="PATH_CHEAPEST_ARC", use_customer_time_windows=False, time_limit_sec=5)

    results = [result_a, result_b, result_c, result_d]

    for r in results:
        print_result(r)

    save_summary_csv(results, os.path.join(RESULT_DIR, "summary.csv"))

    for r in results:
        plot_name = r["method"].replace("/", "_").replace(" ", "_") + ".png"
        plot_routes(data, r, os.path.join(RESULT_DIR, plot_name))

    print("\nSaved files:")
    print(os.path.abspath(RESULT_DIR))

if __name__ == "__main__":
    main()
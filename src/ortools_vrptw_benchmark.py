from ortools.constraint_solver import pywrapcp, routing_enums_pb2
import matplotlib.pyplot as plt
import random
import math
import time
import csv
import os

RESULT_DIR = "results"

STRATEGIES = {
    "PATH_CHEAPEST_ARC": routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC,
    "PARALLEL_CHEAPEST_INSERTION": routing_enums_pb2.FirstSolutionStrategy.PARALLEL_CHEAPEST_INSERTION,
}



def euclidean_distance(a, b):
    """Return integer Euclidean distance used as travel time."""
    dist = int(round(math.hypot(a[0] - b[0], a[1] - b[1])))
    return dist


def build_time_matrix(locations):
    """Build a full travel-time matrix from node coordinates."""
    n = len(locations)
    matrix = []
    for i in range(n):
        row = []
        for j in range(n):
            if i == j:
                row.append(0)
            else:
                d = euclidean_distance(locations[i], locations[j])
                row.append(max(1, d))  # avoid zero travel time between different nodes
        matrix.append(row)
    return matrix


def create_toy_instance(n_customers, seed=42):

    random.seed(seed)

    data = {}

    # Depot at the center
    depot = (50, 50)
    customers = []
    for _ in range(n_customers):
        x = random.randint(0, 100)
        y = random.randint(0, 100)
        customers.append((x, y))

    data["locations"] = [depot] + customers
    data["time_matrix"] = build_time_matrix(data["locations"])
    data["depot"] = 0

    # Use enough vehicles so the toy instances are easier to solve
    # This is okay for a first baseline.
    data["num_vehicles"] = max(3, math.ceil(n_customers / 8))

    # Global time horizon
    # Use a generous horizon to reduce infeasibility.
    horizon = 1000 if n_customers <= 50 else 1500
    data["horizon"] = horizon

    # Build wide time windows

    time_windows = [(0, horizon)]

    # Customer time windows
    for i in range(1, n_customers + 1):
        travel_from_depot = data["time_matrix"][0][i]

        # Earliest time is loosely related to depot distance,
        earliest = max(0, travel_from_depot + random.randint(0, 150))

        # Window width is wide enough for baseline testing
        width = random.randint(300, 600)
        latest = min(horizon, earliest + width)

        time_windows.append((earliest, latest))

    data["time_windows"] = time_windows
    return data


def solve_vrptw(data, strategy_name="PATH_CHEAPEST_ARC", use_time_windows=True, time_limit_s=3):

    manager = pywrapcp.RoutingIndexManager(
        len(data["time_matrix"]),
        data["num_vehicles"],
        data["depot"]
    )

    routing = pywrapcp.RoutingModel(manager)

    def time_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data["time_matrix"][from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(time_callback)

    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Add time dimension even in the ablation case
    routing.AddDimension(
        transit_callback_index,
        data["horizon"],   # maximum waiting time (slack)
        data["horizon"],   # maximum route time
        False,             # do not force start cumul to 0
        "Time"
    )

    time_dimension = routing.GetDimensionOrDie("Time")

    # Add time-window constraints only if enabled
    if use_time_windows:
        for node, window in enumerate(data["time_windows"]):
            if node == data["depot"]:
                continue
            index = manager.NodeToIndex(node)
            time_dimension.CumulVar(index).SetRange(window[0], window[1])

    # Set depot time window for each vehicle start/end
    depot_window = data["time_windows"][data["depot"]]
    for vehicle_id in range(data["num_vehicles"]):
        start_index = routing.Start(vehicle_id)
        end_index = routing.End(vehicle_id)

        time_dimension.CumulVar(start_index).SetRange(depot_window[0], depot_window[1])
        time_dimension.CumulVar(end_index).SetRange(depot_window[0], depot_window[1])

        routing.AddVariableMinimizedByFinalizer(time_dimension.CumulVar(start_index))
        routing.AddVariableMinimizedByFinalizer(time_dimension.CumulVar(end_index))

    # Search parameters
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = STRATEGIES[strategy_name]
    search_parameters.time_limit.FromSeconds(time_limit_s)

    start_time = time.perf_counter()
    solution = routing.SolveWithParameters(search_parameters)
    runtime = time.perf_counter() - start_time

    if not solution:
        return {
            "feasible": False,
            "objective": None,
            "runtime_sec": runtime,
            "vehicles_used": None,
            "routes": None,
            "route_times": None,
            "manager": manager,
            "routing": routing,
            "solution": solution,
        }

    routes = get_routes(data, manager, routing, solution)
    route_times = get_route_times(data, manager, routing, solution)

    vehicles_used = sum(1 for route in routes if len(route) > 2)

    return {
        "feasible": True,
        "objective": solution.ObjectiveValue(),
        "runtime_sec": runtime,
        "vehicles_used": vehicles_used,
        "routes": routes,
        "route_times": route_times,
        "manager": manager,
        "routing": routing,
        "solution": solution,
    }


def get_routes(data, manager, routing, solution):
    """Extract routes as lists of node IDs."""
    routes = []

    for vehicle_id in range(data["num_vehicles"]):
        index = routing.Start(vehicle_id)
        route = []

        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            route.append(node)
            index = solution.Value(routing.NextVar(index))

        route.append(manager.IndexToNode(index))
        routes.append(route)

    return routes


def get_route_times(data, manager, routing, solution):
    """Extract route nodes and arrival times for each vehicle."""
    time_dimension = routing.GetDimensionOrDie("Time")
    route_times = []

    for vehicle_id in range(data["num_vehicles"]):
        index = routing.Start(vehicle_id)
        nodes = []
        times = []

        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            time_var = time_dimension.CumulVar(index)

            nodes.append(node)
            times.append(solution.Min(time_var))

            index = solution.Value(routing.NextVar(index))

        node = manager.IndexToNode(index)
        time_var = time_dimension.CumulVar(index)
        nodes.append(node)
        times.append(solution.Min(time_var))

        route_times.append((nodes, times))

    return route_times


def print_solution(data, result, strategy_name, use_time_windows):
    """Print route details in a readable format."""
    print("=" * 80)
    print(f"Strategy: {strategy_name}")
    print(f"Use time windows: {use_time_windows}")
    print(f"Feasible: {result['feasible']}")

    if not result["feasible"]:
        print("No solution found.")
        print("=" * 80)
        return

    print(f"Objective value: {result['objective']}")
    print(f"Runtime (sec): {result['runtime_sec']:.4f}")
    print(f"Vehicles used: {result['vehicles_used']}")
    print("-" * 80)

    for vehicle_id, (nodes, times) in enumerate(result["route_times"]):
        if len(nodes) <= 2:
            continue
        route_str = " -> ".join(str(n) for n in nodes)
        time_str = " -> ".join(str(t) for t in times)

        print(f"Vehicle {vehicle_id}")
        print(f"  Route: {route_str}")
        print(f"  Arrival times: {time_str}")
        print("-" * 80)

    print("=" * 80)


# --------------------------------------------------
# Plotting
# --------------------------------------------------
def plot_routes(data, routes, save_path, title="VRPTW Route Map"):
    """Plot 2D routes and save the figure."""
    locations = data["locations"]
    depot = data["depot"]
    colors = ["blue", "red", "orange", "purple", "brown", "cyan", "pink", "olive"]

    plt.figure(figsize=(9, 7))

    # Plot all nodes
    for i, (x, y) in enumerate(locations):
        if i == depot:
            plt.scatter(x, y, c="black", s=160, marker="s", label="Depot")
        else:
            plt.scatter(x, y, c="green", s=70)

        plt.text(x + 1, y + 1, str(i), fontsize=8)

    # Plot each non-empty vehicle route
    first_label_used = set()
    for vehicle_id, route in enumerate(routes):
        if len(route) <= 2:
            continue

        xs = [locations[node][0] for node in route]
        ys = [locations[node][1] for node in route]

        label = f"Vehicle {vehicle_id}"
        if label in first_label_used:
            label = None
        else:
            first_label_used.add(label)

        plt.plot(
            xs,
            ys,
            color=colors[vehicle_id % len(colors)],
            linewidth=2,
            marker="o",
            label=label
        )

    plt.title(title)
    plt.xlabel("X coordinate")
    plt.ylabel("Y coordinate")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(save_path, dpi=200)
    plt.close()


def plot_arrival_times(route_times, save_path, title="Arrival Time Along Each Route"):
    """Plot arrival-time line chart and save the figure."""
    plt.figure(figsize=(9, 6))

    for vehicle_id, (nodes, times) in enumerate(route_times):
        if len(nodes) <= 2:
            continue

        x = list(range(len(nodes)))
        plt.plot(
            x,
            times,
            marker="o",
            linewidth=2,
            label=f"Vehicle {vehicle_id}"
        )

        for i, node in enumerate(nodes):
            plt.text(x[i], times[i] + 2, str(node), fontsize=8)

    plt.title(title)
    plt.xlabel("Visit order")
    plt.ylabel("Arrival time")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(save_path, dpi=200)
    plt.close()



def save_results_csv(rows, save_path):
    """Save experiment results to CSV."""
    fieldnames = [
        "instance_size",
        "strategy",
        "use_time_windows",
        "feasible",
        "objective",
        "runtime_sec",
        "vehicles_used"
    ]

    with open(save_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def print_markdown_table(rows):
    """Print a markdown table you can paste into notes/slides."""
    print("\nMarkdown-style result table:\n")
    print("| instance_size | strategy | use_time_windows | feasible | objective | runtime_sec | vehicles_used |")
    print("|---|---|---|---|---|---|---|")
    for row in rows:
        print(
            f"| {row['instance_size']} | {row['strategy']} | {row['use_time_windows']} | "
            f"{row['feasible']} | {row['objective']} | {row['runtime_sec']:.4f} | {row['vehicles_used']} |"
        )


def main():
    os.makedirs(RESULT_DIR, exist_ok=True)

    sizes = [20, 50, 100]

    # Two comparisons + one simple ablation
    experiment_settings = [
        ("PATH_CHEAPEST_ARC", True),
        ("PARALLEL_CHEAPEST_INSERTION", True),
        ("PATH_CHEAPEST_ARC", False),  # simple ablation: remove time-window constraints
    ]

    all_rows = []

    for n_customers in sizes:
        print(f"\nRunning instance with {n_customers} customers...")
        data = create_toy_instance(n_customers=n_customers, seed=100 + n_customers)

        for strategy_name, use_time_windows in experiment_settings:
            result = solve_vrptw(
                data=data,
                strategy_name=strategy_name,
                use_time_windows=use_time_windows,
                time_limit_s=3
            )

            row = {
                "instance_size": n_customers,
                "strategy": strategy_name,
                "use_time_windows": use_time_windows,
                "feasible": result["feasible"],
                "objective": result["objective"],
                "runtime_sec": result["runtime_sec"],
                "vehicles_used": result["vehicles_used"],
            }
            all_rows.append(row)

            print_solution(data, result, strategy_name, use_time_windows)

            # Save figures only for one small instance to keep things simple
            if n_customers == 20 and result["feasible"] and strategy_name == "PATH_CHEAPEST_ARC" and use_time_windows:
                route_fig = os.path.join(RESULT_DIR, "route_map_n20_PATH_CHEAPEST_ARC_TW.png")
                time_fig = os.path.join(RESULT_DIR, "arrival_times_n20_PATH_CHEAPEST_ARC_TW.png")

                plot_routes(
                    data,
                    result["routes"],
                    route_fig,
                    title="VRPTW Route Map (20 customers, PATH_CHEAPEST_ARC, TW)"
                )
                plot_arrival_times(
                    result["route_times"],
                    time_fig,
                    title="Arrival Time Along Each Route (20 customers, PATH_CHEAPEST_ARC, TW)"
                )

    csv_path = os.path.join(RESULT_DIR, "ortools_vrptw_week2_results.csv")
    save_results_csv(all_rows, csv_path)

    print_markdown_table(all_rows)

    print("\nSaved files:")
    print(f"- CSV results: {csv_path}")
    print(f"- Route plot: {os.path.join(RESULT_DIR, 'route_map_n20_PATH_CHEAPEST_ARC_TW.png')}")
    print(f"- Arrival-time plot: {os.path.join(RESULT_DIR, 'arrival_times_n20_PATH_CHEAPEST_ARC_TW.png')}")


if __name__ == "__main__":
    main()
from ortools.constraint_solver import pywrapcp, routing_enums_pb2
import matplotlib.pyplot as plt


def create_data_model():

    data = {}

    # This location data is only for visualization 
    data["locations"] = [
        (50, 50),  # 0: depot
        (20, 60),  # 1
        (80, 60),  # 2
        (20, 20),  # 3
        (80, 20),  # 4
        (50, 80),  # 5
    ]

    # time_matrix[i][j] = travel time from node i to node j
    data["time_matrix"] = [
        [0, 6, 9, 8, 7, 3],
        [6, 0, 5, 4, 3, 7],
        [9, 5, 0, 2, 4, 8],
        [8, 4, 2, 0, 3, 7],
        [7, 3, 4, 3, 0, 6],
        [3, 7, 8, 7, 6, 0],
    ]

    # (earliest_arrival, latest_arrival)
    # e.g. node 1 can only be visited between time 5 and time 15
    data["time_windows"] = [
        (0, 30),   # 0: depot
        (5, 15),   # 1
        (0, 12),   # 2
        (0, 10),   # 3
        (5, 20),   # 4
        (0, 30),   # 5
    ]

    # Number of vehicles
    data["num_vehicles"] = 2

    # Depot node index
    data["depot"] = 0

    return data


def print_solution(data, manager, routing, solution):
    """
    Print the objective value, route of each vehicle, and arrival times.

    Important idea:
    - routing tells us the order of nodes
    - the Time dimension tells us the accumulated arrival time at each node
    """
    print("=" * 60)
    print(f"Objective value (total cost): {solution.ObjectiveValue()}")
    print("=" * 60)

    # Retrieve the time dimension added earlier.
    time_dimension = routing.GetDimensionOrDie("Time")

    total_time = 0

    # Loop through each vehicle
    for vehicle_id in range(data["num_vehicles"]):
        index = routing.Start(vehicle_id)
        route_output = f"Route for vehicle {vehicle_id}:\n"
        route_time = 0

        # Follow the route until the end node is reached
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)

            # CumulVar(index) is the accumulated time variable at this route index
            time_var = time_dimension.CumulVar(index)

            route_output += (
                f"Node {node_index} "
                f"Time[{solution.Min(time_var)}, {solution.Max(time_var)}] -> "
            )

            previous_index = index
            index = solution.Value(routing.NextVar(index))

            # Add travel time to route_time for rough reporting
            prev_node = manager.IndexToNode(previous_index)
            next_node = manager.IndexToNode(index)
            route_time += data["time_matrix"][prev_node][next_node]

        # Print the end node
        node_index = manager.IndexToNode(index)
        time_var = time_dimension.CumulVar(index)
        route_output += (
            f"Node {node_index} "
            f"Time[{solution.Min(time_var)}, {solution.Max(time_var)}]\n"
        )
        route_output += f"Approximate travel time of the route: {route_time}\n"

        print(route_output)
        total_time += route_time

    print(f"Approximate total travel time: {total_time}")
    print("=" * 60)


def get_routes(data, manager, routing, solution):
    """
    Extract routes from the OR-Tools solution.

    Returns:
        routes: a list of routes
                each route is a list of node IDs
                example: [[0, 1, 3, 0], [0, 5, 2, 4, 0]]
    """
    routes = []

    for vehicle_id in range(data["num_vehicles"]):
        index = routing.Start(vehicle_id)
        route = []

        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            route.append(node)
            index = solution.Value(routing.NextVar(index))

        # Add the end node
        route.append(manager.IndexToNode(index))
        routes.append(route)

    return routes


def get_route_times(data, manager, routing, solution):
    """
    Extract both visited nodes and arrival times for each vehicle.

    Returns:
        route_times: a list where each element is (nodes, times)
                     nodes = [0, 5, 2, 0]
                     times = [0, 3, 11, 20]
    """
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

        # Add the end node
        node = manager.IndexToNode(index)
        time_var = time_dimension.CumulVar(index)
        nodes.append(node)
        times.append(solution.Min(time_var))

        route_times.append((nodes, times))

    return route_times


def plot_routes(data, routes):
    """
    Plot the route map.

    - Depot is shown as a black square
    - Customers are green points
    - Each vehicle route has a different color
    """
    locations = data["locations"]
    depot = data["depot"]
    colors = ["blue", "red", "orange", "purple", "brown", "cyan"]

    plt.figure(figsize=(8, 6))

    # Plot all nodes
    for i, (x, y) in enumerate(locations):
        if i == depot:
            plt.scatter(x, y, c="black", s=140, marker="s", label="Depot")
        else:
            plt.scatter(x, y, c="green", s=90)

        # Show node index next to the point
        plt.text(x + 1, y + 1, str(i), fontsize=10)

    # Plot each vehicle route
    for vehicle_id, route in enumerate(routes):
        xs = [locations[node][0] for node in route]
        ys = [locations[node][1] for node in route]

        plt.plot(
            xs,
            ys,
            color=colors[vehicle_id % len(colors)],
            linewidth=2,
            marker="o",
            label=f"Vehicle {vehicle_id}"
        )

    plt.title("VRPTW Route Map")
    plt.xlabel("X coordinate")
    plt.ylabel("Y coordinate")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()


def plot_arrival_times(route_times):
    """
    Plot the arrival time line chart.

    X-axis:
        visit order in the route
    Y-axis:
        arrival time

    This helps visualize how time accumulates along each route.
    """
    plt.figure(figsize=(8, 5))

    for vehicle_id, (nodes, times) in enumerate(route_times):
        x = list(range(len(nodes)))

        plt.plot(
            x,
            times,
            marker="o",
            linewidth=2,
            label=f"Vehicle {vehicle_id}"
        )

        # Annotate each point with the node index
        for i, node in enumerate(nodes):
            plt.text(x[i], times[i] + 0.3, str(node), fontsize=9)

    plt.title("Arrival Time Along Each Route")
    plt.xlabel("Visit order")
    plt.ylabel("Arrival time")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()


def main():
    """
    Main workflow:
    1. Create data
    2. Create manager
    3. Create routing model
    4. Register time callback
    5. Set travel cost
    6. Add time dimension
    7. Add time window constraints
    8. Solve
    9. Print and plot results
    """
    # 1. Create problem data
    data = create_data_model()

    # 2. Create the index manager
    manager = pywrapcp.RoutingIndexManager(
        len(data["time_matrix"]),
        data["num_vehicles"],
        data["depot"]
    )

    # 3. Create routing model
    routing = pywrapcp.RoutingModel(manager)

    # 4. Define transit callback
    # This callback returns the travel time from one node to another.
    def time_callback(from_index, to_index):
        """
        Convert OR-Tools internal indices to node indices,
        then return the travel time from the time matrix.
        """
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data["time_matrix"][from_node][to_node]

    # Register the callback and get its internal callback index
    transit_callback_index = routing.RegisterTransitCallback(time_callback)

    # 5. Set arc cost
    # This tells OR-Tools:
    # "When evaluating route quality, use travel time as route cost."
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
    # 6. Add Time dimension
    # Parameters:
    # transit_callback_index : how time increases between nodes
    # 30                     : maximum waiting time (slack)
    # 30                     : maximum route time per vehicle
    # False                  : do not force start time to be exactly zero
    # "Time"                 : name of this dimension
    routing.AddDimension(
        transit_callback_index,
        30,
        30,
        False,
        "Time"
    )

    # Retrieve the Time dimension object
    time_dimension = routing.GetDimensionOrDie("Time")

    # 7. Add time window constraints
    # For each customer node, constrain its arrival time to be within its time window.
    for node, time_window in enumerate(data["time_windows"]):
        if node == data["depot"]:
            continue

        index = manager.NodeToIndex(node)
        time_dimension.CumulVar(index).SetRange(time_window[0], time_window[1])

    # Also set the depot time window for each vehicle start node
    depot_window = data["time_windows"][data["depot"]]
    for vehicle_id in range(data["num_vehicles"]):
        start_index = routing.Start(vehicle_id)
        time_dimension.CumulVar(start_index).SetRange(
            depot_window[0], depot_window[1]
        )

    # 8. Finalizer settings
    # These lines help the solver produce cleaner start/end times.
    for vehicle_id in range(data["num_vehicles"]):
        routing.AddVariableMinimizedByFinalizer(
            time_dimension.CumulVar(routing.Start(vehicle_id))
        )
        routing.AddVariableMinimizedByFinalizer(
            time_dimension.CumulVar(routing.End(vehicle_id))
        )

    # 9. Search parameters
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()

    # A common first solution strategy:
    # build a route by repeatedly choosing the cheapest next arc
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )

    # 10. Solve
    solution = routing.SolveWithParameters(search_parameters)

    # 11. Output results
    if solution:
        print_solution(data, manager, routing, solution)

        routes = get_routes(data, manager, routing, solution)
        route_times = get_route_times(data, manager, routing, solution)

        print("Extracted routes:", routes)
        print("Extracted route times:", route_times)

        plot_routes(data, routes)
        plot_arrival_times(route_times)
    else:
        print("No solution found.")


if __name__ == "__main__":
    main()
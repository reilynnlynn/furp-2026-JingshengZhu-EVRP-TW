from ortools.constraint_solver import pywrapcp, routing_enums_pb2


def create_data_model():
    data = {}

    data["time_matrix"] = [
        [0, 6, 9, 8, 7, 3],
        [6, 0, 5, 4, 3, 7],
        [9, 5, 0, 2, 4, 8],
        [8, 4, 2, 0, 3, 7],
        [7, 3, 4, 3, 0, 6],
        [3, 7, 8, 7, 6, 0],
    ]

    data["time_windows"] = [
        (0, 30),
        (5, 15),
        (0, 12),
        (0, 10),
        (5, 20),
        (0, 30),
    ]

    data["num_vehicles"] = 2
    data["depot"] = 0
    return data


def print_solution(data, manager, routing, solution):
    total_time = 0

    for vehicle_id in range(data["num_vehicles"]):
        index = routing.Start(vehicle_id)
        route_output = [f"Vehicle {vehicle_id + 1}"]

        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            time_var = time_dimension.CumulVar(index)
            arrival = solution.Min(time_var)
            route_output.append(f"  Node {node} at time {arrival}")
            index = solution.Value(routing.NextVar(index))

        node = manager.IndexToNode(index)
        time_var = time_dimension.CumulVar(index)
        arrival = solution.Min(time_var)
        route_output.append(f"  Node {node} at time {arrival}")

        route_time = solution.Min(time_var)
        total_time += route_time

        print("\n".join(route_output))
        print(f"  Route end time: {route_time}\n")

    print(f"Total end-time sum: {total_time}")


data = create_data_model()

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

routing.AddDimension(
    transit_callback_index,
    30,
    30,
    False,
    "Time"
)

time_dimension = routing.GetDimensionOrDie("Time")

for node, time_window in enumerate(data["time_windows"]):
    if node == data["depot"]:
        continue
    index = manager.NodeToIndex(node)
    time_dimension.CumulVar(index).SetRange(time_window[0], time_window[1])

depot_index_0 = routing.Start(0)
depot_index_1 = routing.Start(1)
time_dimension.CumulVar(depot_index_0).SetRange(
    data["time_windows"][0][0], data["time_windows"][0][1]
)
time_dimension.CumulVar(depot_index_1).SetRange(
    data["time_windows"][0][0], data["time_windows"][0][1]
)

for vehicle_id in range(data["num_vehicles"]):
    routing.AddVariableMinimizedByFinalizer(
        time_dimension.CumulVar(routing.Start(vehicle_id))
    )
    routing.AddVariableMinimizedByFinalizer(
        time_dimension.CumulVar(routing.End(vehicle_id))
    )

search_parameters = pywrapcp.DefaultRoutingSearchParameters()
search_parameters.first_solution_strategy = (
    routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
)

solution = routing.SolveWithParameters(search_parameters)

if solution:
    print_solution(data, manager, routing, solution)
else:
    print("No solution found.")
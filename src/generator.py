import random

from src.instance import EVRPTWInstance, Node


def generate_random_evrptw_instance(
    name: str = "random_10_3",
    num_customers: int = 10,
    num_stations: int = 3,
    vehicle_count: int = 3,
    vehicle_capacity: float = 100.0,
    battery_capacity: float = 120.0,
    energy_consumption_rate: float = 1.0,
    charging_rate: float = 1.0,
    coordinate_limit: float = 100.0,
    demand_min: float = 5.0,
    demand_max: float = 20.0,
    time_window_start_min: float = 0.0,
    time_window_start_max: float = 300.0,
    time_window_width_min: float = 80.0,
    time_window_width_max: float = 200.0,
    service_time_min: float = 5.0,
    service_time_max: float = 20.0,
    seed: int | None = 42222,
) -> EVRPTWInstance:
    """
    Generate a random EVRPTW instance.

    Node ID convention:
        0: depot
        1..num_customers: customers
        num_customers+1 .. num_customers+num_stations: charging stations
    """

    rng = random.Random(seed)
    nodes: list[Node] = []

    depot = Node(
        id=0,
        x=coordinate_limit / 2,
        y=coordinate_limit / 2,
        node_type="depot",
        demand=0.0,
        ready_time=0.0,
        due_time=1_000.0,
        service_time=0.0,
    )
    nodes.append(depot)

    for i in range(1, num_customers + 1):
        ready_time = rng.uniform(time_window_start_min, time_window_start_max)
        width = rng.uniform(time_window_width_min, time_window_width_max)
        due_time = ready_time + width

        customer = Node(
            id=i,
            x=rng.uniform(0.0, coordinate_limit),
            y=rng.uniform(0.0, coordinate_limit),
            node_type="customer",
            demand=rng.uniform(demand_min, demand_max),
            ready_time=ready_time,
            due_time=due_time,
            service_time=rng.uniform(service_time_min, service_time_max),
        )
        nodes.append(customer)

    for j in range(num_stations):
        station_id = num_customers + 1 + j
        station = Node(
            id=station_id,
            x=rng.uniform(0.0, coordinate_limit),
            y=rng.uniform(0.0, coordinate_limit),
            node_type="station",
            demand=0.0,
            ready_time=0.0,
            due_time=1_000.0,
            service_time=0.0,
        )
        nodes.append(station)

    return EVRPTWInstance(
        name=name,
        nodes=nodes,
        depot_id=0,
        vehicle_count=vehicle_count,
        vehicle_capacity=vehicle_capacity,
        battery_capacity=battery_capacity,
        energy_consumption_rate=energy_consumption_rate,
        charging_rate=charging_rate,
    )
from src.instance import Node, EVRPTWInstance


def main() -> None:
    nodes = [
        Node(
            id=0,
            x=50.0,
            y=50.0,
            node_type="depot",
            ready_time=0.0,
            due_time=1000.0,
        ),
        Node(
            id=1,
            x=20.0,
            y=30.0,
            node_type="customer",
            demand=10.0,
            ready_time=0.0,
            due_time=500.0,
            service_time=10.0,
        ),
        Node(
            id=2,
            x=70.0,
            y=60.0,
            node_type="customer",
            demand=15.0,
            ready_time=100.0,
            due_time=600.0,
            service_time=10.0,
        ),
        Node(
            id=100,
            x=40.0,
            y=40.0,
            node_type="station",
            ready_time=0.0,
            due_time=1000.0,
        ),
    ]

    instance = EVRPTWInstance(
        name="demo_instance",
        nodes=nodes,
        depot_id=0,
        vehicle_count=2,
        vehicle_capacity=50.0,
        battery_capacity=100.0,
        energy_consumption_rate=1.0,
        charging_rate=0.5,
        vehicle_speed=1.0,
    )

    print("Instance name:", instance.name)
    print("Depot:", instance.depot)
    print("Customers:", instance.customers)
    print("Stations:", instance.stations)
    print("Node 2:", instance.get_node(2))


if __name__ == "__main__":
    main()
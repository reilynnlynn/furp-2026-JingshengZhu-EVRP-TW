from src.checker import check_solution
from src.decoders.multiroute_decoder import decode_customer_order_to_multiroute_solution
from src.evaluator import evaluate_solution
from src.generator import generate_random_evrptw_instance


def main() -> None:
    instance = generate_random_evrptw_instance(
        name="week2_multiroute_demo_50",
        num_customers=50,
        num_stations=5,
        vehicle_count=15,
        vehicle_capacity=80.0,
        battery_capacity=500.0,
        coordinate_limit=100.0,
        time_window_start_min=0.0,
        time_window_start_max=100.0,
        time_window_width_min=300.0,
        time_window_width_max=600.0,
        seed=42,
    )

    customer_order = [
        node.id for node in instance.nodes if node.node_type == "customer"
    ]

    solution, report = decode_customer_order_to_multiroute_solution(instance, customer_order)
    check_result = check_solution(instance, solution)
    evaluation = evaluate_solution(instance, solution)

    print("=== Multi-route Decoder Demo ===")
    print(f"Instance: {instance.name}")
    print(f"Customers: {len([n for n in instance.nodes if n.node_type == 'customer'])}")
    print(f"Charging stations: {len([n for n in instance.nodes if n.node_type == 'station'])}")
    print(f"Vehicle count limit: {instance.vehicle_count}")
    print(f"Vehicle capacity: {instance.vehicle_capacity}")
    print(f"Battery capacity: {instance.battery_capacity}")
    print(f"Decoder success: {report.success}")
    print(f"Decoder message: {report.message}")
    print(f"Assigned customers: {len(report.assigned_customers)}")
    print(f"Unassigned customers: {len(report.unassigned_customers)}")
    print(f"Route count: {report.route_count}")
    print(f"Checker feasible: {check_result.feasible}")
    print(f"Checker messages: {check_result.messages}")
    print(f"Total distance: {evaluation.total_distance:.2f}")

    print("\nFirst 10 routes:")
    for idx, route in enumerate(solution.routes[:10], start=1):
        print(f"  Route {idx}: {route.node_ids}")

    if report.split_reasons:
        print("\nFirst 10 route split reasons:")
        for reason in report.split_reasons[:10]:
            print(f"  - {reason}")


if __name__ == "__main__":
    main()
from src.checker import check_solution
from src.decoders.multiroute_decoder import decode_customer_order_to_multiroute_solution
from src.generator import generate_random_evrptw_instance


def test_multiroute_decoder_assigns_all_customers_on_relaxed_instance():
    instance = generate_random_evrptw_instance(
        name="decoder_test_relaxed",
        num_customers=12,
        num_stations=2,
        vehicle_count=6,
        vehicle_capacity=200.0,
        battery_capacity=1000.0,
        coordinate_limit=100.0,
        time_window_start_min=0.0,
        time_window_start_max=0.0,
        time_window_width_min=1000.0,
        time_window_width_max=1000.0,
        seed=1,
    )

    customer_order = [
        node.id for node in instance.nodes if node.node_type == "customer"
    ]

    solution, report = decode_customer_order_to_multiroute_solution(instance, customer_order)
    check_result = check_solution(instance, solution)

    assert report.success is True
    assert sorted(report.assigned_customers) == sorted(customer_order)
    assert report.unassigned_customers == []
    assert report.route_count >= 1
    assert check_result.feasible is True


def test_multiroute_decoder_creates_multiple_routes_when_capacity_is_small():
    instance = generate_random_evrptw_instance(
        name="decoder_test_capacity",
        num_customers=12,
        num_stations=2,
        vehicle_count=12,
        vehicle_capacity=25.0,
        battery_capacity=1000.0,
        coordinate_limit=100.0,
        demand_min=10.0,
        demand_max=10.0,
        time_window_start_min=0.0,
        time_window_start_max=0.0,
        time_window_width_min=1000.0,
        time_window_width_max=1000.0,
        seed=2,
    )

    customer_order = [
        node.id for node in instance.nodes if node.node_type == "customer"
    ]

    solution, report = decode_customer_order_to_multiroute_solution(instance, customer_order)
    check_result = check_solution(instance, solution)

    assert report.success is True
    assert report.route_count >= 2
    assert check_result.feasible is True


def test_multiroute_decoder_reports_unassigned_when_vehicle_count_is_too_small():
    instance = generate_random_evrptw_instance(
        name="decoder_test_vehicle_limit",
        num_customers=20,
        num_stations=2,
        vehicle_count=1,
        vehicle_capacity=20.0,
        battery_capacity=1000.0,
        coordinate_limit=100.0,
        demand_min=10.0,
        demand_max=10.0,
        time_window_start_min=0.0,
        time_window_start_max=0.0,
        time_window_width_min=1000.0,
        time_window_width_max=1000.0,
        seed=3,
    )

    customer_order = [
        node.id for node in instance.nodes if node.node_type == "customer"
    ]

    _solution, report = decode_customer_order_to_multiroute_solution(
        instance,
        customer_order,
        allow_partial=False,
    )

    assert report.success is False
    assert len(report.unassigned_customers) > 0
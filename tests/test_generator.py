from src.generator import generate_random_evrptw_instance


def test_generate_random_evrptw_instance_basic():
    instance = generate_random_evrptw_instance(
        num_customers=10,
        num_stations=3,
        seed=42,
    )

    assert len(instance.customers) == 10
    assert len(instance.stations) == 3
    assert instance.depot.id == 0
    assert instance.vehicle_capacity > 0
    assert instance.battery_capacity > 0
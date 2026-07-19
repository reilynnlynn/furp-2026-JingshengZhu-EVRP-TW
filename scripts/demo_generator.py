from src.generator import generate_random_evrptw_instance


def main() -> None:
    instance = generate_random_evrptw_instance(seed=433)

    print("Instance name:", instance.name)
    print("Vehicle count:", instance.vehicle_count)
    print("Number of nodes:", len(instance.nodes))
    print("Number of customers:", len(instance.customers))
    print("Number of stations:", len(instance.stations))

    print("\nFirst 3 customers:")
    for customer in instance.customers[:3]:
        print(customer)


if __name__ == "__main__":
    main()
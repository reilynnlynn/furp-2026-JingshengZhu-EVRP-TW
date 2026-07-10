from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
sys.path.append(str(SRC_PATH))

from src.generator import generate_random_evrptw_instance
from src.io import save_instance_to_json


def main() -> None:
    instance = generate_random_evrptw_instance(
        name="random_10_customers_3_stations",
        num_customers=10,
        num_stations=3,
        vehicle_count=3,
        seed=42,
    )

    output_path = PROJECT_ROOT / "data" / "instances" / "random_10_3.json"
    save_instance_to_json(instance, output_path)

    print("Generated instance:")
    print(f"  name: {instance.name}")
    print(f"  customers: {len(instance.customers)}")
    print(f"  charging stations: {len(instance.stations)}")
    print(f"  vehicles: {instance.vehicle_count}")
    print(f"  capacity: {instance.vehicle_capacity}")
    print(f"  battery capacity: {instance.battery_capacity}")
    print(f"  saved to: {output_path}")


if __name__ == "__main__":
    main()
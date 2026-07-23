"""

Benchmark sizes:
    - 20 customers: small sanity-check instances
    - 50 customers: medium instances
    - 100 customers: larger instances for scalability evaluation

"""

from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
from typing import Any

from src.generator import generate_random_evrptw_instance
from src.instance import EVRPTWInstance, Node


WEEK3_SIZES: list[int] = [20, 50, 100]
WEEK3_SEEDS: list[int] = [1, 2, 3]

DEFAULT_WEEK3_OUTPUT_DIR = Path("data/week3_benchmarks")


def get_week3_vehicle_count(num_customers: int) -> int:
    """
    Return the vehicle count used for a given benchmark size.

    The vehicle count is intentionally scaled with the number of customers.
    If vehicle_count is too small, almost all large instances become infeasible
    simply because there are not enough routes available. That would make the
    comparison less meaningful.

    Args:
        num_customers:
            Number of customer nodes.

    Returns:
        Number of available vehicles.
    """

    if num_customers <= 20:
        return 5
    if num_customers <= 50:
        return 10
    return 20


def get_week3_station_count(num_customers: int) -> int:
    """
    Return the charging station count used for a given benchmark size.

    EVRP-TW instances need charging stations. Larger instances receive more
    charging stations so that battery feasibility is not impossible by design.

    Args:
        num_customers:
            Number of customer nodes.

    Returns:
        Number of charging stations.
    """

    if num_customers <= 20:
        return 4
    if num_customers <= 50:
        return 8
    return 15


def generate_week3_instance(
    num_customers: int,
    seed: int,
) -> EVRPTWInstance:
    """
    Generate one fixed Week 3 EVRP-TW benchmark instance.

    Important design choices:
        - Same generator function as the rest of the project.
        - Explicit seed for reproducibility.
        - Scaled vehicle_count and charging station count.
        - Moderately relaxed time windows so that feasibility is possible but
          still non-trivial.
        - Battery capacity is large enough for local movements but not so large
          that charging becomes irrelevant.

    Args:
        num_customers:
            Number of customers.
        seed:
            Random seed.

    Returns:
        EVRPTWInstance.
    """

    vehicle_count = get_week3_vehicle_count(num_customers)
    num_stations = get_week3_station_count(num_customers)

    return generate_random_evrptw_instance(
        name=f"week3_c{num_customers}_s{seed}",
        num_customers=num_customers,
        num_stations=num_stations,
        vehicle_count=vehicle_count,
        vehicle_capacity=100.0,
        battery_capacity=120.0,
        energy_consumption_rate=1.0,
        charging_rate=1.0,
        coordinate_limit=100.0,
        demand_min=5.0,
        demand_max=20.0,
        time_window_start_min=0.0,
        time_window_start_max=300.0,
        time_window_width_min=120.0,
        time_window_width_max=260.0,
        service_time_min=5.0,
        service_time_max=20.0,
        seed=seed,
    )


def instance_to_dict(instance: EVRPTWInstance) -> dict[str, Any]:
    """
    Convert an EVRPTWInstance object to a JSON-serializable dictionary.

    Args:
        instance:
            EVRPTWInstance object.

    Returns:
        JSON-serializable dictionary.
    """

    return asdict(instance)


def node_from_dict(data: dict[str, Any]) -> Node:
    """
    Convert a dictionary back to a Node object.

    Args:
        data:
            Node dictionary.

    Returns:
        Node object.
    """

    return Node(
        id=int(data["id"]),
        x=float(data["x"]),
        y=float(data["y"]),
        node_type=data["node_type"],
        demand=float(data.get("demand", 0.0)),
        ready_time=float(data.get("ready_time", 0.0)),
        due_time=float(data.get("due_time", 1_000.0)),
        service_time=float(data.get("service_time", 0.0)),
    )


def instance_from_dict(data: dict[str, Any]) -> EVRPTWInstance:
    """
    Convert a dictionary back to an EVRPTWInstance object.

    Args:
        data:
            Instance dictionary.

    Returns:
        EVRPTWInstance object.
    """

    nodes = [node_from_dict(node_data) for node_data in data["nodes"]]

    return EVRPTWInstance(
        name=str(data["name"]),
        nodes=nodes,
        depot_id=int(data["depot_id"]),
        vehicle_count=int(data["vehicle_count"]),
        vehicle_capacity=float(data["vehicle_capacity"]),
        battery_capacity=float(data["battery_capacity"]),
        energy_consumption_rate=float(data["energy_consumption_rate"]),
        charging_rate=float(data["charging_rate"]),
        vehicle_speed=float(data.get("vehicle_speed", 1.0)),
    )


def save_instance_json(instance: EVRPTWInstance, path: str | Path) -> None:
    """
    Save an EVRP-TW instance to a JSON file.

    Args:
        instance:
            Instance to save.
        path:
            Output JSON path.
    """

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(instance_to_dict(instance), file, indent=2)


def load_instance_json(path: str | Path) -> EVRPTWInstance:
    """
    Load an EVRP-TW instance from a JSON file.

    Args:
        path:
            Input JSON path.

    Returns:
        EVRPTWInstance.
    """

    input_path = Path(path)

    with input_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return instance_from_dict(data)


def week3_instance_filename(num_customers: int, seed: int) -> str:
    """
    Return the standard filename for a Week 3 benchmark instance.

    Args:
        num_customers:
            Number of customers.
        seed:
            Random seed.

    Returns:
        JSON filename.
    """

    return f"week3_c{num_customers}_s{seed}.json"


def generate_and_save_week3_benchmarks(
    output_dir: str | Path = DEFAULT_WEEK3_OUTPUT_DIR,
    sizes: list[int] | None = None,
    seeds: list[int] | None = None,
) -> list[Path]:
    """
    Generate and save all Week 3 benchmark instances.

    Args:
        output_dir:
            Directory where JSON files are saved.
        sizes:
            Customer sizes. Defaults to WEEK3_SIZES.
        seeds:
            Random seeds. Defaults to WEEK3_SEEDS.

    Returns:
        List of generated JSON paths.
    """

    output_path = Path(output_dir)
    selected_sizes = sizes if sizes is not None else WEEK3_SIZES
    selected_seeds = seeds if seeds is not None else WEEK3_SEEDS

    generated_paths: list[Path] = []

    for num_customers in selected_sizes:
        for seed in selected_seeds:
            instance = generate_week3_instance(
                num_customers=num_customers,
                seed=seed,
            )

            file_path = output_path / week3_instance_filename(
                num_customers=num_customers,
                seed=seed,
            )

            save_instance_json(instance, file_path)
            generated_paths.append(file_path)

    return generated_paths


def summarize_instance(instance: EVRPTWInstance) -> dict[str, Any]:
    """
    Create a simple summary of one instance.

    Args:
        instance:
            EVRPTWInstance object.

    Returns:
        Summary dictionary.
    """

    return {
        "name": instance.name,
        "customers": len(instance.customers),
        "stations": len(instance.stations),
        "vehicles": instance.vehicle_count,
        "vehicle_capacity": instance.vehicle_capacity,
        "battery_capacity": instance.battery_capacity,
        "energy_consumption_rate": instance.energy_consumption_rate,
        "charging_rate": instance.charging_rate,
        "vehicle_speed": instance.vehicle_speed,
    }
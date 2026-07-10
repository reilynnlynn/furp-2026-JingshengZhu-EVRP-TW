import json
from dataclasses import asdict
from pathlib import Path

from src.instance import EVRPTWInstance, Node


def save_instance_to_json(instance: EVRPTWInstance, path: str | Path) -> None:
    """Save an EVRPTW instance to a JSON file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "name": instance.name,
        "nodes": [asdict(node) for node in instance.nodes],
        "depot_id": instance.depot_id,
        "vehicle_count": instance.vehicle_count,
        "vehicle_capacity": instance.vehicle_capacity,
        "battery_capacity": instance.battery_capacity,
        "energy_consumption_rate": instance.energy_consumption_rate,
        "charging_rate": instance.charging_rate,
        "vehicle_speed": instance.vehicle_speed,
    }

    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_instance_from_json(path: str | Path) -> EVRPTWInstance:
    """Load an EVRPTW instance from a JSON file."""
    path = Path(path)

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    nodes = [Node(**node_data) for node_data in data["nodes"]]

    return EVRPTWInstance(
        name=data["name"],
        nodes=nodes,
        depot_id=data["depot_id"],
        vehicle_count=data["vehicle_count"],
        vehicle_capacity=data["vehicle_capacity"],
        battery_capacity=data["battery_capacity"],
        energy_consumption_rate=data["energy_consumption_rate"],
        charging_rate=data["charging_rate"],
        vehicle_speed=data.get("vehicle_speed", 1.0),
    )
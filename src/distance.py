import math

from src.instance import Node


def euclidean_distance(node_a: Node, node_b: Node) -> float:
    """Compute Euclidean distance between two nodes."""
    dx = node_a.x - node_b.x
    dy = node_a.y - node_b.y
    return math.sqrt(dx * dx + dy * dy)


def travel_time(node_a: Node, node_b: Node, speed: float = 1.0) -> float:
    """Compute travel time between two nodes."""
    if speed <= 0:
        raise ValueError("Speed must be positive.")
    return euclidean_distance(node_a, node_b) / speed


def energy_consumption(
    node_a: Node,
    node_b: Node,
    energy_consumption_rate: float,
) -> float:
    """Compute energy consumption between two nodes."""
    return euclidean_distance(node_a, node_b) * energy_consumption_rate
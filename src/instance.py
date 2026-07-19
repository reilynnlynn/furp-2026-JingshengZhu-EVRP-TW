from dataclasses import dataclass
from typing import Literal


NodeType = Literal["depot", "customer", "station"]


@dataclass(frozen=True)
class Node:
    """
    A node in the EVRPTW instance.

    Attributes:
        id: Unique node identifier.
        x: X-coordinate.
        y: Y-coordinate.
        node_type: depot, customer, or station.
        demand: Customer demand. Depot and stations usually have demand 0.
        ready_time: Earliest service start time.
        due_time: Latest service start time.
        service_time: Service duration.
    """

    id: int
    x: float
    y: float
    node_type: NodeType
    demand: float = 0.0
    ready_time: float = 0.0
    due_time: float = 1_000.0
    service_time: float = 0.0


@dataclass(frozen=True)
class EVRPTWInstance:
    """
    EVRPTW instance definition.

    Attributes:
        name: Instance name.
        nodes: All nodes including depot, customers and charging stations.
        depot_id: ID of the depot.
        vehicle_count: Number of available vehicles.
        vehicle_capacity: Maximum vehicle load capacity.
        battery_capacity: Maximum battery capacity.
        energy_consumption_rate: Energy consumed per unit distance.
        charging_rate: Time required to charge one unit of energy.
        vehicle_speed: Travel speed. If speed = 1, travel time equals distance.
    """

    name: str
    nodes: list[Node]
    depot_id: int
    vehicle_count: int
    vehicle_capacity: float
    battery_capacity: float
    energy_consumption_rate: float
    charging_rate: float
    vehicle_speed: float = 1.0

    @property
    def depot(self) -> Node:
        for node in self.nodes:
            if node.id == self.depot_id:
                return node
        raise ValueError(f"Depot with id {self.depot_id} not found.")

    @property
    def customers(self) -> list[Node]:
        return [node for node in self.nodes if node.node_type == "customer"]

    @property
    def stations(self) -> list[Node]:
        return [node for node in self.nodes if node.node_type == "station"]

    def get_node(self, node_id: int) -> Node:
        for node in self.nodes:
            if node.id == node_id:
                return node
        raise ValueError(f"Node with id {node_id} not found.")
from dataclasses import dataclass


@dataclass
class Route:
    """A single vehicle route represented by a sequence of node IDs.

    Example:
        [0, 1, 2, 0] means:
        depot -> customer 1 -> customer 2 -> depot
    """

    node_ids: list[int]

    @property
    def customer_ids(self) -> list[int]:
        """Return customer node IDs in this route.

        For now, we assume depot has ID 0.
        Charging stations should not be counted as customers.
        This simple version only removes depot 0.
        A more precise version will use the instance information later.
        """
        return [node_id for node_id in self.node_ids if node_id != 0]


@dataclass
class Solution:
    """A complete EVRPTW solution containing multiple vehicle routes."""

    routes: list[Route]

    @property
    def all_visited_node_ids(self) -> list[int]:
        """Return all node IDs visited by all routes."""
        node_ids = []
        for route in self.routes:
            node_ids.extend(route.node_ids)
        return node_ids

    @property
    def all_visited_customer_ids(self) -> list[int]:
        """Return all customer IDs visited by all routes.

        This simple version treats every non-zero node as a customer.
        Later, checker.py will use instance information to distinguish
        customers and charging stations more accurately.
        """
        customer_ids = []
        for route in self.routes:
            customer_ids.extend(route.customer_ids)
        return customer_ids
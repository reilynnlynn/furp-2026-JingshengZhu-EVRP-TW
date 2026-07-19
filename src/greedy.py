from src.instance import EVRPTWInstance
from src.solution import Route, Solution


def build_greedy_solution(instance: EVRPTWInstance) -> Solution:
    """
    Simple greedy baseline:
    - visit customers in increasing node id order
    - split into separate routes if needed
    """
    customer_ids = [node.id for node in instance.customers]

    routes = []
    for customer_id in customer_ids:
        routes.append(Route(node_ids=[instance.depot_id, customer_id, instance.depot_id]))

    return Solution(routes=routes)
from dataclasses import dataclass

from src.checker import check_solution
from src.distance import euclidean_distance
from src.instance import EVRPTWInstance
from src.solution import Solution


@dataclass
class EvaluationResult:
    total_distance: float
    vehicle_count: int
    charging_count: int
    feasible: bool
    num_violations: int
    penalty: float
    objective: float
    messages: list[str]


def calculate_total_distance(instance: EVRPTWInstance, solution: Solution) -> float:
    total_distance = 0.0

    for route in solution.routes:
        for i in range(len(route.node_ids) - 1):
            from_node = instance.get_node(route.node_ids[i])
            to_node = instance.get_node(route.node_ids[i + 1])
            total_distance += euclidean_distance(from_node, to_node)

    return total_distance


def count_charging_visits(instance: EVRPTWInstance, solution: Solution) -> int:
    charging_count = 0

    for route in solution.routes:
        for node_id in route.node_ids:
            node = instance.get_node(node_id)
            if node.node_type == "station":
                charging_count += 1

    return charging_count


def evaluate_solution(
    instance: EVRPTWInstance,
    solution: Solution,
    penalty_per_violation: float = 100000.0,
) -> EvaluationResult:
    check_result = check_solution(instance, solution)

    total_distance = calculate_total_distance(instance, solution)
    vehicle_count = len(solution.routes)
    charging_count = count_charging_visits(instance, solution)

    num_violations = len(check_result.messages)
    penalty = 0.0
    if not check_result.feasible:
        penalty = penalty_per_violation * num_violations

    objective = total_distance + penalty

    return EvaluationResult(
        total_distance=total_distance,
        vehicle_count=vehicle_count,
        charging_count=charging_count,
        feasible=check_result.feasible,
        num_violations=num_violations,
        penalty=penalty,
        objective=objective,
        messages=check_result.messages,
    )
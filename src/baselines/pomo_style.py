"""
    The purpose is to recreate the core POMO idea in a reproducible way:

        - multiple rollout starts;
        - construct one candidate solution from each start;
        - evaluate feasibility and objective;
        - select the best rollout.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import random
import time
from typing import Iterable, Optional, Sequence

from src.distance import euclidean_distance
from src.solution import Route, Solution

try:
    from src.checker import check_solution
except Exception:  # pragma: no cover
    check_solution = None


@dataclass
class POMOStyleResult:
    """
    Result object returned by the POMO-style baseline.

    Attributes:
        solution:
            The selected EVRP-TW solution.
        objective:
            Total route distance.
        feasible:
            Whether the solution is feasible according to the project checker.
            If checker is unavailable, this may be None.
        rollout_count:
            Number of candidate rollouts generated.
        selected_rollout:
            Index of the selected rollout.
        runtime_seconds:
            Wall-clock runtime.
        feasibility_messages:
            Messages returned by checker for the selected solution.
    """

    solution: Solution
    objective: float
    feasible: Optional[bool]
    rollout_count: int
    selected_rollout: int
    runtime_seconds: float
    feasibility_messages: list[str]


class POMOStyleBaseline:
    """
    POMO-style construction baseline.

    The baseline creates multiple candidate solutions using different starting
    customers. Each candidate is built by a nearest-neighbor style rollout.
    The best candidate is selected based on:

        1. feasibility;
        2. number of feasibility messages / violations;
        3. total route distance.

    This is deliberately deterministic by default so that experiments are
    reproducible.
    """

    name = "pomo_style"

    def __init__(
        self,
        rollout_count: int = 16,
        random_seed: int = 0,
        shuffle_fraction: float = 0.25,
    ) -> None:
        if rollout_count <= 0:
            raise ValueError("rollout_count must be positive.")

        self.rollout_count = rollout_count
        self.random_seed = random_seed
        self.shuffle_fraction = shuffle_fraction

    def solve(self, instance) -> POMOStyleResult:
        """
        Solve an EVRP-TW instance using the POMO-style baseline.

        Args:
            instance:
                EVRP-TW instance object used by the current project.

        Returns:
            POMOStyleResult.
        """

        start_time = time.perf_counter()

        customers = _get_customer_ids(instance)
        depot_id = _get_depot_id(instance)

        if not customers:
            solution = Solution(routes=[])
            runtime = time.perf_counter() - start_time
            feasible, messages = _safe_check(instance, solution)
            return POMOStyleResult(
                solution=solution,
                objective=0.0,
                feasible=feasible,
                rollout_count=0,
                selected_rollout=-1,
                runtime_seconds=runtime,
                feasibility_messages=messages,
            )

        rng = random.Random(self.random_seed)

        rollout_orders = self._generate_rollout_orders(
            instance=instance,
            customers=customers,
            depot_id=depot_id,
            rng=rng,
        )

        candidates: list[tuple[int, Solution, float, Optional[bool], list[str]]] = []

        for rollout_idx, order in enumerate(rollout_orders):
            solution = _decode_customer_order(instance, order, depot_id)
            objective = _solution_distance(instance, solution)
            feasible, messages = _safe_check(instance, solution)
            candidates.append((rollout_idx, solution, objective, feasible, messages))

        selected_idx, selected_solution, selected_obj, selected_feasible, selected_messages = min(
            candidates,
            key=lambda item: _candidate_key(item),
        )

        runtime = time.perf_counter() - start_time

        return POMOStyleResult(
            solution=selected_solution,
            objective=selected_obj,
            feasible=selected_feasible,
            rollout_count=len(rollout_orders),
            selected_rollout=selected_idx,
            runtime_seconds=runtime,
            feasibility_messages=selected_messages,
        )

    def _generate_rollout_orders(
        self,
        instance,
        customers: list[int],
        depot_id: int,
        rng: random.Random,
    ) -> list[list[int]]:
        """
        Generate multiple customer visiting orders.

        The first group uses each customer as a possible POMO start.
        If more rollouts are requested, additional mildly randomized orders are
        added to improve diversity.
        """

        orders: list[list[int]] = []

        starts = customers[:]
        rng.shuffle(starts)

        for start_customer in starts:
            if len(orders) >= self.rollout_count:
                break

            order = _nearest_neighbor_order(
                instance=instance,
                customers=customers,
                depot_id=depot_id,
                start_customer=start_customer,
            )
            orders.append(order)

        while len(orders) < self.rollout_count:
            start_customer = rng.choice(customers)
            order = _nearest_neighbor_order(
                instance=instance,
                customers=customers,
                depot_id=depot_id,
                start_customer=start_customer,
            )
            order = _lightly_shuffle_order(order, rng, self.shuffle_fraction)
            orders.append(order)

        return orders


def solve_pomo_style(
    instance,
    rollout_count: int = 16,
    random_seed: int = 0,
    shuffle_fraction: float = 0.25,
) -> POMOStyleResult:
    """
    Functional API for the POMO-style baseline.

    This wrapper is convenient for scripts and comparison runners.
    """

    solver = POMOStyleBaseline(
        rollout_count=rollout_count,
        random_seed=random_seed,
        shuffle_fraction=shuffle_fraction,
    )
    return solver.solve(instance)


def solve(instance) -> Solution:
    """
    Simple compatibility wrapper.

    Some baseline comparison runners expect a function named `solve` that
    directly returns a Solution instead of a rich result object.
    """

    return solve_pomo_style(instance).solution


def _get_depot_id(instance) -> int:
    """
    Infer depot id from the instance.

    The project may store depot information using different names, so this
    function is intentionally defensive.
    """

    for attr in ("depot_id", "depot", "start_depot_id"):
        if hasattr(instance, attr):
            value = getattr(instance, attr)
            if isinstance(value, int):
                return value
            if hasattr(value, "id"):
                return int(value.id)
            if hasattr(value, "node_id"):
                return int(value.node_id)

    nodes = _get_nodes(instance)
    for node in nodes:
        node_type = str(getattr(node, "type", getattr(node, "node_type", ""))).lower()
        if "depot" in node_type:
            return _node_id(node)

    return 0


def _get_nodes(instance) -> list:
    if hasattr(instance, "nodes"):
        nodes = getattr(instance, "nodes")
        if isinstance(nodes, dict):
            return list(nodes.values())
        return list(nodes)

    if hasattr(instance, "customers"):
        depot_id = _get_depot_id(instance)
        depot_node = _get_node(instance, depot_id)
        return [depot_node] + list(getattr(instance, "customers"))

    raise AttributeError("Cannot find nodes in instance. Expected instance.nodes.")


def _get_node(instance, node_id: int):
    nodes = getattr(instance, "nodes")

    if isinstance(nodes, dict):
        return nodes[node_id]

    for node in nodes:
        if _node_id(node) == node_id:
            return node

    raise KeyError(f"Node id {node_id} not found.")


def _node_id(node) -> int:
    for attr in ("id", "node_id", "index", "idx"):
        if hasattr(node, attr):
            return int(getattr(node, attr))
    raise AttributeError(f"Cannot infer node id from node: {node!r}")


def _is_customer(node, depot_id: int) -> bool:
    node_id = _node_id(node)

    if node_id == depot_id:
        return False

    node_type = str(getattr(node, "type", getattr(node, "node_type", ""))).lower()

    if node_type:
        if "depot" in node_type:
            return False
        if "station" in node_type or "charging" in node_type or node_type in {"f", "cs"}:
            return False
        if "customer" in node_type or node_type in {"c", "client"}:
            return True

    demand = getattr(node, "demand", None)
    if demand is not None:
        try:
            return float(demand) > 0
        except Exception:
            pass

    # Fallback:
    # If a non-depot node has no explicit type and no demand information,
    # treat it as a customer. This is useful for simple generated instances.
    return True


def _get_customer_ids(instance) -> list[int]:
    depot_id = _get_depot_id(instance)
    nodes = _get_nodes(instance)

    customers = [_node_id(node) for node in nodes if _is_customer(node, depot_id)]
    customers = sorted(set(customers))

    return customers


def _nearest_neighbor_order(
    instance,
    customers: Sequence[int],
    depot_id: int,
    start_customer: int,
) -> list[int]:
    """
    Construct one nearest-neighbor rollout order starting from a given customer.
    """

    unvisited = set(customers)
    order: list[int] = []

    current = start_customer
    if current in unvisited:
        order.append(current)
        unvisited.remove(current)
    else:
        current = depot_id

    while unvisited:
        next_customer = min(
            unvisited,
            key=lambda customer_id: _distance_between(instance, current, customer_id),
        )
        order.append(next_customer)
        unvisited.remove(next_customer)
        current = next_customer

    return order


def _lightly_shuffle_order(
    order: list[int],
    rng: random.Random,
    shuffle_fraction: float,
) -> list[int]:
    """
    Add small random perturbation to a rollout order.

    This gives POMO-style multiple rollouts some diversity while preserving
    the nearest-neighbor structure.
    """

    if len(order) <= 2:
        return order[:]

    new_order = order[:]
    swap_count = max(1, int(len(order) * shuffle_fraction))

    for _ in range(swap_count):
        i = rng.randrange(len(new_order))
        j = rng.randrange(len(new_order))
        new_order[i], new_order[j] = new_order[j], new_order[i]

    return new_order


def _decode_customer_order(instance, order: Sequence[int], depot_id: int) -> Solution:
    """
    Decode a customer permutation into EVRP-TW routes.

    The decoder is intentionally simple and robust:
        - It builds routes in the given customer order.
        - It starts a new route when capacity would be exceeded.
        - It always returns routes in the form [depot, ..., depot].

    More advanced battery / charging repair is handled by the feasibility
    checker and future Week 3 EVRP-TW work.
    """

    capacity = _get_vehicle_capacity(instance)

    routes: list[Route] = []
    current_route: list[int] = [depot_id]
    current_load = 0.0

    for customer_id in order:
        demand = _get_demand(instance, customer_id)

        should_start_new_route = (
            len(current_route) > 1
            and capacity is not None
            and current_load + demand > capacity + 1e-9
        )

        if should_start_new_route:
            current_route.append(depot_id)
            routes.append(Route(node_ids=current_route))

            current_route = [depot_id]
            current_load = 0.0

        current_route.append(customer_id)
        current_load += demand

    if len(current_route) > 1:
        current_route.append(depot_id)
        routes.append(Route(node_ids=current_route))

    return Solution(routes=routes)


def _get_vehicle_capacity(instance) -> Optional[float]:
    for attr in ("vehicle_capacity", "capacity", "vehicle_load_capacity"):
        if hasattr(instance, attr):
            value = getattr(instance, attr)
            if value is None:
                return None
            try:
                return float(value)
            except Exception:
                return None
    return None


def _get_demand(instance, node_id: int) -> float:
    try:
        node = _get_node(instance, node_id)
    except Exception:
        return 0.0

    value = getattr(node, "demand", 0.0)

    try:
        return float(value)
    except Exception:
        return 0.0


def _distance_between(instance, from_id: int, to_id: int) -> float:
    from_node = _get_node(instance, from_id)
    to_node = _get_node(instance, to_id)
    return float(euclidean_distance(from_node, to_node))


def _solution_distance(instance, solution: Solution) -> float:
    total = 0.0

    for route in solution.routes:
        node_ids = list(route.node_ids)

        for from_id, to_id in zip(node_ids[:-1], node_ids[1:]):
            total += _distance_between(instance, from_id, to_id)

    return total


def _safe_check(instance, solution: Solution) -> tuple[Optional[bool], list[str]]:
    """
    Run project checker if available.

    If the checker cannot run on a lightweight test instance, this function
    returns (None, []) instead of crashing.
    """

    if check_solution is None:
        return None, []

    try:
        result = check_solution(instance, solution)
    except Exception:
        return None, []

    feasible = getattr(result, "feasible", None)
    messages = getattr(result, "messages", [])

    if messages is None:
        messages = []

    return feasible, list(messages)


def _candidate_key(
    candidate: tuple[int, Solution, float, Optional[bool], list[str]],
) -> tuple[int, int, float, int]:
    """
    Ranking rule for candidates.

    Prefer:
        1. feasible solutions;
        2. fewer checker messages;
        3. shorter distance;
        4. smaller rollout index for deterministic tie-breaking.
    """

    rollout_idx, _solution, objective, feasible, messages = candidate

    if feasible is True:
        feasibility_rank = 0
    elif feasible is None:
        feasibility_rank = 1
    else:
        feasibility_rank = 2

    violation_count = len(messages)

    if not math.isfinite(objective):
        objective = float("inf")

    return feasibility_rank, violation_count, objective, rollout_idx
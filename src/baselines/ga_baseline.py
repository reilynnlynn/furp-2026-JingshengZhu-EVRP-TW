"""

Core GA components:
    - chromosome: permutation of customer ids;
    - initial population;
    - fitness evaluation;
    - tournament selection;
    - ordered crossover;
    - swap / inversion mutation;
    - elitism;
    - route decoding;
    - simple EV battery repair by inserting charging stations.

"""

from __future__ import annotations

from dataclasses import dataclass
import math
import random
import time
from typing import Optional, Sequence

from src.distance import euclidean_distance
from src.solution import Route, Solution

try:
    from src.checker import check_solution
except Exception:  # pragma: no cover
    check_solution = None


@dataclass
class GAResult:
    """
    Result returned by the GA baseline.

    Attributes:
        solution:
            Best solution found.
        objective:
            Total distance of the best solution.
        feasible:
            Feasibility according to project checker.
        generation_count:
            Number of GA generations.
        population_size:
            Population size.
        runtime_seconds:
            Wall-clock runtime.
        best_fitness:
            Internal fitness value. Lower is better.
        feasibility_messages:
            Checker messages for selected solution.
    """

    solution: Solution
    objective: float
    feasible: Optional[bool]
    generation_count: int
    population_size: int
    runtime_seconds: float
    best_fitness: float
    feasibility_messages: list[str]


class GABaseline:
    """
    Genetic Algorithm baseline for EVRP-TW.

    Chromosome:
        A list of customer ids.

    Decoder:
        Converts a customer permutation into routes:
            [depot, customer, customer, ..., depot]

        A new route is started when the vehicle capacity would be exceeded.

    EV repair:
        If a long edge appears to exceed the estimated battery range, the decoder
        attempts to insert a nearest charging station between the two nodes.

    Fitness:
        Lower is better.

        fitness = distance
                  + infeasible penalty
                  + checker-message penalty
                  + route-count penalty
    """

    name = "ga_baseline"

    def __init__(
        self,
        population_size: int = 40,
        generations: int = 80,
        crossover_rate: float = 0.85,
        mutation_rate: float = 0.20,
        elite_size: int = 2,
        tournament_size: int = 3,
        random_seed: int = 0,
        infeasible_penalty: float = 100_000.0,
        checker_message_penalty: float = 1_000.0,
        route_penalty: float = 10.0,
    ) -> None:
        if population_size <= 0:
            raise ValueError("population_size must be positive.")
        if generations < 0:
            raise ValueError("generations cannot be negative.")
        if not 0.0 <= crossover_rate <= 1.0:
            raise ValueError("crossover_rate must be in [0, 1].")
        if not 0.0 <= mutation_rate <= 1.0:
            raise ValueError("mutation_rate must be in [0, 1].")
        if elite_size < 0:
            raise ValueError("elite_size cannot be negative.")
        if elite_size >= population_size:
            raise ValueError("elite_size must be smaller than population_size.")
        if tournament_size <= 0:
            raise ValueError("tournament_size must be positive.")

        self.population_size = population_size
        self.generations = generations
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.elite_size = elite_size
        self.tournament_size = tournament_size
        self.random_seed = random_seed
        self.infeasible_penalty = infeasible_penalty
        self.checker_message_penalty = checker_message_penalty
        self.route_penalty = route_penalty

    def solve(self, instance) -> GAResult:
        """
        Solve an EVRP-TW instance using GA.

        Args:
            instance:
                EVRP-TW instance object.

        Returns:
            GAResult.
        """

        start_time = time.perf_counter()
        rng = random.Random(self.random_seed)

        depot_id = _get_depot_id(instance)
        customers = _get_customer_ids(instance)

        if not customers:
            solution = Solution(routes=[])
            runtime = time.perf_counter() - start_time
            feasible, messages = _safe_check(instance, solution)
            return GAResult(
                solution=solution,
                objective=0.0,
                feasible=feasible,
                generation_count=0,
                population_size=self.population_size,
                runtime_seconds=runtime,
                best_fitness=0.0,
                feasibility_messages=messages,
            )

        population = self._initialize_population(instance, customers, depot_id, rng)

        best_chromosome: list[int] | None = None
        best_fitness = float("inf")

        for _generation in range(self.generations + 1):
            evaluated = [
                (chromosome, self._fitness(instance, chromosome, depot_id))
                for chromosome in population
            ]
            evaluated.sort(key=lambda item: item[1])

            if evaluated[0][1] < best_fitness:
                best_chromosome = evaluated[0][0][:]
                best_fitness = evaluated[0][1]

            if _generation == self.generations:
                break

            next_population: list[list[int]] = []

            # Elitism: keep best chromosomes.
            for chromosome, _fitness_value in evaluated[: self.elite_size]:
                next_population.append(chromosome[:])

            while len(next_population) < self.population_size:
                parent_a = self._tournament_select(evaluated, rng)
                parent_b = self._tournament_select(evaluated, rng)

                if rng.random() < self.crossover_rate:
                    child = _ordered_crossover(parent_a, parent_b, rng)
                else:
                    child = parent_a[:]

                if rng.random() < self.mutation_rate:
                    child = _mutate(child, rng)

                child = _repair_permutation(child, customers)
                next_population.append(child)

            population = next_population

        assert best_chromosome is not None

        best_solution = _decode_chromosome(instance, best_chromosome, depot_id)
        objective = _solution_distance(instance, best_solution)
        feasible, messages = _safe_check(instance, best_solution)
        runtime = time.perf_counter() - start_time

        return GAResult(
            solution=best_solution,
            objective=objective,
            feasible=feasible,
            generation_count=self.generations,
            population_size=self.population_size,
            runtime_seconds=runtime,
            best_fitness=best_fitness,
            feasibility_messages=messages,
        )

    def _initialize_population(
        self,
        instance,
        customers: list[int],
        depot_id: int,
        rng: random.Random,
    ) -> list[list[int]]:
        """
        Create initial population.

        The population contains:
            - one nearest-neighbor chromosome;
            - one distance-to-depot sorted chromosome;
            - randomized chromosomes.
        """

        population: list[list[int]] = []

        nn_order = _nearest_neighbor_order(instance, customers, depot_id)
        population.append(nn_order)

        depot_sorted = sorted(
            customers,
            key=lambda customer_id: _distance_between(instance, depot_id, customer_id),
        )
        population.append(depot_sorted)

        while len(population) < self.population_size:
            chromosome = customers[:]
            rng.shuffle(chromosome)
            population.append(chromosome)

        return population[: self.population_size]

    def _fitness(self, instance, chromosome: list[int], depot_id: int) -> float:
        """
        Compute GA fitness value.

        Lower is better.
        """

        solution = _decode_chromosome(instance, chromosome, depot_id)
        distance = _solution_distance(instance, solution)
        feasible, messages = _safe_check(instance, solution)

        fitness = distance

        if feasible is False:
            fitness += self.infeasible_penalty
        elif feasible is None:
            # Checker unavailable or incompatible with lightweight tests.
            # Do not punish too heavily.
            fitness += 0.0

        fitness += len(messages) * self.checker_message_penalty
        fitness += len(solution.routes) * self.route_penalty

        if not math.isfinite(fitness):
            return float("inf")

        return fitness

    def _tournament_select(
        self,
        evaluated_population: list[tuple[list[int], float]],
        rng: random.Random,
    ) -> list[int]:
        """
        Tournament selection.

        Select several candidates randomly and return the best one.
        """

        k = min(self.tournament_size, len(evaluated_population))
        candidates = rng.sample(evaluated_population, k)
        candidates.sort(key=lambda item: item[1])
        return candidates[0][0][:]


def solve_ga(
    instance,
    population_size: int = 40,
    generations: int = 80,
    crossover_rate: float = 0.85,
    mutation_rate: float = 0.20,
    elite_size: int = 2,
    tournament_size: int = 3,
    random_seed: int = 0,
) -> GAResult:
    """
    Functional API for GA baseline.
    """

    solver = GABaseline(
        population_size=population_size,
        generations=generations,
        crossover_rate=crossover_rate,
        mutation_rate=mutation_rate,
        elite_size=elite_size,
        tournament_size=tournament_size,
        random_seed=random_seed,
    )
    return solver.solve(instance)


def solve(instance) -> Solution:
    """
    Compatibility wrapper for comparison runners.

    Returns only Solution.
    """

    return solve_ga(instance).solution


def _ordered_crossover(
    parent_a: Sequence[int],
    parent_b: Sequence[int],
    rng: random.Random,
) -> list[int]:
    """
    Ordered crossover for permutation chromosomes.

    Example:
        parent_a: [1, 2, 3, 4, 5]
        parent_b: [5, 3, 1, 2, 4]

    The child keeps one segment from parent_a and fills the rest using parent_b.
    """

    n = len(parent_a)

    if n <= 1:
        return list(parent_a)

    left = rng.randrange(n)
    right = rng.randrange(n)

    if left > right:
        left, right = right, left

    child: list[Optional[int]] = [None] * n
    child[left : right + 1] = parent_a[left : right + 1]

    used = set(value for value in child if value is not None)

    fill_values = [value for value in parent_b if value not in used]
    fill_idx = 0

    for idx in range(n):
        if child[idx] is None:
            child[idx] = fill_values[fill_idx]
            fill_idx += 1

    return [int(value) for value in child if value is not None]


def _mutate(chromosome: list[int], rng: random.Random) -> list[int]:
    """
    Apply one mutation.

    The function randomly chooses between:
        - swap mutation;
        - inversion mutation.
    """

    n = len(chromosome)

    if n <= 1:
        return chromosome[:]

    mutated = chromosome[:]

    if rng.random() < 0.5:
        i = rng.randrange(n)
        j = rng.randrange(n)
        mutated[i], mutated[j] = mutated[j], mutated[i]
    else:
        i = rng.randrange(n)
        j = rng.randrange(n)
        if i > j:
            i, j = j, i
        mutated[i : j + 1] = reversed(mutated[i : j + 1])

    return mutated


def _repair_permutation(chromosome: list[int], customers: Sequence[int]) -> list[int]:
    """
    Ensure chromosome is a valid customer permutation.

    This makes the GA more robust in case crossover or mutation produces
    duplicates due to unexpected input.
    """

    customer_set = set(customers)
    repaired: list[int] = []
    used: set[int] = set()

    for gene in chromosome:
        if gene in customer_set and gene not in used:
            repaired.append(gene)
            used.add(gene)

    for customer in customers:
        if customer not in used:
            repaired.append(customer)

    return repaired


def _decode_chromosome(instance, chromosome: Sequence[int], depot_id: int) -> Solution:
    """
    Decode a customer permutation into EVRP-TW routes.

    The decoder handles:
        - depot start/end;
        - capacity split;
        - simple battery repair using charging station insertion.
    """

    capacity = _get_vehicle_capacity(instance)

    routes: list[Route] = []
    current_route: list[int] = [depot_id]
    current_load = 0.0

    for customer_id in chromosome:
        demand = _get_demand(instance, customer_id)

        should_start_new_route = (
            len(current_route) > 1
            and capacity is not None
            and current_load + demand > capacity + 1e-9
        )

        if should_start_new_route:
            current_route.append(depot_id)
            current_route = _repair_route_energy(instance, current_route)
            routes.append(Route(node_ids=current_route))

            current_route = [depot_id]
            current_load = 0.0

        current_route.append(customer_id)
        current_load += demand

    if len(current_route) > 1:
        current_route.append(depot_id)
        current_route = _repair_route_energy(instance, current_route)
        routes.append(Route(node_ids=current_route))

    return Solution(routes=routes)


def _repair_route_energy(instance, route: list[int]) -> list[int]:
    """
    Simple EV energy repair.

    If the distance from one node to the next exceeds the estimated battery
    range, insert a charging station between them.

    This is a simple adaptation from CVRP-style GA to EVRP.

    Notes:
        - If no charging station exists, the route is returned unchanged.
        - If a station cannot make the segment feasible, the route is still
          returned. The checker will mark it infeasible later.
    """

    battery_range = _get_battery_range(instance)
    charging_station_ids = _get_charging_station_ids(instance)

    if battery_range is None or not charging_station_ids:
        return route

    repaired: list[int] = [route[0]]

    for next_node in route[1:]:
        prev_node = repaired[-1]
        direct_distance = _distance_between(instance, prev_node, next_node)

        if direct_distance <= battery_range + 1e-9:
            repaired.append(next_node)
            continue

        station = _find_best_charging_station(
            instance=instance,
            from_id=prev_node,
            to_id=next_node,
            station_ids=charging_station_ids,
            battery_range=battery_range,
        )

        if station is not None:
            if repaired[-1] != station:
                repaired.append(station)

        repaired.append(next_node)

    return repaired


def _find_best_charging_station(
    instance,
    from_id: int,
    to_id: int,
    station_ids: Sequence[int],
    battery_range: float,
) -> Optional[int]:
    """
    Find a charging station that can bridge from_id -> station -> to_id.
    """

    feasible_stations: list[tuple[float, int]] = []

    for station_id in station_ids:
        d1 = _distance_between(instance, from_id, station_id)
        d2 = _distance_between(instance, station_id, to_id)

        if d1 <= battery_range + 1e-9 and d2 <= battery_range + 1e-9:
            feasible_stations.append((d1 + d2, station_id))

    if feasible_stations:
        feasible_stations.sort(key=lambda item: item[0])
        return feasible_stations[0][1]

    # fallback: choose station minimizing total detour, even if not fully feasible
    fallback: list[tuple[float, int]] = []
    for station_id in station_ids:
        d1 = _distance_between(instance, from_id, station_id)
        d2 = _distance_between(instance, station_id, to_id)
        fallback.append((d1 + d2, station_id))

    if not fallback:
        return None

    fallback.sort(key=lambda item: item[0])
    return fallback[0][1]


def _nearest_neighbor_order(instance, customers: Sequence[int], depot_id: int) -> list[int]:
    """
    Build one nearest-neighbor order used as a strong initial chromosome.
    """

    unvisited = set(customers)
    order: list[int] = []
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


def _get_depot_id(instance) -> int:
    """
    Infer depot id from instance.
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
    """
    Get all nodes from instance.
    """

    if hasattr(instance, "nodes"):
        nodes = getattr(instance, "nodes")
        if isinstance(nodes, dict):
            return list(nodes.values())
        return list(nodes)

    raise AttributeError("Cannot find nodes in instance. Expected instance.nodes.")


def _get_node(instance, node_id: int):
    """
    Get node object by node id.
    """

    nodes = getattr(instance, "nodes")

    if isinstance(nodes, dict):
        return nodes[node_id]

    for node in nodes:
        if _node_id(node) == node_id:
            return node

    raise KeyError(f"Node id {node_id} not found.")


def _node_id(node) -> int:
    """
    Infer node id from node object.
    """

    for attr in ("id", "node_id", "index", "idx"):
        if hasattr(node, attr):
            return int(getattr(node, attr))

    raise AttributeError(f"Cannot infer node id from node: {node!r}")


def _is_customer(node, depot_id: int) -> bool:
    """
    Decide whether a node is a customer.
    """

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

    return True


def _is_charging_station(node, depot_id: int) -> bool:
    """
    Decide whether a node is a charging station.
    """

    node_id = _node_id(node)

    if node_id == depot_id:
        return False

    node_type = str(getattr(node, "type", getattr(node, "node_type", ""))).lower()

    if "station" in node_type or "charging" in node_type or node_type in {"f", "cs"}:
        return True

    # Some Solomon-style EVRP files use type 'f' for charging station.
    if node_type == "f":
        return True

    return False


def _get_customer_ids(instance) -> list[int]:
    depot_id = _get_depot_id(instance)
    nodes = _get_nodes(instance)

    customers = [_node_id(node) for node in nodes if _is_customer(node, depot_id)]
    return sorted(set(customers))


def _get_charging_station_ids(instance) -> list[int]:
    depot_id = _get_depot_id(instance)
    nodes = _get_nodes(instance)

    stations = [_node_id(node) for node in nodes if _is_charging_station(node, depot_id)]
    return sorted(set(stations))


def _get_vehicle_capacity(instance) -> Optional[float]:
    """
    Get vehicle capacity.
    """

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


def _get_battery_range(instance) -> Optional[float]:
    """
    Estimate battery travel range.

    Different EVRP implementations store battery data under different names.
    This function tries several common names.

    If only battery_capacity and energy_consumption_rate are available:

        range = battery_capacity / energy_consumption_rate
    """

    for attr in (
        "battery_range",
        "max_travel_distance",
        "vehicle_range",
        "driving_range",
        "max_distance_per_charge",
    ):
        if hasattr(instance, attr):
            value = getattr(instance, attr)
            if value is not None:
                try:
                    return float(value)
                except Exception:
                    pass

    battery_capacity = None
    consumption_rate = None

    for attr in ("battery_capacity", "vehicle_battery_capacity", "battery"):
        if hasattr(instance, attr):
            value = getattr(instance, attr)
            try:
                battery_capacity = float(value)
                break
            except Exception:
                pass

    for attr in (
        "energy_consumption_rate",
        "battery_consumption_rate",
        "fuel_consumption_rate",
        "consumption_rate",
    ):
        if hasattr(instance, attr):
            value = getattr(instance, attr)
            try:
                consumption_rate = float(value)
                break
            except Exception:
                pass

    if battery_capacity is not None and consumption_rate is not None and consumption_rate > 0:
        return battery_capacity / consumption_rate

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
    Run project checker safely.
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
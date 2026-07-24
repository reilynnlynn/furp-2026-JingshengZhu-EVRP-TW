from __future__ import annotations

import argparse
import csv
import json
import re
import time
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from src.baselines.ga_baseline import solve_ga
from src.instance import EVRPTWInstance, Node
from src.io import load_instance_from_json


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_INSTANCE_DIR = PROJECT_ROOT / "data" / "week3_benchmarks"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "results" / "week3"
DEFAULT_CSV_PATH = DEFAULT_OUTPUT_DIR / "baseline_results.csv"
DEFAULT_JSON_PATH = DEFAULT_OUTPUT_DIR / "baseline_results.json"


def parse_int_list(text: str) -> List[int]:
    values: List[int] = []

    for raw_part in text.split(","):
        part = raw_part.strip()
        if not part:
            continue
        values.append(int(part))

    if not values:
        raise ValueError("At least one integer seed must be provided.")

    return values


def natural_sort_key(path: Path) -> Tuple[int, int, str]:
    match = re.search(r"c(\d+)_s(\d+)", path.stem)

    if match:
        customer_count = int(match.group(1))
        seed = int(match.group(2))
        return customer_count, seed, path.name

    return 10**9, 10**9, path.name


def find_instance_files(instance_dir: Path, limit: Optional[int]) -> List[Path]:
    if not instance_dir.exists():
        raise FileNotFoundError(f"Instance directory not found: {instance_dir}")

    files = sorted(instance_dir.glob("*.json"), key=natural_sort_key)

    if not files:
        raise FileNotFoundError(f"No JSON instance files found in: {instance_dir}")

    if limit is not None:
        files = files[:limit]

    return files


def extract_customer_count(instance: EVRPTWInstance, instance_path: Path) -> int:
    if hasattr(instance, "customers"):
        customers = getattr(instance, "customers")
        if customers is not None:
            return len(list(customers))

    count = sum(1 for node in instance.nodes if node.node_type == "customer")

    if count > 0:
        return count

    match = re.search(r"c(\d+)", instance_path.stem)
    if match:
        return int(match.group(1))

    return 0


def extract_station_count(instance: EVRPTWInstance) -> int:
    if hasattr(instance, "stations"):
        stations = getattr(instance, "stations")
        if stations is not None:
            return len(list(stations))

    return sum(1 for node in instance.nodes if node.node_type == "station")


def extract_instance_seed(instance_path: Path) -> Optional[int]:
    match = re.search(r"_s(\d+)", instance_path.stem)

    if match:
        return int(match.group(1))

    match = re.search(r"seed(\d+)", instance_path.stem)

    if match:
        return int(match.group(1))

    return None


def safe_getattr(obj: Any, name: str, default: Any = None) -> Any:
    if obj is None:
        return default

    if isinstance(obj, dict):
        return obj.get(name, default)

    return getattr(obj, name, default)


def dataclass_or_object_to_dict(obj: Any) -> Dict[str, Any]:
    if obj is None:
        return {}

    if isinstance(obj, dict):
        return dict(obj)

    if is_dataclass(obj):
        return asdict(obj)

    output: Dict[str, Any] = {}

    for name in dir(obj):
        if name.startswith("_"):
            continue

        try:
            value = getattr(obj, name)
        except Exception:
            continue

        if callable(value):
            continue

        output[name] = value

    return output


def normalize_messages(messages: Any) -> List[str]:
    if messages is None:
        return []

    if isinstance(messages, str):
        return [messages]

    if isinstance(messages, Iterable):
        return [str(message) for message in messages]

    return [str(messages)]


def classify_violation_messages(messages: Sequence[str]) -> Dict[str, int]:
    lower_messages = [message.lower() for message in messages]

    capacity_count = 0
    battery_count = 0
    time_window_count = 0
    coverage_count = 0
    route_count = 0
    other_count = 0

    for message in lower_messages:
        matched = False

        if "capacity" in message or "load" in message or "demand" in message:
            capacity_count += 1
            matched = True

        if (
            "battery" in message
            or "energy" in message
            or "charge" in message
            or "charging" in message
        ):
            battery_count += 1
            matched = True

        if (
            "time window" in message
            or "time-window" in message
            or "timewindow" in message
            or "late" in message
            or "early" in message
            or "due" in message
            or "ready" in message
        ):
            time_window_count += 1
            matched = True

        if (
            "visit" in message
            or "visited" in message
            or "missing" in message
            or "duplicate" in message
            or "customer" in message
        ):
            coverage_count += 1
            matched = True

        if "route" in message or "vehicle" in message or "fleet" in message:
            route_count += 1
            matched = True

        if not matched:
            other_count += 1

    return {
        "capacity_violations": capacity_count,
        "battery_violations": battery_count,
        "time_window_violations": time_window_count,
        "coverage_violations": coverage_count,
        "route_violations": route_count,
        "other_violations": other_count,
        "total_violations": len(messages),
    }


def extract_route_node_ids(route: Any) -> List[int]:
    if route is None:
        return []

    if isinstance(route, list):
        return [int(node_id) for node_id in route]

    if isinstance(route, tuple):
        return [int(node_id) for node_id in route]

    if isinstance(route, dict):
        if "node_ids" in route:
            return [int(node_id) for node_id in route["node_ids"]]
        if "nodes" in route:
            return [int(node_id) for node_id in route["nodes"]]
        if "route" in route:
            return [int(node_id) for node_id in route["route"]]

    if hasattr(route, "node_ids"):
        return [int(node_id) for node_id in getattr(route, "node_ids")]

    if hasattr(route, "nodes"):
        return [int(node_id) for node_id in getattr(route, "nodes")]

    return []


def extract_routes(solution: Any) -> List[List[int]]:
    if solution is None:
        return []

    raw_routes = None

    if isinstance(solution, dict):
        raw_routes = solution.get("routes")
    elif isinstance(solution, list):
        raw_routes = solution
    elif hasattr(solution, "routes"):
        raw_routes = getattr(solution, "routes")

    if raw_routes is None:
        return []

    routes: List[List[int]] = []

    for route in raw_routes:
        node_ids = extract_route_node_ids(route)
        if node_ids:
            routes.append(node_ids)

    return routes


def get_customer_ids(instance: EVRPTWInstance) -> set[int]:
    if hasattr(instance, "customers"):
        customers = getattr(instance, "customers")
        if customers is not None:
            return {int(node.id) for node in customers}

    return {int(node.id) for node in instance.nodes if node.node_type == "customer"}


def count_served_customers(routes: Sequence[Sequence[int]], instance: EVRPTWInstance) -> int:
    customer_ids = get_customer_ids(instance)

    served = set()

    for route in routes:
        for node_id in route:
            if int(node_id) in customer_ids:
                served.add(int(node_id))

    return len(served)


def get_result_messages(result: Any, result_dict: Dict[str, Any]) -> List[str]:
    messages = safe_getattr(result, "messages", None)

    if messages is None:
        messages = safe_getattr(result, "feasibility_messages", None)

    if messages is None:
        messages = result_dict.get("messages", None)

    if messages is None:
        messages = result_dict.get("feasibility_messages", [])

    return normalize_messages(messages)


def evaluate_result(
    result: Any,
    instance: EVRPTWInstance,
    instance_path: Path,
    instance_seed: Optional[int],
    algorithm_seed: int,
    runtime_seconds: float,
    population_size: int,
    generations: int,
) -> Dict[str, Any]:
    result_dict = dataclass_or_object_to_dict(result)

    solution = safe_getattr(result, "solution")
    routes = extract_routes(solution)

    messages = get_result_messages(result, result_dict)
    violation_counts = classify_violation_messages(messages)

    num_customers = extract_customer_count(instance, instance_path)
    num_stations = extract_station_count(instance)

    served_customers = safe_getattr(result, "served_customers", None)

    if served_customers is None:
        served_customers = count_served_customers(routes, instance)

    unserved_customers = max(0, num_customers - int(served_customers))

    result_route_count = safe_getattr(result, "route_count", None)

    if result_route_count is None:
        result_route_count = len(routes)

    feasible_raw = safe_getattr(result, "feasible", None)

    if feasible_raw is None:
        feasible = False
    else:
        feasible = bool(feasible_raw)

    best_distance = safe_getattr(result, "best_distance", None)

    if best_distance is None:
        best_distance = safe_getattr(result, "distance", None)

    if best_distance is None:
        best_distance = safe_getattr(result, "objective", None)

    objective = safe_getattr(result, "objective", None)

    if objective is None:
        objective = safe_getattr(result, "fitness", None)

    if objective is None:
        objective = safe_getattr(result, "best_fitness", None)

    row: Dict[str, Any] = {
        "algorithm": "ga_baseline",
        "instance_name": instance_path.stem,
        "instance_file": str(instance_path.relative_to(PROJECT_ROOT)),
        "num_customers": num_customers,
        "num_stations": num_stations,
        "instance_seed": instance_seed,
        "algorithm_seed": algorithm_seed,
        "population_size": population_size,
        "generations": generations,
        "runtime_seconds": runtime_seconds,
        "feasible": feasible,
        "best_distance": best_distance,
        "objective": objective,
        "served_customers": int(served_customers),
        "unserved_customers": int(unserved_customers),
        "route_count": int(result_route_count),
        "message_count": len(messages),
        "messages": " | ".join(messages),
        "routes": json.dumps(routes),
    }

    row.update(violation_counts)

    return row


def run_single_experiment(
    instance_path: Path,
    algorithm_seed: int,
    population_size: int,
    generations: int,
) -> Dict[str, Any]:
    instance = load_instance_from_json(instance_path)
    instance_seed = extract_instance_seed(instance_path)

    start_time = time.perf_counter()

    result = solve_ga(
        instance,
        population_size=population_size,
        generations=generations,
        random_seed=algorithm_seed,
    )

    runtime_seconds = time.perf_counter() - start_time

    return evaluate_result(
        result=result,
        instance=instance,
        instance_path=instance_path,
        instance_seed=instance_seed,
        algorithm_seed=algorithm_seed,
        runtime_seconds=runtime_seconds,
        population_size=population_size,
        generations=generations,
    )


def write_csv(rows: Sequence[Dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not rows:
        raise ValueError("Cannot write CSV because there are no result rows.")

    preferred_fields = [
        "algorithm",
        "instance_name",
        "instance_file",
        "num_customers",
        "num_stations",
        "instance_seed",
        "algorithm_seed",
        "population_size",
        "generations",
        "runtime_seconds",
        "feasible",
        "best_distance",
        "objective",
        "served_customers",
        "unserved_customers",
        "route_count",
        "capacity_violations",
        "battery_violations",
        "time_window_violations",
        "coverage_violations",
        "route_violations",
        "other_violations",
        "total_violations",
        "message_count",
        "messages",
        "routes",
    ]

    extra_fields = sorted(
        {
            field
            for row in rows
            for field in row.keys()
            if field not in preferred_fields
        }
    )

    fieldnames = preferred_fields + extra_fields

    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(rows: Sequence[Dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(list(rows), file, indent=2)


def print_progress(row: Dict[str, Any]) -> None:
    print(
        " | ".join(
            [
                f"algorithm={row['algorithm']}",
                f"instance={row['instance_name']}",
                f"algo_seed={row['algorithm_seed']}",
                f"customers={row['num_customers']}",
                f"stations={row['num_stations']}",
                f"feasible={row['feasible']}",
                f"served={row['served_customers']}/{row['num_customers']}",
                f"routes={row['route_count']}",
                f"distance={row['best_distance']}",
                f"violations={row['total_violations']}",
                f"runtime={row['runtime_seconds']:.3f}s",
            ]
        )
    )


def run_experiments(
    instance_dir: Path,
    output_csv: Path,
    output_json: Path,
    seeds: Sequence[int],
    population_size: int,
    generations: int,
    limit: Optional[int],
) -> List[Dict[str, Any]]:
    instance_files = find_instance_files(instance_dir=instance_dir, limit=limit)

    print("Running Week 3 baseline GA experiments")
    print("=" * 100)
    print(f"Instance directory: {instance_dir}")
    print(f"Number of instances: {len(instance_files)}")
    print(f"Algorithm seeds: {list(seeds)}")
    print(f"Population size: {population_size}")
    print(f"Generations: {generations}")
    print(f"Output CSV: {output_csv}")
    print(f"Output JSON: {output_json}")
    print("=" * 100)

    rows: List[Dict[str, Any]] = []

    for instance_path in instance_files:
        for algorithm_seed in seeds:
            row = run_single_experiment(
                instance_path=instance_path,
                algorithm_seed=algorithm_seed,
                population_size=population_size,
                generations=generations,
            )
            rows.append(row)
            print_progress(row)

    write_csv(rows, output_csv)
    write_json(rows, output_json)

    print("=" * 100)
    print(f"Finished baseline experiments. Rows written: {len(rows)}")

    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance-dir", type=Path, default=DEFAULT_INSTANCE_DIR)
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_CSV_PATH)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_JSON_PATH)
    parser.add_argument("--seeds", type=str, default="0,1,2")
    parser.add_argument("--population-size", type=int, default=80)
    parser.add_argument("--generations", type=int, default=80)
    parser.add_argument("--limit", type=int, default=None)

    args = parser.parse_args()

    seeds = parse_int_list(args.seeds)

    run_experiments(
        instance_dir=args.instance_dir,
        output_csv=args.output_csv,
        output_json=args.output_json,
        seeds=seeds,
        population_size=args.population_size,
        generations=args.generations,
        limit=args.limit,
    )


if __name__ == "__main__":
    main()
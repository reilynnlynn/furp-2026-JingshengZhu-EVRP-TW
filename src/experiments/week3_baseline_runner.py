"""
Main responsibilities:

    1. Build or receive benchmark instances.
    2. Run the baseline GA multiple times with fixed random seeds.
    3. Evaluate each solution with the same Week 3 metric function.
    4. Save results as CSV and JSON files.
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
import csv
import json
from pathlib import Path
from typing import Any, Iterable

from src.evaluation.week3_metrics import evaluate_solution
from src.experiments.week3_methods import MethodRunResult, run_week3_method
from src.generator import generate_random_evrptw_instance


DEFAULT_INSTANCE_SPECS: list[dict[str, Any]] = [
    {
        "name": "week3_c20_s4_seed2026",
        "num_customers": 20,
        "num_stations": 4,
        "vehicle_count": 5,
        "vehicle_capacity": 80.0,
        "battery_capacity": 250.0,
        "energy_consumption_rate": 1.0,
        "charging_rate": 1.0,
        "coordinate_limit": 100.0,
        "demand_min": 1.0,
        "demand_max": 15.0,
        "time_window_start_min": 0.0,
        "time_window_start_max": 150.0,
        "time_window_width_min": 80.0,
        "time_window_width_max": 220.0,
        "service_time_min": 5.0,
        "service_time_max": 15.0,
        "seed": 2026,
    },
    {
        "name": "week3_c50_s8_seed2027",
        "num_customers": 50,
        "num_stations": 8,
        "vehicle_count": 10,
        "vehicle_capacity": 100.0,
        "battery_capacity": 300.0,
        "energy_consumption_rate": 1.0,
        "charging_rate": 1.0,
        "coordinate_limit": 100.0,
        "demand_min": 1.0,
        "demand_max": 15.0,
        "time_window_start_min": 0.0,
        "time_window_start_max": 200.0,
        "time_window_width_min": 80.0,
        "time_window_width_max": 240.0,
        "service_time_min": 5.0,
        "service_time_max": 15.0,
        "seed": 2027,
    },
    {
        "name": "week3_c100_s12_seed2028",
        "num_customers": 100,
        "num_stations": 12,
        "vehicle_count": 20,
        "vehicle_capacity": 120.0,
        "battery_capacity": 350.0,
        "energy_consumption_rate": 1.0,
        "charging_rate": 1.0,
        "coordinate_limit": 100.0,
        "demand_min": 1.0,
        "demand_max": 15.0,
        "time_window_start_min": 0.0,
        "time_window_start_max": 250.0,
        "time_window_width_min": 100.0,
        "time_window_width_max": 280.0,
        "service_time_min": 5.0,
        "service_time_max": 15.0,
        "seed": 2028,
    },
]


DEFAULT_RUN_SEEDS: list[int] = [11, 22, 33]


DEFAULT_GA_CONFIG: dict[str, Any] = {
    "population_size": 40,
    "generations": 80,
    "crossover_rate": 0.85,
    "mutation_rate": 0.20,
    "elite_size": 2,
    "tournament_size": 3,
}


QUICK_GA_CONFIG: dict[str, Any] = {
    "population_size": 12,
    "generations": 8,
    "crossover_rate": 0.85,
    "mutation_rate": 0.20,
    "elite_size": 1,
    "tournament_size": 2,
}


def build_default_week3_instances() -> list[Any]:
    """
    Build the default deterministic Week 3 benchmark instances.

    The instances are generated from fixed seeds. Therefore, every experiment run
    uses the same instance set, which is required for fair comparison.
    """

    instances: list[Any] = []

    for spec in DEFAULT_INSTANCE_SPECS:
        instance = generate_random_evrptw_instance(**spec)
        instances.append(instance)

    return instances


def get_instance_name(instance: Any) -> str:
    """
    Return a readable instance name.
    """

    name = getattr(instance, "name", None)

    if name is not None:
        return str(name)

    return "unknown_instance"


def get_customer_count(instance: Any) -> int:
    """
    Return the number of customers in the instance.
    """

    customers = getattr(instance, "customers", None)

    if customers is not None:
        return len(customers)

    nodes = getattr(instance, "nodes", None)

    if nodes is None:
        return 0

    if isinstance(nodes, dict):
        iterable_nodes = nodes.values()
    else:
        iterable_nodes = nodes

    count = 0

    for node in iterable_nodes:
        node_type = str(getattr(node, "node_type", getattr(node, "type", ""))).lower()

        if node_type == "customer":
            count += 1

    return count


def get_station_count(instance: Any) -> int:
    """
    Return the number of charging stations in the instance.
    """

    stations = getattr(instance, "stations", None)

    if stations is not None:
        return len(stations)

    nodes = getattr(instance, "nodes", None)

    if nodes is None:
        return 0

    if isinstance(nodes, dict):
        iterable_nodes = nodes.values()
    else:
        iterable_nodes = nodes

    count = 0

    for node in iterable_nodes:
        node_type = str(getattr(node, "node_type", getattr(node, "type", ""))).lower()

        if node_type == "station":
            count += 1

    return count


def to_plain_data(value: Any) -> Any:
    """
    Convert dataclasses and nested objects into JSON-serializable data.

    This helper makes the experiment output robust even if the evaluation result
    contains nested dataclasses such as violation summaries.
    """

    if is_dataclass(value):
        return to_plain_data(asdict(value))

    if isinstance(value, dict):
        return {str(key): to_plain_data(item) for key, item in value.items()}

    if isinstance(value, list):
        return [to_plain_data(item) for item in value]

    if isinstance(value, tuple):
        return [to_plain_data(item) for item in value]

    if isinstance(value, (str, int, float, bool)) or value is None:
        return value

    return str(value)


def safe_getattr(value: Any, name: str, default: Any = None) -> Any:
    """
    Safe getattr wrapper used by CSV flattening.
    """

    return getattr(value, name, default)


def extract_violation_field(evaluation: Any, field_name: str, default: Any = 0) -> Any:
    """
    Extract one field from evaluation.violations safely.
    """

    violations = safe_getattr(evaluation, "violations", None)

    if violations is None:
        return default

    return safe_getattr(violations, field_name, default)


def flatten_experiment_record(record: dict[str, Any]) -> dict[str, Any]:
    """
    Convert one detailed experiment record into a flat CSV row.

    The JSON output keeps all nested details. The CSV output keeps the most
    important table-friendly fields.
    """

    instance = record["instance"]
    method_result = record["method_result"]
    evaluation = record["evaluation"]
    ga_config = record["ga_config"]

    return {
        "instance_name": instance["name"],
        "num_customers": instance["num_customers"],
        "num_stations": instance["num_stations"],
        "method_name": method_result["method_name"],
        "run_seed": record["run_seed"],
        "total_distance": safe_getattr(evaluation, "total_distance", None),
        "runtime_seconds": safe_getattr(evaluation, "runtime_seconds", None),
        "feasible": safe_getattr(evaluation, "feasible", None),
        "served_customers": safe_getattr(evaluation, "served_customers", None),
        "unserved_customers": safe_getattr(evaluation, "unserved_customers", None),
        "capacity_violations": extract_violation_field(evaluation, "capacity", 0),
        "battery_violations": extract_violation_field(evaluation, "battery", 0),
        "time_window_violations": extract_violation_field(evaluation, "time_window", 0),
        "duplicate_customer_violations": extract_violation_field(
            evaluation,
            "duplicate_customer",
            0,
        ),
        "missing_customer_violations": extract_violation_field(
            evaluation,
            "missing_customer",
            0,
        ),
        "total_violations": extract_violation_field(evaluation, "total", 0),
        "raw_objective": method_result["raw_objective"],
        "raw_feasible": method_result["raw_feasible"],
        "population_size": ga_config["population_size"],
        "generations": ga_config["generations"],
        "crossover_rate": ga_config["crossover_rate"],
        "mutation_rate": ga_config["mutation_rate"],
        "elite_size": ga_config["elite_size"],
        "tournament_size": ga_config["tournament_size"],
    }


def run_single_week3_experiment(
    instance: Any,
    method_name: str,
    run_seed: int,
    ga_config: dict[str, Any],
) -> dict[str, Any]:
    """
    Run one method on one instance with one random seed.
    """

    method_result: MethodRunResult = run_week3_method(
        instance=instance,
        method_name=method_name,
        seed=run_seed,
        **ga_config,
    )

    evaluation = evaluate_solution(
        instance=instance,
        routes=method_result.routes,
        method_name=method_result.method_name,
        run_seed=run_seed,
        runtime_seconds=method_result.runtime_seconds,
    )

    record = {
        "instance": {
            "name": get_instance_name(instance),
            "num_customers": get_customer_count(instance),
            "num_stations": get_station_count(instance),
        },
        "method_name": method_name,
        "run_seed": run_seed,
        "ga_config": dict(ga_config),
        "method_result": {
            "method_name": method_result.method_name,
            "routes": method_result.routes,
            "runtime_seconds": method_result.runtime_seconds,
            "raw_objective": method_result.raw_objective,
            "raw_feasible": method_result.raw_feasible,
            "raw_messages": method_result.raw_messages,
            "metadata": method_result.metadata,
        },
        "evaluation": evaluation,
    }

    return record


def run_week3_baseline_experiments(
    instances: Iterable[Any] | None = None,
    run_seeds: Iterable[int] | None = None,
    ga_config: dict[str, Any] | None = None,
    method_name: str = "ga_baseline",
) -> list[dict[str, Any]]:
    """
    Run the baseline GA on all selected Week 3 instances and seeds.
    """

    if instances is None:
        instances = build_default_week3_instances()

    if run_seeds is None:
        run_seeds = DEFAULT_RUN_SEEDS

    if ga_config is None:
        ga_config = DEFAULT_GA_CONFIG

    records: list[dict[str, Any]] = []

    for instance in instances:
        instance_name = get_instance_name(instance)

        for run_seed in run_seeds:
            print(
                f"[Week 3] Running {method_name} on {instance_name} "
                f"with seed={run_seed}..."
            )

            record = run_single_week3_experiment(
                instance=instance,
                method_name=method_name,
                run_seed=int(run_seed),
                ga_config=ga_config,
            )

            records.append(record)

    return records


def save_records_to_json(records: list[dict[str, Any]], output_path: str | Path) -> None:
    """
    Save detailed experiment records to JSON.
    """

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    plain_records = to_plain_data(records)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(
            plain_records,
            file,
            indent=2,
            ensure_ascii=False,
        )


def save_records_to_csv(records: list[dict[str, Any]], output_path: str | Path) -> None:
    """
    Save flattened experiment records to CSV.
    """

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows = [flatten_experiment_record(record) for record in records]

    if not rows:
        with output_path.open("w", encoding="utf-8", newline="") as file:
            file.write("")
        return

    fieldnames = list(rows[0].keys())

    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def save_week3_baseline_outputs(
    records: list[dict[str, Any]],
    output_dir: str | Path = "results/week3",
    csv_filename: str = "baseline_results.csv",
    json_filename: str = "baseline_results.json",
) -> tuple[Path, Path]:
    """
    Save both CSV and JSON experiment outputs.
    """

    output_dir = Path(output_dir)
    csv_path = output_dir / csv_filename
    json_path = output_dir / json_filename

    save_records_to_csv(records, csv_path)
    save_records_to_json(records, json_path)

    return csv_path, json_path
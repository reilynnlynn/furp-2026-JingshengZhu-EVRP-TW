from __future__ import annotations

import csv
import json

from src.experiments.week3_baseline_runner import (
    QUICK_GA_CONFIG,
    flatten_experiment_record,
    run_single_week3_experiment,
    run_week3_baseline_experiments,
    save_week3_baseline_outputs,
)
from src.generator import generate_random_evrptw_instance


def make_runner_test_instance():
    return generate_random_evrptw_instance(
        name="test_week3_baseline_runner",
        num_customers=6,
        num_stations=2,
        vehicle_count=3,
        vehicle_capacity=100.0,
        battery_capacity=500.0,
        energy_consumption_rate=1.0,
        charging_rate=1.0,
        coordinate_limit=30.0,
        demand_min=1.0,
        demand_max=10.0,
        time_window_start_min=0.0,
        time_window_start_max=20.0,
        time_window_width_min=300.0,
        time_window_width_max=500.0,
        service_time_min=0.0,
        service_time_max=2.0,
        seed=2026,
    )


def test_run_single_week3_experiment_returns_record() -> None:
    instance = make_runner_test_instance()

    record = run_single_week3_experiment(
        instance=instance,
        method_name="ga_baseline",
        run_seed=11,
        ga_config=QUICK_GA_CONFIG,
    )

    assert record["instance"]["name"] == "test_week3_baseline_runner"
    assert record["instance"]["num_customers"] == 6
    assert record["instance"]["num_stations"] == 2
    assert record["method_name"] == "ga_baseline"
    assert record["run_seed"] == 11
    assert record["method_result"]["method_name"] == "ga_baseline"
    assert "evaluation" in record


def test_flatten_experiment_record_contains_table_fields() -> None:
    instance = make_runner_test_instance()

    record = run_single_week3_experiment(
        instance=instance,
        method_name="ga_baseline",
        run_seed=12,
        ga_config=QUICK_GA_CONFIG,
    )

    row = flatten_experiment_record(record)

    expected_fields = {
        "instance_name",
        "num_customers",
        "num_stations",
        "method_name",
        "run_seed",
        "total_distance",
        "runtime_seconds",
        "feasible",
        "served_customers",
        "unserved_customers",
        "capacity_violations",
        "battery_violations",
        "time_window_violations",
        "duplicate_customer_violations",
        "missing_customer_violations",
        "total_violations",
        "raw_objective",
        "raw_feasible",
        "population_size",
        "generations",
        "crossover_rate",
        "mutation_rate",
        "elite_size",
        "tournament_size",
    }

    assert expected_fields.issubset(set(row.keys()))
    assert row["instance_name"] == "test_week3_baseline_runner"
    assert row["method_name"] == "ga_baseline"
    assert row["run_seed"] == 12


def test_run_week3_baseline_experiments_returns_multiple_records() -> None:
    instance = make_runner_test_instance()

    records = run_week3_baseline_experiments(
        instances=[instance],
        run_seeds=[21, 22],
        ga_config=QUICK_GA_CONFIG,
        method_name="ga_baseline",
    )

    assert len(records) == 2
    assert records[0]["run_seed"] == 21
    assert records[1]["run_seed"] == 22


def test_save_week3_baseline_outputs_creates_csv_and_json(tmp_path) -> None:
    instance = make_runner_test_instance()

    records = run_week3_baseline_experiments(
        instances=[instance],
        run_seeds=[31],
        ga_config=QUICK_GA_CONFIG,
        method_name="ga_baseline",
    )

    csv_path, json_path = save_week3_baseline_outputs(
        records=records,
        output_dir=tmp_path,
        csv_filename="test_baseline_results.csv",
        json_filename="test_baseline_results.json",
    )

    assert csv_path.exists()
    assert json_path.exists()

    with csv_path.open("r", encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))

    assert len(rows) == 1
    assert rows[0]["instance_name"] == "test_week3_baseline_runner"
    assert rows[0]["method_name"] == "ga_baseline"
    assert rows[0]["run_seed"] == "31"

    with json_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["instance"]["name"] == "test_week3_baseline_runner"
    assert data[0]["method_result"]["method_name"] == "ga_baseline"
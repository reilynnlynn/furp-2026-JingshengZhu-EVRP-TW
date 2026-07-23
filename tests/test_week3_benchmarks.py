from __future__ import annotations

from pathlib import Path

from src.benchmarks.week3_instances import (
    generate_week3_instance,
    generate_and_save_week3_benchmarks,
    load_instance_json,
    save_instance_json,
    summarize_instance,
)


def test_generate_week3_instance_basic_properties() -> None:
    instance = generate_week3_instance(num_customers=20, seed=1)

    assert instance.name == "week3_c20_s1"
    assert len(instance.customers) == 20
    assert len(instance.stations) == 4
    assert instance.vehicle_count == 5
    assert instance.depot_id == 0
    assert instance.vehicle_capacity == 100.0
    assert instance.battery_capacity == 120.0


def test_generate_week3_instance_reproducible_with_same_seed() -> None:
    instance_a = generate_week3_instance(num_customers=20, seed=1)
    instance_b = generate_week3_instance(num_customers=20, seed=1)

    assert instance_a.name == instance_b.name
    assert len(instance_a.nodes) == len(instance_b.nodes)

    for node_a, node_b in zip(instance_a.nodes, instance_b.nodes):
        assert node_a.id == node_b.id
        assert node_a.x == node_b.x
        assert node_a.y == node_b.y
        assert node_a.node_type == node_b.node_type
        assert node_a.demand == node_b.demand
        assert node_a.ready_time == node_b.ready_time
        assert node_a.due_time == node_b.due_time
        assert node_a.service_time == node_b.service_time


def test_save_and_load_instance_json(tmp_path: Path) -> None:
    instance = generate_week3_instance(num_customers=20, seed=2)
    output_path = tmp_path / "instance.json"

    save_instance_json(instance, output_path)

    assert output_path.exists()

    loaded = load_instance_json(output_path)

    assert loaded.name == instance.name
    assert loaded.depot_id == instance.depot_id
    assert loaded.vehicle_count == instance.vehicle_count
    assert loaded.vehicle_capacity == instance.vehicle_capacity
    assert loaded.battery_capacity == instance.battery_capacity
    assert len(loaded.customers) == len(instance.customers)
    assert len(loaded.stations) == len(instance.stations)


def test_generate_and_save_week3_benchmarks_small_subset(tmp_path: Path) -> None:
    generated_paths = generate_and_save_week3_benchmarks(
        output_dir=tmp_path,
        sizes=[20],
        seeds=[1, 2],
    )

    assert len(generated_paths) == 2

    for path in generated_paths:
        assert path.exists()
        loaded = load_instance_json(path)
        assert len(loaded.customers) == 20
        assert loaded.vehicle_count == 5


def test_summarize_instance() -> None:
    instance = generate_week3_instance(num_customers=50, seed=3)
    summary = summarize_instance(instance)

    assert summary["name"] == "week3_c50_s3"
    assert summary["customers"] == 50
    assert summary["stations"] == 8
    assert summary["vehicles"] == 10
    assert summary["vehicle_capacity"] == 100.0
    assert summary["battery_capacity"] == 120.0
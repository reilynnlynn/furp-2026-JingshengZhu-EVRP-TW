from __future__ import annotations

import csv
from pathlib import Path
from statistics import mean

from src.baselines.week2_methods import (
    ga_style_order,
    nearest_neighbor_order,
    or_sweep_order,
    pomo_style_order,
    random_order,
    run_order_based_baseline,
)
from src.generator import generate_random_evrptw_instance


RESULTS_DIR = Path("results")
CSV_PATH = RESULTS_DIR / "week2_comparison.csv"
SUMMARY_PATH = RESULTS_DIR / "week2_comparison_summary.md"


def vehicle_count_for_size(size: int) -> int:
    """
    A simple scaling rule for synthetic EVRP-TW experiments.

    More customers require more vehicles. This prevents large instances from
    being impossible only because of an artificially tiny fleet.
    """
    return max(5, size // 8)


def station_count_for_size(size: int) -> int:
    return max(3, size // 20)


def make_instance(size: int, seed: int):
    """
    Generate an EVRP-TW benchmark instance.

    The time windows and capacities are moderately relaxed. This is intentional
    for Week 2 baseline recreation because we want feasibility comparison across
    methods, not universal failure from over-constrained random data.
    """
    return generate_random_evrptw_instance(
        name=f"week2_{size}_customers_seed_{seed}",
        num_customers=size,
        num_stations=station_count_for_size(size),
        vehicle_count=vehicle_count_for_size(size),
        vehicle_capacity=120.0,
        battery_capacity=600.0,
        energy_consumption_rate=1.0,
        charging_rate=1.0,
        coordinate_limit=100.0,
        demand_min=1.0,
        demand_max=10.0,
        time_window_start_min=0.0,
        time_window_start_max=200.0,
        time_window_width_min=400.0,
        time_window_width_max=800.0,
        service_time_min=5.0,
        service_time_max=10.0,
        seed=seed,
    )


def run_one_instance(size: int, seed: int) -> list[dict]:
    instance = make_instance(size, seed)

    methods = [
        (
            "random",
            lambda: random_order(instance, seed=seed),
            "Random customer permutation baseline.",
        ),
        (
            "nearest_neighbor",
            lambda: nearest_neighbor_order(instance),
            "Greedy nearest-neighbor constructive baseline.",
        ),
        (
            "pomo_style",
            lambda: pomo_style_order(instance, rollout_limit=16),
            "POMO-style multi-start constructive baseline.",
        ),
        (
            "ga_style",
            lambda: ga_style_order(
                instance,
                seed=seed,
                population_size=24,
                generations=25,
                mutation_rate=0.20,
            ),
            "Permutation-based GA baseline.",
        ),
        (
            "or_sweep",
            lambda: or_sweep_order(instance),
            "OR-style sweep heuristic baseline.",
        ),
    ]

    rows: list[dict] = []

    for method_name, builder, description in methods:
        _solution, result = run_order_based_baseline(
            instance=instance,
            method_name=method_name,
            order_builder=builder,
        )

        rows.append(
            {
                "size": size,
                "seed": seed,
                "method": result.method,
                "method_description": description,
                "feasible": result.feasible,
                "checker_feasible": result.checker_feasible,
                "assigned_customers": result.assigned_customers,
                "unassigned_customers": result.unassigned_customers,
                "route_count": result.route_count,
                "total_distance": round(result.total_distance, 4),
                "runtime_seconds": round(result.runtime_seconds, 6),
                "decoder_message": result.decoder_message,
            }
        )

    return rows


def write_csv(rows: list[dict]) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "size",
        "seed",
        "method",
        "method_description",
        "feasible",
        "checker_feasible",
        "assigned_customers",
        "unassigned_customers",
        "route_count",
        "total_distance",
        "runtime_seconds",
        "decoder_message",
    ]

    with CSV_PATH.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def grouped(rows: list[dict], size: int, method: str) -> list[dict]:
    return [
        row for row in rows
        if row["size"] == size and row["method"] == method
    ]


def write_summary(rows: list[dict]) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    sizes = sorted({int(row["size"]) for row in rows})
    methods = sorted({str(row["method"]) for row in rows})

    lines: list[str] = []
    lines.append("# Week 2 Baseline Comparison Summary")
    lines.append("")
    lines.append("## Requirement Mapping")
    lines.append("")
    lines.append("This experiment addresses the Week 2 lab objective:")
    lines.append("")
    lines.append("> Review baseline methods, recreate them, and compare results and methodologies.")
    lines.append("")
    lines.append("The implemented baselines are:")
    lines.append("")
    lines.append("- `random`: random permutation baseline.")
    lines.append("- `nearest_neighbor`: greedy constructive baseline.")
    lines.append("- `pomo_style`: lightweight POMO-style multi-start constructive baseline.")
    lines.append("- `ga_style`: permutation-based genetic algorithm baseline.")
    lines.append("- `or_sweep`: operations-research style sweep heuristic baseline.")
    lines.append("")
    lines.append("All baselines generate a customer order, which is decoded by the shared multi-route EVRP-TW decoder.")
    lines.append("")
    lines.append("## Aggregated Results")
    lines.append("")
    lines.append("| Size | Method | Feasibility Rate | Avg. Unassigned | Avg. Routes | Avg. Distance | Avg. Runtime (s) |")
    lines.append("|---:|---|---:|---:|---:|---:|---:|")

    for size in sizes:
        for method in methods:
            subset = grouped(rows, size, method)
            if not subset:
                continue

            feasibility_rate = mean(1.0 if row["feasible"] else 0.0 for row in subset)
            avg_unassigned = mean(float(row["unassigned_customers"]) for row in subset)
            avg_routes = mean(float(row["route_count"]) for row in subset)
            avg_distance = mean(float(row["total_distance"]) for row in subset)
            avg_runtime = mean(float(row["runtime_seconds"]) for row in subset)

            lines.append(
                f"| {size} | {method} | {feasibility_rate:.2f} | "
                f"{avg_unassigned:.2f} | {avg_routes:.2f} | "
                f"{avg_distance:.2f} | {avg_runtime:.4f} |"
            )

    lines.append("")
    lines.append("## Short Interpretation")
    lines.append("")
    lines.append("- Feasibility is evaluated by whether all customers are assigned and the checker confirms the solution.")
    lines.append("- Distance is only meaningful when feasibility is comparable; an infeasible method may look short because it serves fewer customers.")
    lines.append("- The POMO-style baseline recreates the multi-start idea of POMO without training a neural policy.")
    lines.append("- The GA-style baseline searches over customer permutations and uses EVRP-TW decoding/checking as its constraint mechanism.")
    lines.append("- The OR-style sweep baseline provides a classical heuristic comparison point.")
    lines.append("- Larger 100/200-customer cases are harder because route splitting, fleet limits, capacity, time windows, and battery-return constraints interact.")
    lines.append("")

    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    sizes = [50, 100, 200]
    seeds = [1, 2, 3]

    all_rows: list[dict] = []

    print("Running Week 2 baseline comparison...")
    print(f"Sizes: {sizes}")
    print(f"Seeds: {seeds}")

    for size in sizes:
        for seed in seeds:
            print(f"\nInstance size={size}, seed={seed}")
            rows = run_one_instance(size, seed)
            all_rows.extend(rows)

            for row in rows:
                print(
                    f"  {row['method']:<16} "
                    f"feasible={str(row['feasible']):<5} "
                    f"assigned={row['assigned_customers']:<4} "
                    f"unassigned={row['unassigned_customers']:<4} "
                    f"routes={row['route_count']:<3} "
                    f"distance={row['total_distance']:<10} "
                    f"runtime={row['runtime_seconds']}"
                )

    write_csv(all_rows)
    write_summary(all_rows)

    print("\nDone.")
    print(f"CSV written to: {CSV_PATH}")
    print(f"Summary written to: {SUMMARY_PATH}")


if __name__ == "__main__":
    main()
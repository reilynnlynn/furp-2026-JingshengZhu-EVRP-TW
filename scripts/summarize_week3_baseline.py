from __future__ import annotations

import csv
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_INPUT_CSV = PROJECT_ROOT / "results" / "week3" / "baseline_results.csv"
DEFAULT_OUTPUT_CSV = PROJECT_ROOT / "results" / "week3" / "baseline_summary.csv"
DEFAULT_OUTPUT_MD = PROJECT_ROOT / "results" / "week3" / "baseline_summary.md"


def parse_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    if value is None:
        return default

    text = str(value).strip()

    if text == "":
        return default

    try:
        number = float(text)
    except ValueError:
        return default

    if math.isnan(number):
        return default

    return number


def parse_int(value: Any, default: int = 0) -> int:
    if value is None:
        return default

    text = str(value).strip()

    if text == "":
        return default

    try:
        return int(float(text))
    except ValueError:
        return default


def parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value

    if value is None:
        return False

    text = str(value).strip().lower()

    return text in {"true", "1", "yes", "y"}


def get_numeric_field(row: Dict[str, Any], field_names: List[str], default: Optional[float] = None) -> Optional[float]:
    for field_name in field_names:
        if field_name in row:
            value = parse_float(row.get(field_name), default=None)
            if value is not None:
                return value

    return default


def average(values: List[float], default: float = 0.0) -> float:
    clean_values = [value for value in values if value is not None]

    if not clean_values:
        return default

    return mean(clean_values)


def read_rows(input_csv: Path) -> List[Dict[str, Any]]:
    if not input_csv.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_csv}")

    with input_csv.open("r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return list(reader)


def summarize_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    groups: Dict[int, List[Dict[str, Any]]] = defaultdict(list)

    for row in rows:
        customer_count = parse_int(row.get("num_customers"), default=0)
        groups[customer_count].append(row)

    summaries: List[Dict[str, Any]] = []

    for customer_count in sorted(groups.keys()):
        group_rows = groups[customer_count]
        runs = len(group_rows)

        station_counts = [
            parse_int(row.get("num_stations"), default=0)
            for row in group_rows
        ]
        station_count = max(set(station_counts), key=station_counts.count) if station_counts else 0

        feasible_values = [
            parse_bool(row.get("feasible"))
            for row in group_rows
        ]

        feasible_rate = sum(1 for value in feasible_values if value) / runs if runs else 0.0

        served_customers = [
            parse_float(row.get("served_customers"), default=0.0) or 0.0
            for row in group_rows
        ]

        unserved_customers = [
            parse_float(row.get("unserved_customers"), default=0.0) or 0.0
            for row in group_rows
        ]

        route_counts = [
            parse_float(row.get("route_count"), default=0.0) or 0.0
            for row in group_rows
        ]

        # Important:
        # The current baseline runner writes distance as "best_distance".
        # Older versions may have used "total_distance", "distance", or "objective".
        all_distances = [
            get_numeric_field(
                row,
                ["best_distance", "total_distance", "distance", "objective"],
                default=None,
            )
            for row in group_rows
        ]
        all_distances_clean = [
            value for value in all_distances
            if value is not None
        ]

        feasible_distances = [
            distance
            for row, distance in zip(group_rows, all_distances)
            if parse_bool(row.get("feasible")) and distance is not None
        ]

        runtimes = [
            parse_float(row.get("runtime_seconds"), default=0.0) or 0.0
            for row in group_rows
        ]

        total_violations = [
            parse_float(row.get("total_violations"), default=0.0) or 0.0
            for row in group_rows
        ]

        capacity_violations = [
            parse_float(row.get("capacity_violations"), default=0.0) or 0.0
            for row in group_rows
        ]

        battery_violations = [
            parse_float(row.get("battery_violations"), default=0.0) or 0.0
            for row in group_rows
        ]

        time_window_violations = [
            parse_float(row.get("time_window_violations"), default=0.0) or 0.0
            for row in group_rows
        ]

        missing_customer_violations = [
            parse_float(row.get("missing_customer_violations"), default=None)
            for row in group_rows
        ]

        if all(value is None for value in missing_customer_violations):
            missing_customer_violations = [
                parse_float(row.get("coverage_violations"), default=0.0) or 0.0
                for row in group_rows
            ]
        else:
            missing_customer_violations = [
                value or 0.0
                for value in missing_customer_violations
            ]

        summary = {
            "customer_count": customer_count,
            "station_count": station_count,
            "runs": runs,
            "feasible_rate": feasible_rate,
            "avg_served_customers": average(served_customers),
            "avg_unserved_customers": average(unserved_customers),
            "avg_route_count": average(route_counts),
            "avg_total_distance_all_runs": average(all_distances_clean),
            "avg_total_distance_feasible_runs": average(feasible_distances, default=float("nan")),
            "avg_runtime_seconds": average(runtimes),
            "avg_total_violations": average(total_violations),
            "avg_capacity_violations": average(capacity_violations),
            "avg_battery_violations": average(battery_violations),
            "avg_time_window_violations": average(time_window_violations),
            "avg_missing_customer_violations": average(missing_customer_violations),
        }

        summaries.append(summary)

    return summaries


def format_float(value: Any, digits: int = 4) -> str:
    if value is None:
        return ""

    try:
        number = float(value)
    except ValueError:
        return ""

    if math.isnan(number):
        return ""

    return f"{number:.{digits}f}"


def write_summary_csv(summaries: List[Dict[str, Any]], output_csv: Path) -> None:
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "customer_count",
        "station_count",
        "runs",
        "feasible_rate",
        "avg_served_customers",
        "avg_unserved_customers",
        "avg_route_count",
        "avg_total_distance_all_runs",
        "avg_total_distance_feasible_runs",
        "avg_runtime_seconds",
        "avg_total_violations",
        "avg_capacity_violations",
        "avg_battery_violations",
        "avg_time_window_violations",
        "avg_missing_customer_violations",
    ]

    with output_csv.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summaries)


def write_summary_md(summaries: List[Dict[str, Any]], output_md: Path) -> None:
    output_md.parent.mkdir(parents=True, exist_ok=True)

    lines: List[str] = []

    lines.append("# Week 3 Baseline GA Summary")
    lines.append("")
    lines.append("This table summarizes the baseline GA experiment results by customer size.")
    lines.append("")
    lines.append("## Summary Table")
    lines.append("")
    lines.append(
        "| Customer Count | Stations | Runs | Feasible Rate | Avg Served | Avg Unserved | Avg Routes | "
        "Avg Distance All Runs | Avg Distance Feasible Runs | Avg Runtime (s) | Avg Total Violations | "
        "Avg Capacity Viol. | Avg Battery Viol. | Avg TW Viol. | Avg Missing Viol. |"
    )
    lines.append(
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"
    )

    for summary in summaries:
        lines.append(
            "| "
            f"{summary['customer_count']} | "
            f"{summary['station_count']} | "
            f"{summary['runs']} | "
            f"{format_float(summary['feasible_rate'])} | "
            f"{format_float(summary['avg_served_customers'])} | "
            f"{format_float(summary['avg_unserved_customers'])} | "
            f"{format_float(summary['avg_route_count'])} | "
            f"{format_float(summary['avg_total_distance_all_runs'])} | "
            f"{format_float(summary['avg_total_distance_feasible_runs'])} | "
            f"{format_float(summary['avg_runtime_seconds'])} | "
            f"{format_float(summary['avg_total_violations'])} | "
            f"{format_float(summary['avg_capacity_violations'])} | "
            f"{format_float(summary['avg_battery_violations'])} | "
            f"{format_float(summary['avg_time_window_violations'])} | "
            f"{format_float(summary['avg_missing_customer_violations'])} |"
        )

    lines.append("")
    lines.append("## Metric Definitions")
    lines.append("")
    lines.append("- `Feasible Rate`: fraction of runs where the produced solution satisfies the EVRP-TW checker.")
    lines.append("- `Avg Served`: average number of customers included in the final solution.")
    lines.append("- `Avg Unserved`: average number of customers not included in the final solution.")
    lines.append("- `Avg Routes`: average number of vehicle routes used.")
    lines.append("- `Avg Distance All Runs`: average best route distance over all runs, including infeasible runs.")
    lines.append("- `Avg Distance Feasible Runs`: average best route distance only among feasible runs.")
    lines.append("- `Avg Runtime`: average wall-clock runtime in seconds.")
    lines.append("- `Avg Total Violations`: average number of violation messages returned by the evaluator.")
    lines.append("- `Avg Capacity Viol.`: average number of detected capacity-related violations.")
    lines.append("- `Avg Battery Viol.`: average number of detected battery-related violations.")
    lines.append("- `Avg TW Viol.`: average number of detected time-window-related violations.")
    lines.append("- `Avg Missing Viol.`: average number of detected missing-customer or coverage violations.")
    lines.append("")
    lines.append("## Initial Observation")
    lines.append("")
    lines.append(
        "The baseline GA serves all customers in these benchmark instances, but it does not explicitly repair "
        "battery and time-window violations. As a result, the feasible rate is 0 on the tested instances, "
        "and the number of violations increases as the customer count grows. This motivates the enhanced GA "
        "component in the next stage."
    )
    lines.append("")

    output_md.write_text("\n".join(lines), encoding="utf-8")


def print_summary(summaries: List[Dict[str, Any]]) -> None:
    print("Week 3 Baseline GA Summary")
    print("=" * 100)

    for summary in summaries:
        feasible_distance = format_float(summary["avg_total_distance_feasible_runs"])

        if feasible_distance == "":
            feasible_distance = "N/A"

        print(
            "customers={customer_count}, stations={station_count}, runs={runs}, "
            "feasible_rate={feasible_rate:.4f}, "
            "avg_distance_all={avg_total_distance_all_runs:.2f}, "
            "avg_distance_feasible={feasible_distance}, "
            "avg_runtime={avg_runtime_seconds:.4f}, "
            "avg_total_violations={avg_total_violations:.2f}, "
            "avg_capacity_viol={avg_capacity_violations:.2f}, "
            "avg_battery_viol={avg_battery_violations:.2f}, "
            "avg_tw_viol={avg_time_window_violations:.2f}, "
            "avg_missing_viol={avg_missing_customer_violations:.2f}".format(
                feasible_distance=feasible_distance,
                **summary,
            )
        )

    print("=" * 100)


def main() -> None:
    rows = read_rows(DEFAULT_INPUT_CSV)
    summaries = summarize_rows(rows)

    write_summary_csv(summaries, DEFAULT_OUTPUT_CSV)
    write_summary_md(summaries, DEFAULT_OUTPUT_MD)
    print_summary(summaries)

    print(f"Wrote CSV summary to: {DEFAULT_OUTPUT_CSV}")
    print(f"Wrote Markdown summary to: {DEFAULT_OUTPUT_MD}")


if __name__ == "__main__":
    main()
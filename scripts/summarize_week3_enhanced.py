from __future__ import annotations

import csv
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any, Dict, Iterable, List, Optional, Tuple


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_INPUT_CSV = PROJECT_ROOT / "results" / "week3" / "enhanced_results.csv"
DEFAULT_OUTPUT_CSV = PROJECT_ROOT / "results" / "week3" / "enhanced_summary.csv"
DEFAULT_OUTPUT_MD = PROJECT_ROOT / "results" / "week3" / "enhanced_summary.md"


def parse_float(value: Any) -> Optional[float]:
    if value is None:
        return None

    text = str(value).strip()
    if text == "":
        return None

    lowered = text.lower()
    if lowered in {"none", "nan", "null"}:
        return None

    try:
        number = float(text)
    except ValueError:
        return None

    if math.isnan(number) or math.isinf(number):
        return None

    return number


def parse_int(value: Any) -> Optional[int]:
    number = parse_float(value)
    if number is None:
        return None
    return int(number)


def parse_bool(value: Any) -> Optional[bool]:
    if value is None:
        return None

    text = str(value).strip().lower()

    if text in {"true", "1", "yes", "y"}:
        return True

    if text in {"false", "0", "no", "n"}:
        return False

    return None


def first_existing(row: Dict[str, Any], names: Iterable[str]) -> Any:
    for name in names:
        if name in row:
            return row[name]
    return None


def get_metric(row: Dict[str, Any], candidates: Iterable[str]) -> Optional[float]:
    return parse_float(first_existing(row, candidates))


def get_int_metric(row: Dict[str, Any], candidates: Iterable[str]) -> Optional[int]:
    return parse_int(first_existing(row, candidates))


def average(values: Iterable[Optional[float]]) -> Optional[float]:
    valid = [value for value in values if value is not None]
    if not valid:
        return None
    return mean(valid)


def format_number(value: Optional[float], digits: int = 3) -> str:
    if value is None:
        return ""
    return f"{value:.{digits}f}"


def load_rows(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Cannot find enhanced results CSV: {path}")

    with path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        rows = list(reader)

    if not rows:
        raise ValueError(f"Enhanced results CSV is empty: {path}")

    return rows


def group_key(row: Dict[str, Any]) -> Tuple[int, int]:
    num_customers = get_int_metric(
        row,
        [
            "num_customers",
            "customer_count",
            "customers",
            "n_customers",
        ],
    )

    num_stations = get_int_metric(
        row,
        [
            "num_stations",
            "station_count",
            "stations",
            "n_stations",
        ],
    )

    if num_customers is None:
        raise ValueError(f"Cannot find customer-count field in row: {row}")

    if num_stations is None:
        num_stations = -1

    return num_customers, num_stations


def summarize_group(num_customers: int, num_stations: int, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    feasible_values = [
        parse_bool(first_existing(row, ["feasible", "is_feasible"]))
        for row in rows
    ]
    feasible_values = [value for value in feasible_values if value is not None]

    feasible_rate: Optional[float]
    if feasible_values:
        feasible_rate = sum(1 for value in feasible_values if value) / len(feasible_values)
    else:
        feasible_rate = None

    served_values = [
        get_metric(row, ["served_customers", "num_served", "served"])
        for row in rows
    ]

    unserved_values = [
        get_metric(row, ["unserved_customers", "num_unserved", "unserved"])
        for row in rows
    ]

    route_values = [
        get_metric(row, ["route_count", "num_routes", "routes"])
        for row in rows
    ]

    distance_values = [
        get_metric(row, ["distance", "total_distance", "best_distance"])
        for row in rows
    ]

    runtime_values = [
        get_metric(row, ["runtime_seconds", "runtime", "time_seconds"])
        for row in rows
    ]

    total_violation_values = [
        get_metric(row, ["total_violations", "total_violation_count", "violation_count", "violations"])
        for row in rows
    ]

    battery_violation_values = [
        get_metric(row, ["battery_violations", "battery_violation_count"])
        for row in rows
    ]

    time_window_violation_values = [
        get_metric(row, ["time_window_violations", "time_window_violation_count", "tw_violations"])
        for row in rows
    ]

    capacity_violation_values = [
        get_metric(row, ["capacity_violations", "capacity_violation_count"])
        for row in rows
    ]

    customer_violation_values = [
        get_metric(row, ["customer_violations", "customer_violation_count"])
        for row in rows
    ]

    return {
        "num_customers": num_customers,
        "num_stations": num_stations,
        "runs": len(rows),
        "feasible_rate": feasible_rate,
        "avg_served_customers": average(served_values),
        "avg_unserved_customers": average(unserved_values),
        "avg_routes": average(route_values),
        "avg_distance_all": average(distance_values),
        "avg_runtime_seconds": average(runtime_values),
        "avg_total_violations": average(total_violation_values),
        "avg_battery_violations": average(battery_violation_values),
        "avg_time_window_violations": average(time_window_violation_values),
        "avg_capacity_violations": average(capacity_violation_values),
        "avg_customer_violations": average(customer_violation_values),
    }


def summarize(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[Tuple[int, int], List[Dict[str, Any]]] = defaultdict(list)

    for row in rows:
        key = group_key(row)
        grouped[key].append(row)

    summaries: List[Dict[str, Any]] = []

    for key in sorted(grouped.keys()):
        num_customers, num_stations = key
        summaries.append(
            summarize_group(
                num_customers=num_customers,
                num_stations=num_stations,
                rows=grouped[key],
            )
        )

    return summaries


def write_summary_csv(summaries: List[Dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "num_customers",
        "num_stations",
        "runs",
        "feasible_rate",
        "avg_served_customers",
        "avg_unserved_customers",
        "avg_routes",
        "avg_distance_all",
        "avg_runtime_seconds",
        "avg_total_violations",
        "avg_battery_violations",
        "avg_time_window_violations",
        "avg_capacity_violations",
        "avg_customer_violations",
    ]

    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for row in summaries:
            writer.writerow(row)


def make_markdown(summaries: List[Dict[str, Any]]) -> str:
    lines: List[str] = []

    lines.append("# Week 3 Enhanced GA Summary")
    lines.append("")
    lines.append(
        "This table summarizes the enhanced GA experiment results by customer size. "
        "The enhanced method is evaluated using the same benchmark instances and algorithm seeds "
        "as the baseline GA."
    )
    lines.append("")
    lines.append("## Summary Table")
    lines.append("")
    lines.append(
        "| Customer Count | Stations | Runs | Feasible Rate | Avg Served | Avg Unserved | "
        "Avg Routes | Avg Distance | Avg Runtime (s) | Avg Violations | Battery Viol. | "
        "Time-Window Viol. | Capacity Viol. | Customer Viol. |"
    )
    lines.append(
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"
    )

    for row in summaries:
        feasible_rate = row["feasible_rate"]
        feasible_rate_text = "" if feasible_rate is None else f"{feasible_rate:.3f}"

        lines.append(
            f"| {row['num_customers']} "
            f"| {row['num_stations']} "
            f"| {row['runs']} "
            f"| {feasible_rate_text} "
            f"| {format_number(row['avg_served_customers'])} "
            f"| {format_number(row['avg_unserved_customers'])} "
            f"| {format_number(row['avg_routes'])} "
            f"| {format_number(row['avg_distance_all'])} "
            f"| {format_number(row['avg_runtime_seconds'])} "
            f"| {format_number(row['avg_total_violations'])} "
            f"| {format_number(row['avg_battery_violations'])} "
            f"| {format_number(row['avg_time_window_violations'])} "
            f"| {format_number(row['avg_capacity_violations'])} "
            f"| {format_number(row['avg_customer_violations'])} |"
        )

    lines.append("")
    lines.append("## Initial Observation")
    lines.append("")
    lines.append(
        "The enhanced GA is designed to improve constraint handling compared with the baseline GA. "
        "The most important comparison is not only the feasible rate, but also whether the enhanced "
        "method reduces battery, time-window, capacity, and customer-service violations."
    )
    lines.append("")

    return "\n".join(lines)


def write_summary_md(summaries: List[Dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    markdown = make_markdown(summaries)
    path.write_text(markdown, encoding="utf-8")


def print_summary(summaries: List[Dict[str, Any]]) -> None:
    print("Week 3 Enhanced GA Summary")
    print("=" * 100)

    for row in summaries:
        feasible_rate = row["feasible_rate"]
        feasible_rate_text = "NA" if feasible_rate is None else f"{feasible_rate:.3f}"

        print(
            "customers={customers}, stations={stations}, runs={runs}, "
            "feasible_rate={feasible_rate}, avg_distance={distance}, "
            "avg_violations={violations}, avg_runtime={runtime}".format(
                customers=row["num_customers"],
                stations=row["num_stations"],
                runs=row["runs"],
                feasible_rate=feasible_rate_text,
                distance=format_number(row["avg_distance_all"]),
                violations=format_number(row["avg_total_violations"]),
                runtime=format_number(row["avg_runtime_seconds"]),
            )
        )

    print("=" * 100)


def main() -> None:
    rows = load_rows(DEFAULT_INPUT_CSV)
    summaries = summarize(rows)

    write_summary_csv(summaries, DEFAULT_OUTPUT_CSV)
    write_summary_md(summaries, DEFAULT_OUTPUT_MD)
    print_summary(summaries)

    print(f"Summary CSV written to: {DEFAULT_OUTPUT_CSV}")
    print(f"Summary Markdown written to: {DEFAULT_OUTPUT_MD}")


if __name__ == "__main__":
    main()
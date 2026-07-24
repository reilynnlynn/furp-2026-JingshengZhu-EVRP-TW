from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Any, Dict, List, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[1]

BASELINE_SUMMARY = PROJECT_ROOT / "results" / "week3" / "baseline_summary.csv"
ENHANCED_SUMMARY = PROJECT_ROOT / "results" / "week3" / "enhanced_summary.csv"

OUTPUT_CSV = PROJECT_ROOT / "results" / "week3" / "baseline_vs_enhanced_comparison.csv"
OUTPUT_MD = PROJECT_ROOT / "results" / "week3" / "baseline_vs_enhanced_comparison.md"


def load_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Cannot find file: {path}")

    with path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        rows = list(reader)

    if not rows:
        raise ValueError(f"CSV file is empty: {path}")

    return rows


def get_first(row: Dict[str, Any], names: List[str], default: Any = "") -> Any:
    for name in names:
        if name in row and row[name] not in [None, ""]:
            return row[name]
    return default


def parse_float(value: Any) -> Optional[float]:
    if value is None:
        return None

    text = str(value).strip()
    if text == "":
        return None

    try:
        number = float(text)
    except ValueError:
        return None

    if math.isnan(number):
        return None

    return number


def fmt(value: Optional[float], digits: int = 3) -> str:
    if value is None:
        return ""
    return f"{value:.{digits}f}"


def diff(enhanced: Optional[float], baseline: Optional[float]) -> Optional[float]:
    if enhanced is None or baseline is None:
        return None
    return enhanced - baseline


def reduction_rate(baseline: Optional[float], enhanced: Optional[float]) -> Optional[float]:
    """
    Positive means enhanced reduced the metric.
    Example:
        baseline = 10, enhanced = 7 => 0.3
    """
    if baseline is None or enhanced is None:
        return None
    if baseline == 0:
        return None
    return (baseline - enhanced) / baseline


def get_customer_count(row: Dict[str, Any]) -> str:
    value = get_first(row, ["customer_count", "num_customers", "customers"])
    if value in [None, ""]:
        raise ValueError(f"Missing customer count in row: {row}")
    return str(value).strip()


def index_by_customer_count(rows: List[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    indexed: Dict[str, Dict[str, str]] = {}

    for row in rows:
        customer_count = get_customer_count(row)
        indexed[customer_count] = row

    return indexed


def get_metric(row: Dict[str, Any], names: List[str]) -> Optional[float]:
    return parse_float(get_first(row, names))


def make_comparison_rows(
    baseline_rows: List[Dict[str, str]],
    enhanced_rows: List[Dict[str, str]],
) -> List[Dict[str, Any]]:
    baseline_by_c = index_by_customer_count(baseline_rows)
    enhanced_by_c = index_by_customer_count(enhanced_rows)

    customer_counts = sorted(
        set(baseline_by_c.keys()) & set(enhanced_by_c.keys()),
        key=lambda x: int(float(x)),
    )

    if not customer_counts:
        raise ValueError("No matching customer counts between baseline and enhanced summaries.")

    comparison_rows: List[Dict[str, Any]] = []

    for customer_count in customer_counts:
        b = baseline_by_c[customer_count]
        e = enhanced_by_c[customer_count]

        b_feasible = get_metric(b, ["feasible_rate", "avg_feasible_rate"])
        e_feasible = get_metric(e, ["feasible_rate", "avg_feasible_rate"])

        b_distance = get_metric(
            b,
            [
                "avg_total_distance_all_runs",
                "avg_distance_all",
                "avg_total_distance",
                "avg_distance",
            ],
        )
        e_distance = get_metric(
            e,
            [
                "avg_total_distance_all_runs",
                "avg_distance_all",
                "avg_total_distance",
                "avg_distance",
            ],
        )

        b_runtime = get_metric(b, ["avg_runtime_seconds", "avg_runtime", "runtime_seconds"])
        e_runtime = get_metric(e, ["avg_runtime_seconds", "avg_runtime", "runtime_seconds"])

        b_total_v = get_metric(b, ["avg_total_violations", "total_violations"])
        e_total_v = get_metric(e, ["avg_total_violations", "total_violations"])

        b_capacity_v = get_metric(b, ["avg_capacity_violations", "capacity_violations"])
        e_capacity_v = get_metric(e, ["avg_capacity_violations", "capacity_violations"])

        b_battery_v = get_metric(b, ["avg_battery_violations", "battery_violations"])
        e_battery_v = get_metric(e, ["avg_battery_violations", "battery_violations"])

        b_tw_v = get_metric(
            b,
            [
                "avg_time_window_violations",
                "avg_timewindow_violations",
                "time_window_violations",
            ],
        )
        e_tw_v = get_metric(
            e,
            [
                "avg_time_window_violations",
                "avg_timewindow_violations",
                "time_window_violations",
            ],
        )

        b_customer_v = get_metric(
            b,
            [
                "avg_missing_customer_violations",
                "avg_customer_violations",
                "missing_customer_violations",
                "customer_violations",
            ],
        )
        e_customer_v = get_metric(
            e,
            [
                "avg_missing_customer_violations",
                "avg_customer_violations",
                "missing_customer_violations",
                "customer_violations",
            ],
        )

        comparison_rows.append(
            {
                "customer_count": customer_count,
                "baseline_runs": get_first(b, ["runs"]),
                "enhanced_runs": get_first(e, ["runs"]),

                "baseline_feasible_rate": b_feasible,
                "enhanced_feasible_rate": e_feasible,
                "feasible_rate_change": diff(e_feasible, b_feasible),

                "baseline_avg_distance": b_distance,
                "enhanced_avg_distance": e_distance,
                "distance_change": diff(e_distance, b_distance),
                "distance_reduction_rate": reduction_rate(b_distance, e_distance),

                "baseline_avg_runtime": b_runtime,
                "enhanced_avg_runtime": e_runtime,
                "runtime_change": diff(e_runtime, b_runtime),

                "baseline_avg_total_violations": b_total_v,
                "enhanced_avg_total_violations": e_total_v,
                "total_violation_change": diff(e_total_v, b_total_v),
                "total_violation_reduction_rate": reduction_rate(b_total_v, e_total_v),

                "baseline_avg_capacity_violations": b_capacity_v,
                "enhanced_avg_capacity_violations": e_capacity_v,
                "capacity_violation_change": diff(e_capacity_v, b_capacity_v),

                "baseline_avg_battery_violations": b_battery_v,
                "enhanced_avg_battery_violations": e_battery_v,
                "battery_violation_change": diff(e_battery_v, b_battery_v),
                "battery_violation_reduction_rate": reduction_rate(b_battery_v, e_battery_v),

                "baseline_avg_time_window_violations": b_tw_v,
                "enhanced_avg_time_window_violations": e_tw_v,
                "time_window_violation_change": diff(e_tw_v, b_tw_v),
                "time_window_violation_reduction_rate": reduction_rate(b_tw_v, e_tw_v),

                "baseline_avg_customer_violations": b_customer_v,
                "enhanced_avg_customer_violations": e_customer_v,
                "customer_violation_change": diff(e_customer_v, b_customer_v),
            }
        )

    return comparison_rows


def write_csv(rows: List[Dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "customer_count",
        "baseline_runs",
        "enhanced_runs",
        "baseline_feasible_rate",
        "enhanced_feasible_rate",
        "feasible_rate_change",
        "baseline_avg_distance",
        "enhanced_avg_distance",
        "distance_change",
        "distance_reduction_rate",
        "baseline_avg_runtime",
        "enhanced_avg_runtime",
        "runtime_change",
        "baseline_avg_total_violations",
        "enhanced_avg_total_violations",
        "total_violation_change",
        "total_violation_reduction_rate",
        "baseline_avg_capacity_violations",
        "enhanced_avg_capacity_violations",
        "capacity_violation_change",
        "baseline_avg_battery_violations",
        "enhanced_avg_battery_violations",
        "battery_violation_change",
        "battery_violation_reduction_rate",
        "baseline_avg_time_window_violations",
        "enhanced_avg_time_window_violations",
        "time_window_violation_change",
        "time_window_violation_reduction_rate",
        "baseline_avg_customer_violations",
        "enhanced_avg_customer_violations",
        "customer_violation_change",
    ]

    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(rows: List[Dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    lines: List[str] = []

    lines.append("# Week 3 Baseline vs Enhanced GA Comparison")
    lines.append("")
    lines.append(
        "This table compares the baseline GA and enhanced GA on the same Week 3 benchmark instances."
    )
    lines.append("")

    lines.append("## Main Comparison Table")
    lines.append("")
    lines.append(
        "| Customers | Baseline Feas. | Enhanced Feas. | Baseline Viol. | Enhanced Viol. | "
        "Viol. Change | Viol. Reduction | Baseline Battery | Enhanced Battery | "
        "Battery Reduction | Baseline TW | Enhanced TW | TW Reduction | Baseline Dist. | Enhanced Dist. | Runtime Change |"
    )
    lines.append(
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"
    )

    for row in rows:
        lines.append(
            f"| {row['customer_count']} "
            f"| {fmt(row['baseline_feasible_rate'])} "
            f"| {fmt(row['enhanced_feasible_rate'])} "
            f"| {fmt(row['baseline_avg_total_violations'])} "
            f"| {fmt(row['enhanced_avg_total_violations'])} "
            f"| {fmt(row['total_violation_change'])} "
            f"| {fmt(row['total_violation_reduction_rate'])} "
            f"| {fmt(row['baseline_avg_battery_violations'])} "
            f"| {fmt(row['enhanced_avg_battery_violations'])} "
            f"| {fmt(row['battery_violation_reduction_rate'])} "
            f"| {fmt(row['baseline_avg_time_window_violations'])} "
            f"| {fmt(row['enhanced_avg_time_window_violations'])} "
            f"| {fmt(row['time_window_violation_reduction_rate'])} "
            f"| {fmt(row['baseline_avg_distance'])} "
            f"| {fmt(row['enhanced_avg_distance'])} "
            f"| {fmt(row['runtime_change'])} |"
        )

    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "- Positive violation reduction means the enhanced GA reduced violations compared with the baseline."
    )
    lines.append(
        "- Negative violation reduction means the enhanced GA produced more violations than the baseline."
    )
    lines.append(
        "- Feasible rate is a strict all-or-nothing metric. Even if feasible rate remains zero, violation counts help evaluate whether the algorithm is moving closer to feasibility."
    )
    lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def print_comparison(rows: List[Dict[str, Any]]) -> None:
    print("Week 3 Baseline vs Enhanced GA Comparison")
    print("=" * 100)

    for row in rows:
        print(
            "customers={customers}, baseline_viol={bviol}, enhanced_viol={eviol}, "
            "viol_change={vchange}, viol_reduction={vreduct}, "
            "baseline_battery={bbat}, enhanced_battery={ebat}, "
            "baseline_tw={btw}, enhanced_tw={etw}, "
            "baseline_dist={bdist}, enhanced_dist={edist}".format(
                customers=row["customer_count"],
                bviol=fmt(row["baseline_avg_total_violations"]),
                eviol=fmt(row["enhanced_avg_total_violations"]),
                vchange=fmt(row["total_violation_change"]),
                vreduct=fmt(row["total_violation_reduction_rate"]),
                bbat=fmt(row["baseline_avg_battery_violations"]),
                ebat=fmt(row["enhanced_avg_battery_violations"]),
                btw=fmt(row["baseline_avg_time_window_violations"]),
                etw=fmt(row["enhanced_avg_time_window_violations"]),
                bdist=fmt(row["baseline_avg_distance"]),
                edist=fmt(row["enhanced_avg_distance"]),
            )
        )

    print("=" * 100)


def main() -> None:
    baseline_rows = load_csv(BASELINE_SUMMARY)
    enhanced_rows = load_csv(ENHANCED_SUMMARY)

    comparison_rows = make_comparison_rows(baseline_rows, enhanced_rows)

    write_csv(comparison_rows, OUTPUT_CSV)
    write_markdown(comparison_rows, OUTPUT_MD)
    print_comparison(comparison_rows)

    print(f"Comparison CSV written to: {OUTPUT_CSV}")
    print(f"Comparison Markdown written to: {OUTPUT_MD}")


if __name__ == "__main__":
    main()
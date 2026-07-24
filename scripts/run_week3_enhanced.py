from __future__ import annotations

import argparse
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from src.baselines.ga_enhanced import solve_ga_enhanced
from src.io import load_instance_from_json

from scripts.run_week3_baseline import (
    PROJECT_ROOT,
    parse_int_list,
    find_instance_files,
    extract_instance_seed,
    evaluate_result,
    write_csv,
    write_json,
    print_progress,
)


DEFAULT_INSTANCE_DIR = PROJECT_ROOT / "data" / "week3_benchmarks"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "results" / "week3"
DEFAULT_CSV_PATH = DEFAULT_OUTPUT_DIR / "enhanced_results.csv"
DEFAULT_JSON_PATH = DEFAULT_OUTPUT_DIR / "enhanced_results.json"


def run_single_experiment(
    instance_path: Path,
    algorithm_seed: int,
    population_size: int,
    generations: int,
) -> Dict[str, Any]:
    instance = load_instance_from_json(instance_path)
    instance_seed = extract_instance_seed(instance_path)

    start_time = time.perf_counter()

    result = solve_ga_enhanced(
        instance,
        population_size=population_size,
        generations=generations,
        random_seed=algorithm_seed,
    )

    runtime_seconds = time.perf_counter() - start_time

    row = evaluate_result(
        result=result,
        instance=instance,
        instance_path=instance_path,
        instance_seed=instance_seed,
        algorithm_seed=algorithm_seed,
        runtime_seconds=runtime_seconds,
        population_size=population_size,
        generations=generations,
    )

    # evaluate_result comes from the baseline runner, so it labels rows as
    # ga_baseline by default. For this runner we overwrite the label.
    row["algorithm"] = "ga_enhanced"

    return row


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

    print("Running Week 3 enhanced GA experiments")
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
    print(f"Finished enhanced experiments. Rows written: {len(rows)}")

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
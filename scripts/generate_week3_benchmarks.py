from __future__ import annotations

from src.benchmarks.week3_instances import (
    DEFAULT_WEEK3_OUTPUT_DIR,
    WEEK3_SEEDS,
    WEEK3_SIZES,
    generate_and_save_week3_benchmarks,
    load_instance_json,
    summarize_instance,
)


def main() -> None:
    print("Generating Week 3 fixed benchmark instances...")
    print(f"Output directory: {DEFAULT_WEEK3_OUTPUT_DIR}")
    print(f"Sizes: {WEEK3_SIZES}")
    print(f"Seeds: {WEEK3_SEEDS}")
    print()

    generated_paths = generate_and_save_week3_benchmarks(
        output_dir=DEFAULT_WEEK3_OUTPUT_DIR,
        sizes=WEEK3_SIZES,
        seeds=WEEK3_SEEDS,
    )

    print("Generated instances:")
    for path in generated_paths:
        instance = load_instance_json(path)
        summary = summarize_instance(instance)

        print(
            f"  {path} | "
            f"customers={summary['customers']}, "
            f"stations={summary['stations']}, "
            f"vehicles={summary['vehicles']}, "
            f"capacity={summary['vehicle_capacity']}, "
            f"battery={summary['battery_capacity']}"
        )

    print()
    print(f"Done. Total generated files: {len(generated_paths)}")


if __name__ == "__main__":
    main()
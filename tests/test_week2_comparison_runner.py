from scripts.run_week2_comparison import run_one_instance


def test_week2_comparison_runner_returns_rows_for_all_methods():
    rows = run_one_instance(size=10, seed=123)

    methods = {row["method"] for row in rows}

    assert "random" in methods
    assert "nearest_neighbor" in methods
    assert "pomo_style" in methods
    assert "ga_style" in methods
    assert "or_sweep" in methods

    for row in rows:
        assert row["size"] == 10
        assert row["seed"] == 123
        assert row["assigned_customers"] >= 0
        assert row["unassigned_customers"] >= 0
        assert row["route_count"] >= 0
        assert row["runtime_seconds"] >= 0.0
        assert "method_description" in row
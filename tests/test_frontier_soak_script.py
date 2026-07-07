"""Tests for the activated frontier soak runner."""

from scripts.run_frontier_soak import run_frontier_soak


def test_frontier_soak_runner_reports_real_metrics(tmp_path):
    """A one-year soak should produce measurable historical-loop output."""
    metrics = run_frontier_soak(
        years=1,
        seed=123,
        db_path=tmp_path / "frontier_soak.db",
        workbook_path=tmp_path / "frontier_soak.xlsx",
        export_workbook=True,
    )

    assert metrics.seed == 123
    assert metrics.years_simulated == 1
    assert metrics.months_simulated == 12
    assert 16 <= metrics.factions <= 20
    assert metrics.claims_pressed > 0
    assert metrics.treaty_crises > 0
    assert metrics.historical_actions > 0
    assert metrics.chronicle_entries > 0
    assert metrics.workbook_exported is True
    assert metrics.workbook_path.exists()
    assert metrics.db_path.exists()

    lines = metrics.lines()
    assert "Seed: 123" in lines
    assert "Years simulated: 1" in lines
    assert any(line.startswith("Claims pressed: ") for line in lines)

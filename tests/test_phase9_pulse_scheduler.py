"""Phase 9 pulse-scheduler tests."""

import sqlite3
from pathlib import Path

from warfare_simulation.app import WarfareSimulationApp
from warfare_simulation.orchestration import PulseContext, PulseScheduler, PulseType
from warfare_simulation.orchestration.game_state import GameState

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "src" / "warfare_simulation" / "config" / "data"


def test_pulse_context_detects_daily_weekly_monthly_seasonal_and_yearly_boundaries():
    """Pulse boundaries should be deterministic from the date transition."""
    before = GameState(current_day=31, current_turn=12, current_month=12, current_year=1)
    after = GameState(current_day=1, current_turn=13, current_month=1, current_year=2)

    context = PulseContext.from_transition(before, after, month_rolled=True)

    assert context.pulses == (
        PulseType.DAILY,
        PulseType.MONTHLY,
        PulseType.SEASONAL,
        PulseType.YEARLY,
    )


def test_scheduler_rejects_duplicate_hooks_and_runs_in_pulse_order():
    """Duplicate-run prevention starts with unique hook registration per pulse."""
    scheduler = PulseScheduler()
    executed = []
    scheduler.register(PulseType.DAILY, "clock", lambda _context: executed.append("daily"))
    scheduler.register(PulseType.MONTHLY, "economy", lambda _context: executed.append("monthly"))

    try:
        scheduler.register(PulseType.MONTHLY, "economy", lambda _context: None)
    except ValueError as exc:
        assert "already registered" in str(exc)
    else:  # pragma: no cover - keeps assertion message clear
        raise AssertionError("Expected duplicate pulse hook registration to fail")

    context = PulseContext(
        current_day=1, current_month=2, current_year=1, current_turn=2, month_rolled=True
    )

    assert scheduler.run(context) == ("daily:clock", "monthly:economy")
    assert executed == ["daily", "monthly"]


def test_campaign_registers_domain_pulse_hooks(tmp_path):
    """The orchestrator should expose registered hooks for current domains."""
    app = WarfareSimulationApp(config_path=CONFIG_DIR, db_path=tmp_path / "phase9_hooks.db")

    assert app.campaign.pulse_scheduler.registered_hook_names(PulseType.DAILY) == (
        "kingdom_clock_sync",
    )
    assert app.campaign.pulse_scheduler.registered_hook_names(PulseType.MONTHLY) == (
        "kingdom_economy",
        "logistics_resources",
        "observer_summary",
    )


def test_daily_progression_monthly_pulse_logs_once(tmp_path):
    """Daily advancement should run monthly economy/logistics exactly once at rollover."""
    db_path = tmp_path / "phase9_daily_monthly_pulse.db"
    app = WarfareSimulationApp(config_path=CONFIG_DIR, db_path=db_path)

    for _ in range(31):
        app.campaign.advance_day()

    with sqlite3.connect(db_path) as conn:
        economy_audits = conn.execute("""
            SELECT COUNT(*)
            FROM audit_log
            WHERE turn = 2 AND system = 'Economy'
            """).fetchone()[0]
        logistics_audits = conn.execute("""
            SELECT COUNT(*)
            FROM audit_log
            WHERE turn = 2 AND system = 'Logistics'
            """).fetchone()[0]
        summaries = conn.execute("""
            SELECT COUNT(*)
            FROM turn_summary
            WHERE turn = 2
            """).fetchone()[0]

    assert economy_audits == 1
    assert logistics_audits == 4
    assert summaries == 1

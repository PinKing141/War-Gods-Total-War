"""Phase 7 turn-simulation tests."""

import sqlite3
from pathlib import Path

from warfare_simulation.app import WarfareSimulationApp
from warfare_simulation.orchestration import GameState, SimDate
from warfare_simulation.services.campaign_service import CampaignService


ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "src" / "warfare_simulation" / "config" / "data"


def test_game_state_advances_across_year_boundary():
    """The global clock should roll month 12 into year +1."""
    state = GameState(current_turn=12, current_month=12, current_year=1)

    state.advance_turn()

    assert state.current_turn == 13
    assert state.current_month == 1
    assert state.current_year == 2


def test_sim_date_formats_and_advances_as_canonical_calendar():
    """SimDate should provide the canonical observer-facing calendar behavior."""
    date = SimDate(day=28, month=2, year=4)

    next_date, month_rolled = date.advance_day()

    assert date.format() == "28/02/0004"
    assert next_date == SimDate(day=29, month=2, year=4)
    assert month_rolled is False
    assert next_date.advance_day() == (SimDate(day=1, month=3, year=4), True)


def test_game_state_advances_day_across_month_and_year_boundary():
    """Daily advancement should roll over both month and year correctly."""
    state = GameState(current_day=31, current_turn=12, current_month=12, current_year=1)

    month_rolled = state.advance_day()

    assert month_rolled is True
    assert state.current_day == 1
    assert state.current_turn == 13
    assert state.current_month == 1
    assert state.current_year == 2


def test_game_state_checkpoint_round_trip(tmp_path):
    """GameState checkpoints should save and restore the campaign clock."""
    checkpoint = tmp_path / "checkpoint.json"
    state = GameState(
        current_day=18,
        current_turn=4,
        current_month=4,
        current_year=1,
        simulation_speed="2x",
    )

    saved_path = state.save_checkpoint(checkpoint)
    restored = GameState.load_checkpoint(saved_path)

    assert restored == state


def test_phase8_simulation_speeds_match_observer_controls(tmp_path):
    """The supported speed labels should match the observer-pivot roadmap."""
    db_path = tmp_path / "phase8_speeds.db"
    app = WarfareSimulationApp(config_path=CONFIG_DIR, db_path=db_path)
    service = CampaignService(app)

    for speed, expected_interval in {
        "paused": None,
        "1x": 1000,
        "2x": 500,
        "5x": 200,
        "fast": 50,
    }.items():
        service.set_simulation_speed(speed)
        assert service.get_simulation_status().simulation_speed == speed
        assert service.get_speed_interval_ms() == expected_interval


def test_advance_turn_persists_mutable_state_to_sqlite(tmp_path):
    """Turn advancement should persist kingdom and resource changes back to SQLite."""
    db_path = tmp_path / "phase7_persisted_turn.db"
    app = WarfareSimulationApp(config_path=CONFIG_DIR, db_path=db_path)

    app.campaign.advance_turn()

    with sqlite3.connect(db_path) as conn:
        kingdom = conn.execute(
            """
            SELECT treasury_silver, current_day, current_turn, current_month, current_year
            FROM kingdom
            WHERE id = 1
            """
        ).fetchone()
        food = conn.execute(
            """
            SELECT stored
            FROM resource
            WHERE id = 1
            """
        ).fetchone()

    assert kingdom == (525700, 1, 2, 2, 1)
    assert food == (5100,)


def test_advance_day_only_triggers_monthly_economy_on_month_rollover(tmp_path):
    """Daily advancement should only apply the monthly slice when the month changes."""
    db_path = tmp_path / "phase8_daily_clock.db"
    app = WarfareSimulationApp(config_path=CONFIG_DIR, db_path=db_path)

    kingdom = app.repos.kingdom.get_current_kingdom()
    assert kingdom is not None

    for _ in range(30):
        state = app.campaign.advance_day()

    assert state.current_day == 31
    assert state.current_month == 1
    assert state.current_year == 1
    assert kingdom.treasury_silver == 520000

    state = app.campaign.advance_day()

    assert state.current_day == 1
    assert state.current_month == 2
    assert state.current_year == 1
    assert state.current_turn == 2
    assert kingdom.treasury_silver == 525700


def test_rehydrated_repositories_include_persisted_turn_state(tmp_path):
    """A restarted app should hydrate from the SQLite turn state, not the seed JSON."""
    db_path = tmp_path / "phase7_restart.db"
    app = WarfareSimulationApp(config_path=CONFIG_DIR, db_path=db_path)

    for _ in range(31):
        app.campaign.advance_day()
    restarted = WarfareSimulationApp(config_path=CONFIG_DIR, db_path=db_path)

    kingdom = restarted.repos.kingdom.get_current_kingdom()
    food = restarted.repos.resource.get(1)

    assert restarted.game_state.current_day == 1
    assert restarted.game_state.current_turn == 2
    assert restarted.game_state.current_month == 2
    assert restarted.game_state.current_year == 1
    assert kingdom.current_day == 1
    assert kingdom.current_turn == 2
    assert kingdom.current_month == 2
    assert kingdom.current_year == 1
    assert kingdom.treasury_silver == 525700
    assert food.stored == 5100


def test_advance_turn_writes_event_and_audit_logs(tmp_path):
    """Turn advancement should leave traceable event and audit records."""
    db_path = tmp_path / "phase7_audit_log.db"
    app = WarfareSimulationApp(config_path=CONFIG_DIR, db_path=db_path)

    app.campaign.advance_turn()

    with sqlite3.connect(db_path) as conn:
        events = conn.execute(
            """
            SELECT turn, category, description, impact, affected_entities
            FROM event
            ORDER BY id
            """
        ).fetchall()
        audits = conn.execute(
            """
            SELECT turn, month, year, actor, target, system, action,
                   previous_value, new_value, reason
            FROM audit_log
            ORDER BY id
            """
        ).fetchall()

    assert events[0] == (
        2,
        "Economy",
        "The Dominion of Auster collected monthly net income.",
        "Treasury changed from 520000 to 525700 silver.",
        "[1]",
    )
    assert audits[0] == (
        2,
        2,
        1,
        "kingdom:1",
        "kingdom:1.treasury_silver",
        "Economy",
        "collect_monthly_net_income",
        "520000",
        "525700",
        "Monthly income minus expenses during turn advancement.",
    )
    assert any(log[5] == "Logistics" for log in audits)


def test_advance_turn_persists_turn_summary(tmp_path):
    """Turn advancement should persist a compact summary of resolved systems."""
    db_path = tmp_path / "phase7_turn_summary.db"
    app = WarfareSimulationApp(config_path=CONFIG_DIR, db_path=db_path)

    app.campaign.advance_turn()

    with sqlite3.connect(db_path) as conn:
        summary = conn.execute(
            """
            SELECT turn, month, year, title, event_count, audit_count, highlights
            FROM turn_summary
            ORDER BY id
            """
        ).fetchone()

    assert summary[:6] == (2, 2, 1, "Turn 2 Summary", 1, 5)
    assert "The Dominion of Auster collected monthly net income." in summary[6]


def test_rehydrated_repositories_include_turn_summaries(tmp_path):
    """A restarted app should hydrate persisted turn summaries from SQLite."""
    db_path = tmp_path / "phase7_summary_restart.db"
    app = WarfareSimulationApp(config_path=CONFIG_DIR, db_path=db_path)

    app.campaign.advance_turn()
    restarted = WarfareSimulationApp(config_path=CONFIG_DIR, db_path=db_path)

    summary = restarted.repos.turn_summary.get_latest()

    assert summary.turn == 2
    assert summary.event_count == 1
    assert summary.audit_count == 5
    assert "Logistics resolved 4 resource update(s)." in summary.narrative

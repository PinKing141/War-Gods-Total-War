"""Phase 7 turn-simulation tests."""

import sqlite3
from pathlib import Path

from warfare_simulation.app import WarfareSimulationApp
from warfare_simulation.orchestration import GameState


ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "src" / "warfare_simulation" / "config" / "data"


def test_game_state_advances_across_year_boundary():
    """The global clock should roll month 12 into year +1."""
    state = GameState(current_turn=12, current_month=12, current_year=1)

    state.advance_turn()

    assert state.current_turn == 13
    assert state.current_month == 1
    assert state.current_year == 2


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

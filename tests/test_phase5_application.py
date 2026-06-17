"""Phase 5 thin application slice tests."""

from pathlib import Path

import openpyxl
import sqlite3
import pytest

from warfare_simulation.app import WarfareSimulationApp

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "src" / "warfare_simulation" / "config" / "data"
EXPECTED_TABLES = {
    "kingdom",
    "province",
    "unit",
    "commander",
    "faction",
    "relation",
    "resource",
    "event",
    "migration",
}

EXPECTED_SHEETS = [
    "Kingdom Dashboard",
    "Provinces",
    "Resources",
    "Army Register",
    "Commanders",
    "Diplomacy & Intel",
    "Logistics & Projects",
    "Event Log",
]


def test_app_run_loads_config_seeds_sqlite_and_exports_workbook(tmp_path):
    """The Phase 5 app entry point should execute JSON -> SQLite -> workbook export."""
    db_path = tmp_path / "phase5_campaign.db"
    output_path = tmp_path / "Auster_Campaign_Engine.xlsx"

    app = WarfareSimulationApp(config_path=CONFIG_DIR, db_path=db_path)
    exported_path = app.run(output_path)

    assert exported_path == output_path
    assert output_path.exists()
    assert db_path.exists()

    workbook = openpyxl.load_workbook(output_path, data_only=False)
    assert workbook.sheetnames == EXPECTED_SHEETS

    assert app.game_state.current_turn == 1
    assert len(app.repos.kingdom.list_all()) == 1
    assert len(app.repos.province.list_all()) == 4
    assert len(app.repos.unit.list_all()) == 3
    assert len(app.repos.commander.list_all()) == 3
    assert len(app.repos.faction.list_all()) == 3
    assert len(app.repos.relation.list_all()) == 3
    assert len(app.repos.resource.list_all()) == 4


def test_advance_turn_is_explicitly_deferred(tmp_path):
    """Phase 5 intentionally exposes export only; turn simulation is post-Phase 6."""
    app = WarfareSimulationApp(config_path=CONFIG_DIR, db_path=tmp_path / "phase5_campaign.db")

    with pytest.raises(NotImplementedError, match="Turn simulation comes after export parity"):
        app.campaign.advance_turn()


def test_app_run_creates_expected_sqlite_schema(tmp_path):
    """The app should create the complete Phase 6 runtime schema before export."""
    db_path = tmp_path / "phase6_schema.db"
    output_path = tmp_path / "phase6_schema.xlsx"

    app = WarfareSimulationApp(config_path=CONFIG_DIR, db_path=db_path)
    app.run(output_path)

    with sqlite3.connect(db_path) as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }

        assert EXPECTED_TABLES.issubset(tables)
        assert conn.execute("PRAGMA foreign_key_list(province)").fetchall()
        assert conn.execute("PRAGMA foreign_key_list(relation)").fetchall()
        assert conn.execute("SELECT COUNT(*) FROM kingdom").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM province").fetchone()[0] == 4
        assert conn.execute("SELECT COUNT(*) FROM unit").fetchone()[0] == 3
        assert conn.execute("SELECT COUNT(*) FROM commander").fetchone()[0] == 3
        assert conn.execute("SELECT COUNT(*) FROM faction").fetchone()[0] == 3
        assert conn.execute("SELECT COUNT(*) FROM relation").fetchone()[0] == 3
        assert conn.execute("SELECT COUNT(*) FROM resource").fetchone()[0] == 4

"""Phase 5 thin application slice tests."""

from pathlib import Path

import openpyxl
import pytest

from warfare_simulation.app import WarfareSimulationApp

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "src" / "warfare_simulation" / "config" / "data"
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

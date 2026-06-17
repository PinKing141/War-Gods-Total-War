"""Integration tests comparing modular export to the legacy monolith."""

from pathlib import Path

import openpyxl
import pytest

from campaign_engine_initialiser import create_campaign_workbook
from warfare_simulation.config.config import ConfigManager
from warfare_simulation.export.workbook_factory import WorkbookFactory
from warfare_simulation.persistence.campaign_bootstrap import CampaignBootstrap
from warfare_simulation.persistence.database import DatabaseManager

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "src" / "warfare_simulation" / "config" / "data"


@pytest.fixture
def legacy_workbook(tmp_path, monkeypatch):
    """Create the legacy workbook in an isolated directory and return it."""
    monkeypatch.chdir(tmp_path)
    workbook = create_campaign_workbook()
    if workbook is not None:
        return workbook
    return openpyxl.load_workbook(tmp_path / "Auster_Campaign_Engine.xlsx", data_only=False)


@pytest.fixture
def modular_workbook(tmp_path):
    """Create a modular workbook from JSON -> SQLite -> hydrated repositories."""
    db = DatabaseManager(str(tmp_path / "campaign.db"))
    config_mgr = ConfigManager(str(CONFIG_DIR))
    repos = CampaignBootstrap.initialize(config_mgr, db, force=True)
    factory = WorkbookFactory.from_campaign_repositories(repos)
    return factory.create_workbook()


def _non_empty_row_count(ws):
    return sum(1 for row in ws.iter_rows(values_only=True) if any(cell is not None for cell in row))


def test_sheet_names_and_row_counts_parity(legacy_workbook, modular_workbook):
    """The modular export must preserve legacy sheet order and row counts."""
    assert modular_workbook.sheetnames == legacy_workbook.sheetnames

    for sheet_name in legacy_workbook.sheetnames:
        assert _non_empty_row_count(modular_workbook[sheet_name]) == _non_empty_row_count(
            legacy_workbook[sheet_name]
        )


def test_key_cell_values_match_monolith(legacy_workbook, modular_workbook):
    """Guard key formulas and values while full cell-level parity evolves."""
    key_cells = {
        "Kingdom Dashboard": ["A2", "B2", "B4", "B5", "B8", "B10"],
        "Provinces": ["A2", "B2", "H5"],
        "Resources": ["A2", "E2", "F3"],
        "Army Register": ["A2", "D2", "I10"],
        "Commanders": ["A2", "H5"],
        "Diplomacy & Intel": ["A2", "C3"],
        "Logistics & Projects": ["A2", "E4"],
        "Event Log": ["A2", "D3"],
    }

    for sheet_name, cells in key_cells.items():
        legacy_ws = legacy_workbook[sheet_name]
        modular_ws = modular_workbook[sheet_name]
        for cell in cells:
            assert modular_ws[cell].value == legacy_ws[cell].value, f"Mismatch at {sheet_name}!{cell}"

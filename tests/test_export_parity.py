"""Integration tests comparing modular export to the legacy monolith."""

from pathlib import Path

import openpyxl
import pytest

from campaign_engine_initialiser import create_campaign_workbook
from warfare_simulation.app import WarfareSimulationApp
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


def _style_snapshot(cell):
    return {
        "font_bold": cell.font.bold,
        "font_color": cell.font.color.rgb if cell.font.color else None,
        "fill_start": cell.fill.start_color.rgb,
        "fill_end": cell.fill.end_color.rgb,
        "fill_type": cell.fill.fill_type,
        "horizontal": cell.alignment.horizontal,
        "vertical": cell.alignment.vertical,
    }


def test_sheet_names_and_row_counts_parity(legacy_workbook, modular_workbook):
    """The modular export must preserve legacy sheet order and row counts."""
    assert modular_workbook.sheetnames == legacy_workbook.sheetnames

    for sheet_name in legacy_workbook.sheetnames:
        assert _non_empty_row_count(modular_workbook[sheet_name]) == _non_empty_row_count(
            legacy_workbook[sheet_name]
        )


def test_cell_level_export_parity(legacy_workbook, modular_workbook):
    """The modular export must preserve every populated legacy cell value."""
    for sheet_name in legacy_workbook.sheetnames:
        legacy_ws = legacy_workbook[sheet_name]
        modular_ws = modular_workbook[sheet_name]
        assert modular_ws.max_row == legacy_ws.max_row
        assert modular_ws.max_column == legacy_ws.max_column

        for row in range(1, legacy_ws.max_row + 1):
            for column in range(1, legacy_ws.max_column + 1):
                coordinate = legacy_ws.cell(row=row, column=column).coordinate
                assert (
                    modular_ws[coordinate].value == legacy_ws[coordinate].value
                ), f"Mismatch at {sheet_name}!{coordinate}"


def test_header_style_and_width_parity(legacy_workbook, modular_workbook):
    """The modular export must preserve monolith header styling and column widths."""
    for sheet_name in legacy_workbook.sheetnames:
        legacy_ws = legacy_workbook[sheet_name]
        modular_ws = modular_workbook[sheet_name]

        for column in range(1, legacy_ws.max_column + 1):
            coordinate = legacy_ws.cell(row=1, column=column).coordinate
            legacy_cell = legacy_ws[coordinate]
            modular_cell = modular_ws[coordinate]

            assert _style_snapshot(modular_cell) == _style_snapshot(
                legacy_cell
            ), f"Style mismatch at {sheet_name}!{coordinate}"

            column_letter = legacy_cell.column_letter
            assert (
                modular_ws.column_dimensions[column_letter].width
                == legacy_ws.column_dimensions[column_letter].width
            ), f"Width mismatch at {sheet_name}!{column_letter}"


def test_app_run_export_matches_legacy_workbook(legacy_workbook, tmp_path):
    """The runnable app must preserve legacy workbook output through the public entry point."""
    output_path = tmp_path / "app_export.xlsx"
    db_path = tmp_path / "app_campaign.db"

    app = WarfareSimulationApp(config_path=CONFIG_DIR, db_path=db_path)
    exported_path = app.run(output_path)

    assert exported_path == output_path
    app_workbook = openpyxl.load_workbook(output_path, data_only=False)

    assert app_workbook.sheetnames == legacy_workbook.sheetnames
    for sheet_name in legacy_workbook.sheetnames:
        legacy_ws = legacy_workbook[sheet_name]
        app_ws = app_workbook[sheet_name]
        assert app_ws.max_row == legacy_ws.max_row
        assert app_ws.max_column == legacy_ws.max_column

        for row in range(1, legacy_ws.max_row + 1):
            for column in range(1, legacy_ws.max_column + 1):
                coordinate = legacy_ws.cell(row=row, column=column).coordinate
                assert (
                    app_ws[coordinate].value == legacy_ws[coordinate].value
                ), f"Mismatch at {sheet_name}!{coordinate}"

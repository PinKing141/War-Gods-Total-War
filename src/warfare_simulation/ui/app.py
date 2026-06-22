"""PySide6 application bootstrap.

Constructs the simulation engine, wraps it in the service facade,
and hands it to the Qt window.  Zero simulation logic lives here.
"""
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from warfare_simulation.app import WarfareSimulationApp
from warfare_simulation.services.campaign_service import CampaignService
from warfare_simulation.ui.main_window import MainWindow

# Resolved at import time — works from any working directory
_DEFAULT_CONFIG = Path(__file__).parents[1] / "config" / "data"
_DEFAULT_DB     = Path("war_sim.db")


def run(
    config_path: Path = _DEFAULT_CONFIG,
    db_path: Path = _DEFAULT_DB,
) -> None:
    """Bootstrap the campaign engine and open the desktop dashboard."""
    qt_app = QApplication.instance() or QApplication(sys.argv)
    qt_app.setApplicationName("War Gods — Campaign Command")
    qt_app.setOrganizationName("War Gods")

    engine  = WarfareSimulationApp(config_path=config_path, db_path=db_path)
    service = CampaignService(engine)

    window = MainWindow(service)
    window.show()

    sys.exit(qt_app.exec())


if __name__ == "__main__":
    run()

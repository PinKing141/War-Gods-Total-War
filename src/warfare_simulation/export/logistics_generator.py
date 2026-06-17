"""
Generates the 'Logistics & Projects' sheet.
"""

from openpyxl.workbook import Workbook
from typing import Any, Optional

LogisticsRepository = Any

from .base_generator import SheetGenerator
from .styles import StyleManager


class LogisticsGenerator(SheetGenerator):
    """Generates the 'Logistics & Projects' sheet."""

    def __init__(self, workbook: Workbook, style_manager: StyleManager, logistics_repo: Optional[LogisticsRepository] = None):
        super().__init__("Logistics & Projects", workbook, style_manager)
        self.logistics_repo = logistics_repo

    def generate(self) -> None:
        """Generates the full logistics and projects sheet."""
        super().generate()

        headers = ["Project/Route", "Type", "Cost", "Progress", "Turns Left", "Notes"]
        self._format_header(headers)

        log_data = [
            ["Southern Watchtowers", "Fortification", "12,000 Silver", "20%", 4, "Extending sightlines towards Volantis"],
            ["Veyl Supply Road", "Infrastructure", "8,000 Silver", "85%", 1, "Paving road to improve supply cart speed"],
            ["Supply Train Alpha", "Convoy", "500 Silver/mo", "Active", "N/A", "Route: Highreach -> Veyl (Food & Arrows)"],
        ]
        self._append_data(log_data)
"""
Generates the 'Resources' sheet.
"""

from openpyxl.workbook import Workbook
from typing import Optional

from warfare_simulation.domain.logistics.repository import LogisticsRepository

from .base_generator import SheetGenerator
from .styles import StyleManager


class ResourcesGenerator(SheetGenerator):
    """Generates the 'Resources' sheet."""

    def __init__(self, workbook: Workbook, style_manager: StyleManager, logistics_repo: Optional[LogisticsRepository] = None):
        super().__init__("Resources", workbook, style_manager)
        self.logistics_repo = logistics_repo

    def generate(self) -> None:
        """Generates the full resources sheet."""
        super().generate()

        headers = ["Resource", "Stored", "Monthly Production", "Monthly Consumption", "Net Change", "Reserve Status"]
        self._format_header(headers)

        res_data = [
            ["Food (Bushels)", 90000, 15000, 12500, "=C2-D2", "Stable"],
            ["Iron (Tons)", 12000, 250, 100, "=C3-D3", "Surplus"],
            ["Timber (Cords)", 8400, 140, 90, "=C4-D4", "Stable"],
            ["Stone (Tons)", 6300, 120, 40, "=C5-D5", "Surplus"],
            ["Wool/Cloth (Bolts)", 4800, 80, 50, "=C6-D6", "Stable"],
            ["Horses (Mounts)", 1150, 15, 5, "=C7-D7", "Stable"],
        ]
        self._append_data(res_data)
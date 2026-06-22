"""
Generates the 'Resources' sheet.
"""

from openpyxl.workbook import Workbook
from typing import Any, Optional

LogisticsRepository = Any

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

        if self.logistics_repo is not None and hasattr(self.logistics_repo, "list_all"):
            resources = self.logistics_repo.list_all()
            if resources:
                rows = []
                for row_number, resource in enumerate(resources, start=2):
                    rows.append([
                        getattr(resource.resource_type, "value", str(resource.resource_type)),
                        resource.stored,
                        resource.monthly_production,
                        resource.monthly_consumption,
                        f"=C{row_number}-D{row_number}",
                        self._reserve_status(resource.stored, resource.max_storage),
                    ])
                self._append_data(rows)
                return

        res_data = [
            ["Food (Bushels)", 90000, 15000, 12500, "=C2-D2", "Stable"],
            ["Iron (Tons)", 12000, 250, 100, "=C3-D3", "Surplus"],
            ["Timber (Cords)", 8400, 140, 90, "=C4-D4", "Stable"],
            ["Stone (Tons)", 6300, 120, 40, "=C5-D5", "Surplus"],
            ["Wool/Cloth (Bolts)", 4800, 80, 50, "=C6-D6", "Stable"],
            ["Horses (Mounts)", 1150, 15, 5, "=C7-D7", "Stable"],
        ]
        self._append_data(res_data)

    @staticmethod
    def _reserve_status(stored: int, max_storage: int) -> str:
        if max_storage <= 0:
            return "Unknown"

        fill_ratio = stored / max_storage
        if fill_ratio < 0.25:
            return "Low"
        if fill_ratio < 0.75:
            return "Stable"
        if fill_ratio < 0.95:
            return "High"
        return "Near Capacity"
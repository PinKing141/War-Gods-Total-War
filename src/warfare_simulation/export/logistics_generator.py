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

        resource_repo = getattr(self.logistics_repo, "resource", self.logistics_repo)
        if resource_repo is not None and hasattr(resource_repo, "list_all"):
            resources = resource_repo.list_all()
            if resources:
                headers = ["Resource", "Supply Status", "Stored", "Net Change", "Capacity", "Notes"]
                self._format_header(headers)
                self._append_data([
                    [
                        getattr(resource.resource_type, "value", str(resource.resource_type)),
                        self._supply_status(resource.stored, resource.max_storage),
                        resource.stored,
                        resource.monthly_production - resource.monthly_consumption,
                        resource.max_storage,
                        f"Production {resource.monthly_production} / Consumption {resource.monthly_consumption}",
                    ]
                    for resource in resources
                ])
                return

        headers = ["Project/Route", "Type", "Cost", "Progress", "Turns Left", "Notes"]
        self._format_header(headers)

        log_data = [
            ["Southern Watchtowers", "Fortification", "12,000 Silver", "20%", 4, "Extending sightlines towards Volantis"],
            ["Veyl Supply Road", "Infrastructure", "8,000 Silver", "85%", 1, "Paving road to improve supply cart speed"],
            ["Supply Train Alpha", "Convoy", "500 Silver/mo", "Active", "N/A", "Route: Highreach -> Veyl (Food & Arrows)"],
        ]
        self._append_data(log_data)

    @staticmethod
    def _supply_status(stored: int, max_storage: int) -> str:
        if max_storage <= 0:
            return "Unknown"

        fill_ratio = stored / max_storage
        if fill_ratio < 0.25:
            return "Fragile"
        if fill_ratio < 0.75:
            return "Stable"
        return "Stockpiled"
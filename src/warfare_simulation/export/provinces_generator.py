"""
Generates the 'Provinces' sheet.
"""

from openpyxl.workbook import Workbook
from typing import Optional

from warfare_simulation.domain.geography.repository import ProvinceRepository

from .base_generator import SheetGenerator
from .styles import StyleManager


class ProvincesGenerator(SheetGenerator):
    """Generates the 'Provinces' sheet."""

    def __init__(self, workbook: Workbook, style_manager: StyleManager, province_repo: Optional[ProvinceRepository] = None):
        super().__init__("Provinces", workbook, style_manager)
        self.province_repo = province_repo

    def generate(self) -> None:
        """Generates the full provinces sheet."""
        super().generate()

        headers = ["Province", "Population", "Fort Level", "Food Stored", "Monthly Tax", "Loyalty", "Garrison", "Governor"]
        self._format_header(headers)

        if self.province_repo is not None:
            provinces = self.province_repo.list_all()
            if provinces:
                self._append_data([
                    [
                        province.name,
                        province.population,
                        province.fort_level,
                        province.food_stored,
                        province.monthly_tax,
                        province.loyalty,
                        province.garrison_size,
                        province.governor_name,
                    ]
                    for province in provinces
                ])
                return

        prov_data = [
            ["Highreach (Capital)", 150000, 5, 25000, 8000, 95, 1000, "Lord Protector Favour"],
            ["Oakhaven (Agri)", 180000, 2, 45000, 4500, 90, 300, "Lord Vance"],
            ["Ironford (Mining)", 80000, 3, 12000, 4000, 85, 400, "Overseer Thorne"],
            ["Veyl (Border/Intel)", 40000, 4, 8000, 2000, 92, 800, "Spymaster Kael"],
        ]
        self._append_data(prov_data)
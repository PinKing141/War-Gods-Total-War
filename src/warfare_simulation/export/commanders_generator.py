"""
Generates the 'Commanders' sheet.
"""

from openpyxl.workbook import Workbook
from typing import Optional

from warfare_simulation.domain.military.repository import MilitaryRepository

from .base_generator import SheetGenerator
from .styles import StyleManager


class CommandersGenerator(SheetGenerator):
    """Generates the 'Commanders' sheet."""

    def __init__(self, workbook: Workbook, style_manager: StyleManager, military_repo: Optional[MilitaryRepository] = None):
        super().__init__("Commanders", workbook, style_manager)
        self.military_repo = military_repo

    def generate(self) -> None:
        """Generates the full commanders sheet."""
        super().generate()

        headers = ["Name", "Role", "Leadership", "Tactics", "Logistics", "Loyalty", "Status", "Traits"]
        self._format_header(headers)

        com_data = [
            ["Lord Protector Favour", "Sovereign", 95, 97, 96, 100, "Active", "Defensive Strategist, Patient, Over-analytical"],
            ["Marcus Thorne", "General (Cavalry)", 84, 79, 72, 88, "Active", "Bold, Inspiring, Prideful"],
            ["Elias Kael", "Spymaster", 75, 82, 88, 92, "Active", "Deceptive, Cautious, Calculating"],
            ["Julian Vance", "Steward", 60, 50, 94, 95, "Active", "Brilliant Logistician, Physically Frail"],
        ]
        self._append_data(com_data)
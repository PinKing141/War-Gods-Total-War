"""
Generates the 'Army Register' sheet.
"""

from openpyxl.workbook import Workbook
from typing import Any, Optional

MilitaryRepository = Any

from .base_generator import SheetGenerator
from .styles import StyleManager


class ArmyGenerator(SheetGenerator):
    """Generates the 'Army Register' sheet."""

    def __init__(self, workbook: Workbook, style_manager: StyleManager, military_repo: Optional[MilitaryRepository] = None):
        super().__init__("Army Register", workbook, style_manager)
        self.military_repo = military_repo

    def generate(self) -> None:
        """Generates the full army register sheet."""
        super().generate()

        headers = ["Unit Name", "Soldiers", "Veterans", "Type", "Morale", "Fatigue", "Armour", "Location", "Commander"]
        self._format_header(headers)

        army_data = [
            ["Vanguard I", 500, 420, "Heavy Spearmen", 92, 0, "Brigandine", "Highreach", "Lord Protector Favour"],
            ["Vanguard II", 500, 380, "Heavy Spearmen", 88, 0, "Brigandine", "Highreach", "Captain Aris"],
            ["Vanguard III", 500, 350, "Heavy Spearmen", 85, 0, "Brigandine", "Ironford", "General Thorne"],
            ["Vanguard IV", 500, 310, "Heavy Spearmen", 85, 0, "Brigandine", "Veyl", "Captain Dael"],
            ["Vanguard V", 500, 290, "Heavy Spearmen", 82, 0, "Brigandine", "Oakhaven", "Lieutenant Vane"],
            ["Crossbows I", 500, 250, "Ranged", 89, 0, "Gambeson", "Veyl", "Captain Sylas"],
            ["Crossbows II", 500, 220, "Ranged", 86, 0, "Gambeson", "Highreach", "Lieutenant Corren"],
            ["Iron Guard", 500, 450, "Heavy Infantry", 95, 0, "Plate/Mail", "Highreach", "Lord Protector Favour"],
            ["Thorne's Riders", 500, 300, "Medium Cavalry", 84, 0, "Mail", "Ironford", "General Thorne"],
        ]
        self._append_data(army_data)
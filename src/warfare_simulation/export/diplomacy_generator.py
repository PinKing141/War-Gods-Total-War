"""
Generates the 'Diplomacy & Intel' sheet.
"""

from openpyxl.workbook import Workbook
from typing import Optional

from warfare_simulation.domain.diplomacy.repository import DiplomacyRepository

from .base_generator import SheetGenerator
from .styles import StyleManager


class DiplomacyGenerator(SheetGenerator):
    """Generates the 'Diplomacy & Intel' sheet."""

    def __init__(self, workbook: Workbook, style_manager: StyleManager, diplomacy_repo: Optional[DiplomacyRepository] = None):
        super().__init__("Diplomacy & Intel", workbook, style_manager)
        self.diplomacy_repo = diplomacy_repo

    def generate(self) -> None:
        """Generates the full diplomacy and intel sheet."""
        super().generate()

        headers = ["Faction/Agent", "Type", "Opinion/Risk", "Status", "Notes/Mission"]
        self._format_header(headers)

        intel_data = [
            ["Republic of Tyra", "Nation (Ally)", "+89", "Trade Pact Active", "Supplies gold and exotic goods for iron."],
            ["Empire of Volantis", "Nation (Rival)", "-85", "Cold War", "Expansionist empire to the south. Tensions high."],
            ["Raven 1 (Kael's Network)", "Spy", "12% Risk", "Active", "Scouting Volantis border troop movements."],
            ["Raven 2 (Kael's Network)", "Spy", "40% Risk", "Active", "Infiltrating Volantis military command."],
        ]
        self._append_data(intel_data)
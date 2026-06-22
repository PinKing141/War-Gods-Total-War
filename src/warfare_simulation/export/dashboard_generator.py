"""
Generates the 'Kingdom Dashboard' sheet.
"""

from openpyxl.workbook import Workbook
from typing import Optional

from warfare_simulation.domain.kingdom.repository import KingdomRepository

from .base_generator import SheetGenerator
from .styles import StyleManager


class DashboardGenerator(SheetGenerator):
    """Generates the 'Kingdom Dashboard' sheet."""

    def __init__(self, workbook: Workbook, style_manager: StyleManager, kingdom_repo: Optional[KingdomRepository] = None):
        super().__init__("Kingdom Dashboard", workbook, style_manager)
        self.kingdom_repo = kingdom_repo

    def generate(self) -> None:
        """Generates the full dashboard sheet."""
        # The monolith creates the dashboard on the default active sheet.
        # To match this, we get the active sheet, title it, and then proceed.
        self.ws = self.wb.active
        assert self.ws is not None, "Active worksheet not found in a new workbook."
        self.ws.title = self.sheet_name

        headers = ["Category", "Value", "Notes"]
        column_widths = [25, 20, 40]
        self._format_header(headers, column_widths)

        kingdom = self.kingdom_repo.get_current_kingdom() if self.kingdom_repo else None
        if kingdom is not None:
            dash_data = [
                ["Kingdom", kingdom.name, "Current ruling state"],
                ["Ruler", kingdom.ruler_name, "Active sovereign"],
                ["Population", "=SUM(Provinces!B:B)", "Total citizens across provinces"],
                ["Treasury (Silver)", kingdom.treasury_silver, "Available silver reserves"],
                ["Monthly Income", kingdom.monthly_income, "Kingdom recurring income"],
                ["Monthly Expenses", kingdom.monthly_expenses, "Kingdom recurring expenses"],
                ["Net Income", "=B6-B7", "Monthly surplus or deficit"],
                ["Grain Stores (Months)", kingdom.grain_stores, "Strategic food reserves"],
                ["Army Size", "=SUM('Army Register'!B:B)", "Total active soldiers"],
                ["National Morale", f"{kingdom.morale}%", "Realm-wide confidence"],
                ["Noble Loyalty", f"{kingdom.loyalty}%", "Support from the nobility"],
                [
                    "Current Turn",
                    kingdom.current_turn,
                    f"Year {kingdom.current_year}, Month {kingdom.current_month}",
                ],
            ]
            self._append_data(dash_data)
            return

        # Data from campaign_engine_initialiser.py for parity
        dash_data = [
            ["Kingdom", "The Dominion of Auster", "Motto: Order Before Ambition"],
            ["Ruler", "Lord Protector Favour", "Age: 21, Stoic, Calculating"],
            ["Population", "=SUM(Provinces!B2:B5)", "Total citizens"],
            ["Treasury (Silver)", 520000, "Vast reserves of silver and iron"],
            ["Monthly Income", 18500, "Taxes & Tyra Trade"],
            ["Monthly Expenses", 12800, "Army Upkeep & Logistics"],
            ["Net Income", "=B5-B6", "Monthly surplus/deficit"],
            ["Grain Stores (Months)", 14, "Highly resilient to sieges"],
            ["Army Size", "=SUM('Army Register'!B2:B10)", "Professional Standing Army"],
            ["National Morale", "87%", "Disciplined and steady"],
            ["Noble Loyalty", "83%", "House Kael & Thorne hold sway"],
            ["Current Turn", 1, "Year 1, Month 1, Early Spring"],
        ]
        self._append_data(dash_data)
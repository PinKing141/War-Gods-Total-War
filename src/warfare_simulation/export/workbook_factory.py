"""
Orchestrates all sheet generators to create the campaign workbook.
"""

import openpyxl
from openpyxl.workbook import Workbook

from .army_generator import ArmyGenerator
from .commanders_generator import CommandersGenerator
from .dashboard_generator import DashboardGenerator
from .diplomacy_generator import DiplomacyGenerator
from .events_generator import EventsGenerator
from .logistics_generator import LogisticsGenerator
from .provinces_generator import ProvincesGenerator
from .resources_generator import ResourcesGenerator
from .styles import StyleManager


class WorkbookFactory:
    """Orchestrates all sheet generators to create the campaign workbook."""

    def __init__(self, repos: dict):
        """
        Initializes the factory with all necessary domain repositories.

        Args:
            repos: A dictionary mapping repository names (e.g., 'kingdom')
                   to repository instances.
        """
        self.repos = repos

    def create_workbook(self) -> Workbook:
        """
        Creates and returns a complete campaign workbook.

        Returns:
            An openpyxl Workbook object populated with all campaign sheets.
        """
        wb = openpyxl.Workbook()
        # The default sheet will be used for the dashboard and renamed.

        styles = StyleManager()

        # For now, repos are passed but not used by generators,
        # as they use hardcoded data from the monolith for parity testing.
        kingdom_repo = self.repos.get("kingdom")
        province_repo = self.repos.get("geography")
        military_repo = self.repos.get("military")
        diplomacy_repo = self.repos.get("diplomacy")
        logistics_repo = self.repos.get("logistics")
        event_repo = self.repos.get("events")

        # The order of generation determines the order of sheets in the workbook.
        # DashboardGenerator is special as it uses the default active sheet.
        DashboardGenerator(wb, styles, kingdom_repo).generate()
        ProvincesGenerator(wb, styles, province_repo).generate()
        ResourcesGenerator(wb, styles, logistics_repo).generate()
        ArmyGenerator(wb, styles, military_repo).generate()
        CommandersGenerator(wb, styles, military_repo).generate()
        DiplomacyGenerator(wb, styles, diplomacy_repo).generate()
        LogisticsGenerator(wb, styles, logistics_repo).generate()
        EventsGenerator(wb, styles, event_repo).generate()

        return wb
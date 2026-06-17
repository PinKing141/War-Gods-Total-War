"""
Generates the 'Event Log' sheet.
"""

from openpyxl.workbook import Workbook
from typing import Optional

from warfare_simulation.domain.events.repository import EventRepository

from .base_generator import SheetGenerator
from .styles import StyleManager


class EventsGenerator(SheetGenerator):
    """Generates the 'Event Log' sheet."""

    def __init__(self, workbook: Workbook, style_manager: StyleManager, event_repo: Optional[EventRepository] = None):
        super().__init__("Event Log", workbook, style_manager)
        self.event_repo = event_repo

    def generate(self) -> None:
        """Generates the full event log sheet."""
        super().generate()

        headers = ["Turn", "Category", "Event Details", "Impact"]
        self._format_header(headers)

        events_data = [
            [0, "System", "Campaign Initialised.", "The Dominion of Auster is ready."],
            [1, "Diplomacy", "Tyra trade envoy arrives in Highreach.", "+500 Silver this turn."],
        ]
        self._append_data(events_data)
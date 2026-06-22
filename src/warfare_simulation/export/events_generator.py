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

        if self.event_repo is not None:
            events = self.event_repo.list_all()
            if events:
                self._append_data([
                    [
                        event.turn,
                        getattr(event.category, "value", str(event.category)),
                        self._format_event_details(event),
                        event.effect_summary or event.impact,
                    ]
                    for event in events
                ])
                return

        events_data = [
            [0, "System", "01/01/0001 | system → campaign | Campaign Initialised. | Cause: seed data", "The Dominion of Auster is ready."],
            [1, "Diplomacy", "01/01/0001 | faction:Tyra → province:Highreach | Tyra trade envoy arrives in Highreach. | Cause: seed example", "+500 Silver this turn."],
        ]
        self._append_data(events_data)

    @staticmethod
    def _format_event_details(event) -> str:
        """Return an observer-readable detail string while preserving legacy columns."""
        date = f"{event.day:02d}/{event.month:02d}/{event.year:04d}"
        cause = " → ".join(event.cause_chain) if event.cause_chain else "unspecified"
        target = event.target or "world"
        return (
            f"{date} | {event.actor} → {target} | "
            f"{event.description} | Source: {event.source_system} | Cause: {cause}"
        )

"""
Events domain models.

Models for campaign events and auditable state changes.
"""

from dataclasses import dataclass
from typing import Any

from warfare_simulation.core.base import GameEntity
from warfare_simulation.core.constants import EventCategory


@dataclass
class Event(GameEntity):
    """
    Represents a campaign event.

    Attributes:
        turn: Turn number when event occurred
        category: Event category
        description: Event description
        impact: What changed as a result
        affected_entities: IDs of entities affected (e.g., [kingdom_id, unit_id])
    """

    turn: int = 1
    category: EventCategory = EventCategory.SYSTEM
    description: str = ""
    impact: str = ""
    affected_entities: list = None

    def __post_init__(self):
        """Initialize affected_entities if None."""
        if self.affected_entities is None:
            self.affected_entities = []


@dataclass
class AuditLog(GameEntity):
    """Traceable record for an important campaign state mutation."""

    turn: int = 1
    month: int = 1
    year: int = 1
    actor: str = "system"
    target: str = ""
    system: str = "System"
    action: str = ""
    previous_value: Any = None
    new_value: Any = None
    reason: str = ""
    source_event_id: int | None = None

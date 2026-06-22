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
    day: int = 1
    month: int = 1
    year: int = 1
    actor: str = "system"
    target: str = ""
    source_system: str = "System"
    cause_chain: list[str] = None
    effect_summary: str = ""

    def __post_init__(self):
        """Initialize collection fields if None."""
        if self.affected_entities is None:
            self.affected_entities = []
        if self.cause_chain is None:
            self.cause_chain = []


@dataclass
class TurnSummary(GameEntity):
    """Persisted summary of a completed campaign turn."""

    turn: int = 1
    month: int = 1
    year: int = 1
    title: str = ""
    narrative: str = ""
    event_count: int = 0
    audit_count: int = 0
    highlights: list[str] = None

    def __post_init__(self):
        """Initialize highlights if None."""
        if self.highlights is None:
            self.highlights = []


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

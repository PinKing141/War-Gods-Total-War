"""
Events domain service.

Orchestrates event logging and campaign history.
"""

from warfare_simulation.core.base import GameSystem
from warfare_simulation.core.logger import get_logger
from warfare_simulation.core.constants import EventCategory
from .models import Event
from .repository import EventRepository


logger = get_logger(__name__)


class EventService(GameSystem):
    """
    Service for event logging and campaign history.
    
    Tracks all campaign events and provides history querying.
    """
    
    def __init__(self, event_repo: EventRepository):
        """Initialize Event service."""
        super().__init__("Events")
        self.event_repo = event_repo
        self.current_turn = 1
    
    def initialize(self) -> None:
        """Initialize Event service."""
        logger.info("Event service initialized")
        self._initialized = True
    
    def log_event(
        self,
        turn: int,
        category: EventCategory,
        description: str,
        impact: str = "",
        affected_entities: list = None,
    ) -> Event:
        """
        Log a campaign event.
        
        Args:
            turn: Turn number
            category: Event category
            description: What happened
            impact: What changed
            affected_entities: Entity IDs affected
        
        Returns:
            Created event
        """
        if affected_entities is None:
            affected_entities = []
        
        event = Event(
            turn=turn,
            category=category,
            description=description,
            impact=impact,
            affected_entities=affected_entities,
        )
        
        created = self.event_repo.create(event)
        logger.info(f"Event logged (turn {turn}): {description}")
        return created
    
    def log_kingdom_event(
        self,
        turn: int,
        description: str,
        impact: str,
        kingdom_id: int,
    ) -> Event:
        """
        Log a kingdom-related event.
        
        Args:
            turn: Turn number
            description: Event description
            impact: Impact description
            kingdom_id: Affected kingdom
        
        Returns:
            Created event
        """
        return self.log_event(
            turn,
            EventCategory.ECONOMY,
            description,
            impact,
            [kingdom_id],
        )
    
    def log_military_event(
        self,
        turn: int,
        description: str,
        impact: str,
        unit_id: int,
        location_id: int = None,
    ) -> Event:
        """
        Log a military event.
        
        Args:
            turn: Turn number
            description: Event description
            impact: Impact description
            unit_id: Affected unit
            location_id: Location of event
        
        Returns:
            Created event
        """
        affected = [unit_id]
        if location_id:
            affected.append(location_id)
        
        return self.log_event(
            turn,
            EventCategory.MILITARY,
            description,
            impact,
            affected,
        )
    
    def log_diplomatic_event(
        self,
        turn: int,
        description: str,
        impact: str,
        faction_a_id: int,
        faction_b_id: int,
    ) -> Event:
        """
        Log a diplomatic event.
        
        Args:
            turn: Turn number
            description: Event description
            impact: Impact description
            faction_a_id: First affected faction
            faction_b_id: Second affected faction
        
        Returns:
            Created event
        """
        return self.log_event(
            turn,
            EventCategory.DIPLOMACY,
            description,
            impact,
            [faction_a_id, faction_b_id],
        )
    
    def get_turn_summary(self, turn: int) -> str:
        """
        Get summary of all events in a turn.
        
        Args:
            turn: Turn to summarize
        
        Returns:
            Formatted summary
        """
        events = self.event_repo.get_by_turn(turn)
        
        summary = f"--- Turn {turn} Summary ---\n"
        summary += f"Total events: {len(events)}\n\n"
        
        for event in events:
            summary += f"[{event.category.value}] {event.description}\n"
            if event.impact:
                summary += f"  Impact: {event.impact}\n"
            summary += "\n"
        
        return summary
    
    def advance_turn(self, turn_number: int) -> None:
        """
        Execute event systems for this turn.
        
        Args:
            turn_number: Current campaign turn
        """
        self.current_turn = turn_number
        # Event-specific turn logic can be added here
    
    def validate_state(self) -> list:
        """
        Validate all event state.
        
        Returns:
            List of validation error messages
        """
        # Event service doesn't have state to validate
        return []

"""
Events domain repository.

Data access for events and campaign logs.
"""

from typing import Optional, List
from warfare_simulation.persistence.repository import Repository
from warfare_simulation.core.exceptions import RepositoryError
from warfare_simulation.core.constants import EventCategory
from .models import Event


class EventRepository(Repository[Event]):
    """Repository for Event entities."""
    
    def __init__(self, db_manager=None):
        """Initialize Event repository."""
        super().__init__(db_manager)
        self._events: dict = {}
        self._next_id = 1
    
    def create(self, entity: Event) -> Event:
        """Create a new event."""
        entity.id = self._next_id
        entity.mark_updated()
        self._events[self._next_id] = entity
        self._next_id += 1
        return entity
    
    def get(self, entity_id: int) -> Optional[Event]:
        """Fetch event by ID."""
        return self._events.get(entity_id)
    
    def get_by_turn(self, turn: int) -> List[Event]:
        """Fetch all events for a specific turn."""
        return [e for e in self._events.values() if e.turn == turn]
    
    def get_by_category(self, category: EventCategory) -> List[Event]:
        """Fetch all events of a specific category."""
        return [e for e in self._events.values() if e.category == category]
    
    def get_recent(self, count: int = 10) -> List[Event]:
        """Fetch most recent events."""
        sorted_events = sorted(self._events.values(), key=lambda e: e.id, reverse=True)
        return sorted_events[:count]
    
    def update(self, entity: Event) -> Event:
        """Update existing event."""
        if entity.id not in self._events:
            raise RepositoryError(f"Event with ID {entity.id} not found")
        
        entity.mark_updated()
        self._events[entity.id] = entity
        return entity
    
    def delete(self, entity_id: int) -> bool:
        """Delete event by ID."""
        if entity_id in self._events:
            del self._events[entity_id]
            return True
        return False
    
    def list_all(self) -> List[Event]:
        """Fetch all events."""
        return list(self._events.values())

    def hydrate(self, entity: Event) -> Event:
        """Load an event with a pre-assigned ID from SQLite."""
        return self._hydrate_entity(entity, self._events)

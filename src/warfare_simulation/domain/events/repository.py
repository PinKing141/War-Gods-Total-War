"""
Events domain repository.

Data access for events and campaign audit logs.
"""

import json
from typing import List, Optional

from warfare_simulation.core.constants import EventCategory
from warfare_simulation.core.exceptions import RepositoryError
from warfare_simulation.persistence.repository import Repository

from .models import AuditLog, Event


class EventRepository(Repository[Event]):
    """Repository for Event entities."""

    def __init__(self, db_manager=None):
        """Initialize Event repository."""
        super().__init__(db_manager)
        self._events: dict = {}
        self._next_id = 1

    def create(self, entity: Event) -> Event:
        """Create a new event."""
        entity.mark_updated()
        if self.db_manager is not None and self.db_manager.conn:
            cursor = self.db_manager.execute(
                """
                INSERT INTO event (turn, category, description, impact, affected_entities)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    entity.turn,
                    entity.category.value,
                    entity.description,
                    entity.impact,
                    json.dumps(entity.affected_entities),
                ),
            )
            self.db_manager.commit()
            entity.id = cursor.lastrowid
        else:
            entity.id = self._next_id
            self._next_id += 1
        self._events[entity.id] = entity
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


class AuditLogRepository(Repository[AuditLog]):
    """Repository for auditable state mutation records."""

    def __init__(self, db_manager=None):
        """Initialize audit-log repository."""
        super().__init__(db_manager)
        self._logs: dict = {}
        self._next_id = 1

    def create(self, entity: AuditLog) -> AuditLog:
        """Create a new audit-log record."""
        entity.mark_updated()
        if self.db_manager is not None and self.db_manager.conn:
            cursor = self.db_manager.execute(
                """
                INSERT INTO audit_log (
                    turn, month, year, actor, target, system, action,
                    previous_value, new_value, reason, source_event_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entity.turn,
                    entity.month,
                    entity.year,
                    entity.actor,
                    entity.target,
                    entity.system,
                    entity.action,
                    json.dumps(entity.previous_value),
                    json.dumps(entity.new_value),
                    entity.reason,
                    entity.source_event_id,
                ),
            )
            self.db_manager.commit()
            entity.id = cursor.lastrowid
        else:
            entity.id = self._next_id
            self._next_id += 1
        self._logs[entity.id] = entity
        return entity

    def get(self, entity_id: int) -> Optional[AuditLog]:
        """Fetch audit log by ID."""
        return self._logs.get(entity_id)

    def get_by_turn(self, turn: int) -> List[AuditLog]:
        """Fetch all audit logs for a turn."""
        return [log for log in self._logs.values() if log.turn == turn]

    def get_by_system(self, system: str) -> List[AuditLog]:
        """Fetch audit logs for a simulation system."""
        return [log for log in self._logs.values() if log.system == system]

    def update(self, entity: AuditLog) -> AuditLog:
        """Update an existing audit-log record."""
        if entity.id not in self._logs:
            raise RepositoryError(f"AuditLog with ID {entity.id} not found")
        entity.mark_updated()
        self._logs[entity.id] = entity
        return entity

    def delete(self, entity_id: int) -> bool:
        """Delete audit log by ID."""
        if entity_id in self._logs:
            del self._logs[entity_id]
            return True
        return False

    def list_all(self) -> List[AuditLog]:
        """Fetch all audit logs."""
        return list(self._logs.values())

    def hydrate(self, entity: AuditLog) -> AuditLog:
        """Load an audit log with a pre-assigned ID from SQLite."""
        return self._hydrate_entity(entity, self._logs)

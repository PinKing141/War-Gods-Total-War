"""SQLite persistence for deterministic scheduler queue state."""

from __future__ import annotations

import json
from typing import Iterable

from warfare_simulation.orchestration.pulse_scheduler import ScheduledEvent
from warfare_simulation.orchestration.game_state import SimDate
from warfare_simulation.persistence.database import DatabaseManager


class ScheduledEventRepository:
    """Persist and hydrate scheduled events for long-running campaign reloads."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def replace_all(self, events: Iterable[ScheduledEvent]) -> None:
        """Replace the SQLite scheduler queue snapshot with the supplied events."""
        self.db_manager.execute("DELETE FROM scheduled_event")
        for event in events:
            self.upsert(event, commit=False)
        self.db_manager.commit()

    def upsert(self, event: ScheduledEvent, *, commit: bool = True) -> ScheduledEvent:
        """Insert or update one scheduled event by deterministic scheduler ID."""
        self.db_manager.execute(
            """
            INSERT INTO scheduled_event (
                event_id, due_day, due_month, due_year, event_type,
                actor, target, payload, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(event_id) DO UPDATE SET
                due_day = excluded.due_day,
                due_month = excluded.due_month,
                due_year = excluded.due_year,
                event_type = excluded.event_type,
                actor = excluded.actor,
                target = excluded.target,
                payload = excluded.payload,
                status = excluded.status,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                event.id,
                event.due_date.day,
                event.due_date.month,
                event.due_date.year,
                event.event_type,
                event.actor,
                event.target,
                json.dumps(event.payload, sort_keys=True),
                event.status,
            ),
        )
        if commit:
            self.db_manager.commit()
        return event

    def list_all(self) -> list[ScheduledEvent]:
        """Load all scheduled events in deterministic queue order."""
        rows = self.db_manager.execute(
            """
            SELECT event_id, due_day, due_month, due_year, event_type,
                   actor, target, payload, status
            FROM scheduled_event
            ORDER BY due_year, due_month, due_day, event_id
            """
        ).fetchall()
        return [
            ScheduledEvent(
                id=row[0],
                due_date=SimDate(day=int(row[1]), month=int(row[2]), year=int(row[3])),
                event_type=row[4],
                actor=row[5],
                target=row[6],
                payload=json.loads(row[7] or "{}"),
                status=row[8],
            )
            for row in rows
        ]

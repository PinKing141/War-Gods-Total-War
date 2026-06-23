"""Deterministic simulation pulse scheduler."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from warfare_simulation.orchestration.game_state import SimDate

PulseHook = Callable[[SimDate], None]
ScheduledEventHook = Callable[["ScheduledEvent", SimDate], None]


@dataclass(frozen=True)
class PulseReport:
    """Pulse boundaries and scheduled events due for a single simulated day."""

    date: SimDate
    pulses: tuple[str, ...]
    scheduled_events: tuple["ScheduledEvent", ...] = ()

    def includes(self, pulse: str) -> bool:
        """Return True when the named pulse is due on this date."""
        return pulse in self.pulses


@dataclass(frozen=True)
class ScheduledEvent:
    """A deterministic day-level work item owned by the simulation scheduler."""

    id: str
    due_date: SimDate
    event_type: str
    actor: str
    target: str
    payload: dict[str, Any] = field(default_factory=dict)
    status: str = "pending"

    def __post_init__(self) -> None:
        if self.status not in {"pending", "completed", "cancelled"}:
            raise ValueError(f"Unsupported scheduled event status: {self.status}")
        if isinstance(self.due_date, dict):
            object.__setattr__(self, "due_date", SimDate(**self.due_date))

    def is_due(self, current_date: SimDate) -> bool:
        """Return True when this event should resolve on or before ``current_date``."""
        return self.status == "pending" and self._date_key(self.due_date) <= self._date_key(
            current_date
        )

    def mark_completed(self) -> "ScheduledEvent":
        """Return a completed copy of this event."""
        return ScheduledEvent(
            id=self.id,
            due_date=self.due_date,
            event_type=self.event_type,
            actor=self.actor,
            target=self.target,
            payload=dict(self.payload),
            status="completed",
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable scheduler checkpoint row."""
        return {
            "id": self.id,
            "due_date": {
                "day": self.due_date.day,
                "month": self.due_date.month,
                "year": self.due_date.year,
            },
            "event_type": self.event_type,
            "actor": self.actor,
            "target": self.target,
            "payload": self.payload,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ScheduledEvent":
        """Build a scheduled event from a checkpoint row."""
        due_date = data.get("due_date", {})
        return cls(
            id=str(data["id"]),
            due_date=due_date if isinstance(due_date, SimDate) else SimDate(**due_date),
            event_type=str(data["event_type"]),
            actor=str(data["actor"]),
            target=str(data["target"]),
            payload=dict(data.get("payload", {})),
            status=str(data.get("status", "pending")),
        )

    @staticmethod
    def _date_key(date: SimDate) -> tuple[int, int, int]:
        return date.year, date.month, date.day


@dataclass
class PulseScheduler:
    """Schedules pulse hooks and day-level events in deterministic order.

    Orchestration owns state mutation; this class owns cadence and queue ordering.
    A date can be processed once per scheduler instance, preventing accidental
    double execution at month/year boundaries.
    """

    hooks: dict[str, list[PulseHook]] = field(default_factory=dict)
    scheduled_event_hooks: dict[str, list[ScheduledEventHook]] = field(default_factory=dict)
    scheduled_events: list[ScheduledEvent] = field(default_factory=list)
    _processed_dates: set[tuple[int, int, int]] = field(default_factory=set, init=False)

    PULSE_ORDER = ("daily", "weekly", "monthly", "seasonal", "yearly")
    SEASON_START_MONTHS = (1, 4, 7, 10)

    def register(self, pulse: str, hook: PulseHook) -> None:
        """Register a hook for a supported pulse type."""
        if pulse not in self.PULSE_ORDER:
            raise ValueError(f"Unsupported pulse type: {pulse}")
        self.hooks.setdefault(pulse, []).append(hook)

    def register_scheduled_event_hook(self, event_type: str, hook: ScheduledEventHook) -> None:
        """Register a resolver for a scheduled event type."""
        self.scheduled_event_hooks.setdefault(event_type, []).append(hook)

    def schedule_event(self, event: ScheduledEvent) -> ScheduledEvent:
        """Add a pending event to the queue and keep deterministic due-date ordering."""
        if any(existing.id == event.id for existing in self.scheduled_events):
            raise ValueError(f"Scheduled event already exists: {event.id}")
        self.scheduled_events.append(event)
        self.scheduled_events.sort(
            key=lambda item: (item.due_date.year, item.due_date.month, item.due_date.day, item.id)
        )
        return event

    def due_pulses(self, previous_date: SimDate, current_date: SimDate) -> tuple[str, ...]:
        """Return ordered pulses due after advancing to ``current_date``."""
        pulses: list[str] = ["daily"]
        if self._is_week_boundary(current_date):
            pulses.append("weekly")
        if self._is_month_boundary(previous_date, current_date):
            pulses.append("monthly")
            if current_date.month in self.SEASON_START_MONTHS:
                pulses.append("seasonal")
            if current_date.month == 1:
                pulses.append("yearly")
        return tuple(pulses)

    def run_due_pulses(self, previous_date: SimDate, current_date: SimDate) -> PulseReport:
        """Run registered hooks and due scheduled events once for ``current_date``."""
        key = (current_date.year, current_date.month, current_date.day)
        if key in self._processed_dates:
            return PulseReport(current_date, ())

        pulses = self.due_pulses(previous_date, current_date)
        self._processed_dates.add(key)
        for pulse in pulses:
            for hook in self.hooks.get(pulse, []):
                hook(current_date)
        due_events = self._resolve_due_events(current_date)
        return PulseReport(current_date, pulses, due_events)

    def checkpoint(self) -> dict[str, Any]:
        """Return serializable scheduler queue state for save/checkpoint files."""
        return {"scheduled_events": [event.to_dict() for event in self.scheduled_events]}

    def restore_checkpoint(self, data: dict[str, Any]) -> None:
        """Restore scheduled queue state from a checkpoint payload."""
        self.scheduled_events = [
            ScheduledEvent.from_dict(row) for row in data.get("scheduled_events", [])
        ]
        self.scheduled_events.sort(
            key=lambda item: (item.due_date.year, item.due_date.month, item.due_date.day, item.id)
        )
        self._processed_dates.clear()

    def _resolve_due_events(self, current_date: SimDate) -> tuple[ScheduledEvent, ...]:
        due: list[ScheduledEvent] = []
        updated: list[ScheduledEvent] = []
        for event in self.scheduled_events:
            if event.is_due(current_date):
                for hook in self.scheduled_event_hooks.get(event.event_type, []):
                    hook(event, current_date)
                completed = event.mark_completed()
                due.append(completed)
                updated.append(completed)
            else:
                updated.append(event)
        self.scheduled_events = updated
        return tuple(due)

    @staticmethod
    def _is_week_boundary(current_date: SimDate) -> bool:
        """Treat every seventh in-world day as the weekly pulse boundary."""
        return current_date.day % 7 == 0

    @staticmethod
    def _is_month_boundary(previous_date: SimDate, current_date: SimDate) -> bool:
        """Return True when a daily tick entered a new month."""
        return previous_date.month != current_date.month or previous_date.year != current_date.year

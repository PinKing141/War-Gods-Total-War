"""Deterministic simulation pulse scheduler."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from warfare_simulation.orchestration.game_state import SimDate


PulseHook = Callable[[SimDate], None]


@dataclass(frozen=True)
class PulseReport:
    """Pulse boundaries due for a single simulated day."""

    date: SimDate
    pulses: tuple[str, ...]

    def includes(self, pulse: str) -> bool:
        """Return True when the named pulse is due on this date."""
        return pulse in self.pulses


@dataclass
class PulseScheduler:
    """Schedules pulse hooks in a deterministic, duplicate-safe order.

    The scheduler is intentionally small: orchestration owns state mutation, while
    this class owns cadence. A date can be processed once per scheduler instance;
    repeated attempts return an empty report, preventing accidental double execution
    at month/year boundaries.
    """

    hooks: dict[str, list[PulseHook]] = field(default_factory=dict)
    _processed_dates: set[tuple[int, int, int]] = field(default_factory=set, init=False)

    PULSE_ORDER = ("daily", "weekly", "monthly", "seasonal", "yearly")
    SEASON_START_MONTHS = (1, 4, 7, 10)

    def register(self, pulse: str, hook: PulseHook) -> None:
        """Register a hook for a supported pulse type."""
        if pulse not in self.PULSE_ORDER:
            raise ValueError(f"Unsupported pulse type: {pulse}")
        self.hooks.setdefault(pulse, []).append(hook)

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
        """Run registered hooks for due pulses once for ``current_date``."""
        key = (current_date.year, current_date.month, current_date.day)
        if key in self._processed_dates:
            return PulseReport(current_date, ())

        pulses = self.due_pulses(previous_date, current_date)
        self._processed_dates.add(key)
        for pulse in pulses:
            for hook in self.hooks.get(pulse, []):
                hook(current_date)
        return PulseReport(current_date, pulses)

    @staticmethod
    def _is_week_boundary(current_date: SimDate) -> bool:
        """Treat every seventh in-world day as the weekly pulse boundary."""
        return current_date.day % 7 == 0

    @staticmethod
    def _is_month_boundary(previous_date: SimDate, current_date: SimDate) -> bool:
        """Return True when a daily tick entered a new month."""
        return previous_date.month != current_date.month or previous_date.year != current_date.year

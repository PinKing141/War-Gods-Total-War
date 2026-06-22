"""Pulse scheduling primitives for in-world simulation cadence."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable

from warfare_simulation.orchestration.game_state import GameState


class PulseType(str, Enum):
    """Supported simulation pulse cadences."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    SEASONAL = "seasonal"
    YEARLY = "yearly"


@dataclass(frozen=True)
class PulseContext:
    """Boundary facts for a single simulated-day advancement."""

    current_day: int
    current_month: int
    current_year: int
    current_turn: int
    month_rolled: bool = False
    year_rolled: bool = False

    @classmethod
    def from_transition(
        cls, before: GameState, after: GameState, month_rolled: bool
    ) -> "PulseContext":
        """Build context from the clock state before and after a daily tick."""
        return cls(
            current_day=after.current_day,
            current_month=after.current_month,
            current_year=after.current_year,
            current_turn=after.current_turn,
            month_rolled=month_rolled,
            year_rolled=after.current_year != before.current_year,
        )

    @property
    def pulses(self) -> tuple[PulseType, ...]:
        """Return the pulse types that should execute for this boundary."""
        pulses = [PulseType.DAILY]
        if self.current_day % 7 == 0:
            pulses.append(PulseType.WEEKLY)
        if self.month_rolled:
            pulses.append(PulseType.MONTHLY)
            if self.current_month in (1, 4, 7, 10):
                pulses.append(PulseType.SEASONAL)
        if self.year_rolled:
            pulses.append(PulseType.YEARLY)
        return tuple(pulses)


PulseHook = Callable[[PulseContext], None]


@dataclass
class PulseScheduler:
    """Deterministic hook scheduler for daily simulation boundaries."""

    _hooks: dict[PulseType, list[tuple[str, PulseHook]]] = field(
        default_factory=lambda: {pulse: [] for pulse in PulseType}
    )

    def register(self, pulse: PulseType, name: str, hook: PulseHook) -> None:
        """Register a named hook for a pulse, rejecting duplicate names."""
        registered = self._hooks[pulse]
        if any(existing_name == name for existing_name, _hook in registered):
            raise ValueError(f"Pulse hook already registered for {pulse.value}: {name}")
        registered.append((name, hook))

    def run(self, context: PulseContext) -> tuple[str, ...]:
        """Run hooks for all pulses in order and return executed hook identifiers."""
        executed: list[str] = []
        for pulse in context.pulses:
            for name, hook in self._hooks[pulse]:
                hook(context)
                executed.append(f"{pulse.value}:{name}")
        return tuple(executed)

    def registered_hook_names(self, pulse: PulseType) -> tuple[str, ...]:
        """Return registered hook names for diagnostics and tests."""
        return tuple(name for name, _hook in self._hooks[pulse])

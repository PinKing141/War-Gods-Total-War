"""Campaign state snapshot and checkpoint helpers."""

from __future__ import annotations

import calendar
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


SIMULATION_SPEEDS = ("paused", "1x", "2x", "5x", "fast")


@dataclass(frozen=True)
class SimDate:
    """Canonical observer-facing in-world calendar date."""

    day: int = 1
    month: int = 1
    year: int = 1

    def __post_init__(self) -> None:
        """Validate date component ranges early."""
        if self.month < 1 or self.month > 12:
            raise ValueError(f"Month must be between 1 and 12: {self.month}")
        if self.year < 1:
            raise ValueError(f"Year must be positive: {self.year}")
        max_day = calendar.monthrange(self.year, self.month)[1]
        if self.day < 1 or self.day > max_day:
            raise ValueError(f"Day must be between 1 and {max_day}: {self.day}")

    def formatted(self) -> str:
        """Return the date in observer-facing DD/MM/YYYY format."""
        return f"{self.day:02d}/{self.month:02d}/{self.year:04d}"

    def advance_day(self) -> tuple["SimDate", bool, bool]:
        """Return the next date plus month/year rollover flags."""
        next_day = self.day + 1
        if next_day <= calendar.monthrange(self.year, self.month)[1]:
            return SimDate(next_day, self.month, self.year), False, False

        next_month = self.month + 1
        next_year = self.year
        year_rolled = False
        if next_month > 12:
            next_month = 1
            next_year += 1
            year_rolled = True
        return SimDate(1, next_month, next_year), True, year_rolled


@dataclass
class GameState:
    """Tracks campaign clock state outside any single domain."""

    current_day: int = 1
    current_turn: int = 1
    current_month: int = 1
    current_year: int = 1
    simulation_speed: str = "paused"

    def __post_init__(self) -> None:
        """Normalize persisted clock values to their runtime types."""
        self.current_day = int(self.current_day)
        self.current_turn = int(self.current_turn)
        self.current_month = int(self.current_month)
        self.current_year = int(self.current_year)
        self.simulation_speed = str(self.simulation_speed)
        # Validate the restored canonical date.
        self.sim_date

    @staticmethod
    def days_in_month(month: int, year: int) -> int:
        """Return the number of days in a given month/year pair."""
        return calendar.monthrange(max(1, year), month)[1]

    def advance_day(self) -> bool:
        """Advance the campaign clock by one day.

        Returns:
            True when the date rolls into a new month.
        """
        next_date, month_rolled, _year_rolled = self.sim_date.advance_day()
        self.current_day = next_date.day
        self.current_month = next_date.month
        self.current_year = next_date.year
        if month_rolled:
            self.current_turn += 1
        return month_rolled

    def advance_turn(self) -> None:
        """Advance the global campaign clock by one monthly turn."""
        self.current_day = 1
        self.current_turn += 1
        self.current_month += 1
        if self.current_month > 12:
            self.current_month = 1
            self.current_year += 1

    def set_speed(self, speed: str) -> None:
        """Set the active simulation speed label."""
        if speed not in SIMULATION_SPEEDS:
            raise ValueError(f"Unsupported simulation speed: {speed}")
        self.simulation_speed = speed

    def is_paused(self) -> bool:
        """Return True when the simulation is not auto-advancing."""
        return self.simulation_speed == "paused"

    def formatted_date(self) -> str:
        """Return the observer-facing date string."""
        return self.sim_date.formatted()

    @property
    def sim_date(self) -> SimDate:
        """Return the canonical date object for the current state."""
        return SimDate(self.current_day, self.current_month, self.current_year)

    def sync_from_kingdom(self, kingdom: Any) -> None:
        """Mirror clock fields from the active kingdom aggregate."""
        self.current_day = int(getattr(kingdom, "current_day", 1))
        self.current_turn = int(kingdom.current_turn)
        self.current_month = int(kingdom.current_month)
        self.current_year = int(kingdom.current_year)

    def to_dict(self) -> dict[str, int | str]:
        """Return a serializable state snapshot."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GameState":
        """Build a state snapshot from serialized data."""
        return cls(
            current_day=int(data.get("current_day", 1)),
            current_turn=int(data.get("current_turn", 1)),
            current_month=int(data.get("current_month", 1)),
            current_year=int(data.get("current_year", 1)),
            simulation_speed=str(data.get("simulation_speed", "paused")),
        )

    def save_checkpoint(self, filename: str | Path) -> Path:
        """Write the current game-state clock to JSON."""
        path = Path(filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2) + "\n", encoding="utf-8")
        return path

    @classmethod
    def load_checkpoint(cls, filename: str | Path) -> "GameState":
        """Load a game-state clock checkpoint from JSON."""
        path = Path(filename)
        return cls.from_dict(json.loads(path.read_text(encoding="utf-8")))

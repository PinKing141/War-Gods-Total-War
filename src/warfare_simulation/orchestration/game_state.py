"""Campaign state snapshot and checkpoint helpers."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class GameState:
    """Tracks campaign clock state outside any single domain."""

    current_turn: int = 1
    current_month: int = 1
    current_year: int = 1

    def advance_turn(self) -> None:
        """Advance the global campaign clock by one monthly turn."""
        self.current_turn += 1
        self.current_month += 1
        if self.current_month > 12:
            self.current_month = 1
            self.current_year += 1

    def sync_from_kingdom(self, kingdom: Any) -> None:
        """Mirror clock fields from the active kingdom aggregate."""
        self.current_turn = kingdom.current_turn
        self.current_month = kingdom.current_month
        self.current_year = kingdom.current_year

    def to_dict(self) -> dict[str, int]:
        """Return a serializable state snapshot."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GameState":
        """Build a state snapshot from serialized data."""
        return cls(
            current_turn=int(data.get("current_turn", 1)),
            current_month=int(data.get("current_month", 1)),
            current_year=int(data.get("current_year", 1)),
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

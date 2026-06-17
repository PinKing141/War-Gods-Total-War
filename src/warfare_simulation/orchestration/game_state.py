"""Lightweight campaign state snapshot for the thin application slice."""

from dataclasses import dataclass


@dataclass
class GameState:
    """Tracks the current campaign turn."""

    current_turn: int = 1

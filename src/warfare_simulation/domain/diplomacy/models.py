"""
Diplomacy domain models.

Models for factions, relations, and espionage.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from warfare_simulation.core.base import GameEntity
from warfare_simulation.core.constants import FactionStatus


@dataclass
class Faction(GameEntity):
    """
    Represents a foreign faction/nation.
    
    Attributes:
        name: Faction name
        faction_type: Type (nation, tribe, order, etc.)
        government_type: Type of government
        power_level: Military power (0-100)
        wealth: Economic power (0-100)
        stability: Internal stability (0-100)
    """
    
    name: str = ""
    faction_type: str = ""  # "nation", "tribe", "order", etc.
    government_type: str = ""
    power_level: int = 50
    wealth: int = 50
    stability: int = 50


@dataclass
class Relation(GameEntity):
    """
    Represents a diplomatic relation between two factions.
    
    Attributes:
        faction_a_id: First faction
        faction_b_id: Second faction
        status: Diplomatic status (Ally, Enemy, Neutral, etc.)
        opinion: Opinion score (-100 to +100)
        trust: Trust level (-100 to +100)
        trade_agreement: Whether trade pact exists
        military_alliance: Whether military alliance exists
    """
    
    faction_a_id: int = 0
    faction_b_id: int = 0
    status: FactionStatus = FactionStatus.NEUTRAL
    opinion: int = 0  # -100 (hate) to +100 (love)
    trust: int = 0  # -100 (distrust) to +100 (trust)
    trade_agreement: bool = False
    military_alliance: bool = False
    
    def shift_opinion(self, delta: int) -> None:
        """
        Shift opinion (clamped -100 to +100).
        
        Args:
            delta: Change in opinion
        """
        self.opinion = max(-100, min(100, self.opinion + delta))
        self.mark_updated()
    
    def shift_trust(self, delta: int) -> None:
        """
        Shift trust (clamped -100 to +100).
        
        Args:
            delta: Change in trust
        """
        self.trust = max(-100, min(100, self.trust + delta))
        self.mark_updated()


@dataclass
class Spy(GameEntity):
    """
    Represents a spy/agent working for a faction.
    
    Attributes:
        kingdom_id: Kingdom employing this spy
        codename: Spy codename
        target_faction_id: Faction being spied on
        skill_level: Spy skill (0-100)
        risk_level: Risk of discovery (0-100)
        status: Current status (Active, Discovered, Captured, etc.)
        last_report: Last intelligence gathered
    """
    
    kingdom_id: int = 0
    codename: str = ""
    target_faction_id: int = 0
    skill_level: int = 50
    risk_level: int = 0  # 0% to 100% chance of discovery
    status: str = "Active"
    last_report: str = ""
    
    def increase_risk(self, amount: int) -> None:
        """Increase discovery risk."""
        self.risk_level = min(100, self.risk_level + amount)
        self.mark_updated()
    
    def decrease_risk(self, amount: int) -> None:
        """Decrease discovery risk."""
        self.risk_level = max(0, self.risk_level - amount)
        self.mark_updated()


@dataclass
class Mission(GameEntity):
    """
    Represents a diplomatic or espionage mission.
    
    Attributes:
        kingdom_id: Kingdom executing mission
        target_faction_id: Target faction
        mission_type: Type (trade, espionage, military, alliance, etc.)
        success_chance: Estimated success percentage
        duration: Number of turns to complete
        turns_remaining: Turns left
        status: Current status (Planning, Active, Completed, Failed, etc.)
    """
    
    kingdom_id: int = 0
    target_faction_id: int = 0
    mission_type: str = ""  # "trade", "espionage", "military", "alliance", etc.
    success_chance: int = 50
    duration: int = 3
    turns_remaining: int = 3
    status: str = "Planning"
    
    def advance_turn(self) -> None:
        """Advance mission by one turn."""
        if self.turns_remaining > 0:
            self.turns_remaining -= 1
            if self.turns_remaining == 0:
                self.status = "Completed"
        self.mark_updated()

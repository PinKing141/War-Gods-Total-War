"""
Military domain models.

Models for units, commanders, and military operations.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from warfare_simulation.core.base import GameEntity
from warfare_simulation.core.constants import (
    UnitType,
    ArmorType,
    CommanderRole,
    UnitStatus,
    DEFAULT_MORALE,
)


@dataclass
class Unit(GameEntity):
    """
    Represents a military unit.

    Attributes:
        kingdom_id: Kingdom this unit belongs to
        name: Unit name (e.g., "Vanguard I")
        unit_type: Type of unit (HEAVY_SPEARMEN, RANGED, etc.)
        soldiers: Current soldier count
        veterans: Experienced soldiers
        morale: Unit morale (0-100)
        fatigue: Unit fatigue (0-100)
        armor: Armor type
        location_id: Province where unit is stationed
        commander_id: Commander of unit
        status: Current unit status
    """

    kingdom_id: int = 0
    name: str = ""
    unit_type: UnitType = UnitType.HEAVY_SPEARMEN
    soldiers: int = 0
    veterans: int = 0
    morale: int = DEFAULT_MORALE
    fatigue: int = 0
    armor: ArmorType = ArmorType.BRIGANDINE
    location_id: int = 0
    commander_id: Optional[int] = None
    status: UnitStatus = UnitStatus.ACTIVE

    def get_total_strength(self) -> int:
        """Get total unit strength (soldiers + veterans)."""
        return self.soldiers + self.veterans

    def get_morale_status(self) -> str:
        """Get morale classification."""
        if self.morale < 20:
            return "Broken"
        elif self.morale < 40:
            return "Low"
        elif self.morale < 60:
            return "Neutral"
        elif self.morale < 80:
            return "Good"
        else:
            return "Excellent"

    def set_morale(self, morale: int) -> None:
        """Set unit morale (0-100)."""
        if not 0 <= morale <= 100:
            raise ValueError(f"Morale must be 0-100, got {morale}")
        self.morale = morale
        self.mark_updated()

    def add_fatigue(self, amount: int) -> None:
        """Add fatigue to unit (max 100)."""
        self.fatigue = min(100, self.fatigue + amount)
        self.mark_updated()

    def reduce_fatigue(self, amount: int) -> None:
        """Reduce fatigue from unit."""
        self.fatigue = max(0, self.fatigue - amount)
        self.mark_updated()

    def take_casualties(self, regular_casualties: int, veteran_casualties: int) -> None:
        """
        Apply casualties to unit.

        Args:
            regular_casualties: Regular soldier losses
            veteran_casualties: Veteran soldier losses
        """
        self.soldiers = max(0, self.soldiers - regular_casualties)
        self.veterans = max(0, self.veterans - veteran_casualties)

        # Morale hits from casualties
        total_lost = regular_casualties + veteran_casualties
        morale_hit = min(20, total_lost // 10)  # 10 casualties = 1 morale loss
        self.set_morale(max(0, self.morale - morale_hit))

        self.mark_updated()


@dataclass
class Commander(GameEntity):
    """
    Represents a military commander or leader.

    Attributes:
        kingdom_id: Kingdom this commander serves
        name: Commander name
        role: Position held
        leadership: Leadership skill (0-100)
        tactics: Tactical skill (0-100)
        logistics: Logistics skill (0-100)
        loyalty: Loyalty to kingdom (0-100)
        status: Current status (Active, Wounded, Captured, etc.)
        traits: Special traits or characteristics
    """

    kingdom_id: int = 0
    name: str = ""
    role: CommanderRole = CommanderRole.CAPTAIN
    leadership: int = 50
    tactics: int = 50
    logistics: int = 50
    loyalty: int = 75
    status: str = "Active"
    traits: str = ""

    def get_average_skill(self) -> int:
        """Get average of all skills."""
        return (self.leadership + self.tactics + self.logistics) // 3

    def set_skill(self, skill_name: str, value: int) -> None:
        """Set a skill (0-100)."""
        if not 0 <= value <= 100:
            raise ValueError(f"Skill must be 0-100, got {value}")

        if skill_name == "leadership":
            self.leadership = value
        elif skill_name == "tactics":
            self.tactics = value
        elif skill_name == "logistics":
            self.logistics = value
        else:
            raise ValueError(f"Unknown skill: {skill_name}")

        self.mark_updated()


@dataclass
class BattleReport(GameEntity):
    """Auditable result of one deterministic field battle.

    The report is a read model produced after unit state has already been
    mutated. It keeps the facts needed for observer chronicles without
    requiring prose generation to inspect live unit objects.
    """

    location_id: int = 0
    attacker_unit_id: int = 0
    defender_unit_id: int = 0
    attacker_commander_id: Optional[int] = None
    defender_commander_id: Optional[int] = None
    attacker_power: int = 0
    defender_power: int = 0
    attacker_casualties: int = 0
    defender_casualties: int = 0
    attacker_morale_shift: int = 0
    defender_morale_shift: int = 0
    attacker_fatigue_shift: int = 0
    defender_fatigue_shift: int = 0
    winner: str = "draw"
    retreating_side: Optional[str] = None
    pursuit_casualties: int = 0
    commander_risk: str = "low"
    battle_log: List[str] = field(default_factory=list)
    chronicle_entry: str = ""

    @property
    def referenced_unit_ids(self) -> List[int]:
        """Return unit IDs used by this report for audit cross-reference."""
        return [self.attacker_unit_id, self.defender_unit_id]


@dataclass
class Garrison(GameEntity):
    """
    Represents a military garrison in a location.

    Tracks unit positioning and defenses at specific locations.
    """

    location_id: int = 0
    unit_ids: List[int] = field(default_factory=list)  # Units in garrison
    commander_id: Optional[int] = None
    food_requirement: int = 0  # Monthly food needed
    defense_bonus: int = 0  # Defensive bonus from fortifications

    def add_unit(self, unit_id: int) -> None:
        """Add unit to garrison."""
        if unit_id not in self.unit_ids:
            self.unit_ids.append(unit_id)
            self.mark_updated()

    def remove_unit(self, unit_id: int) -> None:
        """Remove unit from garrison."""
        if unit_id in self.unit_ids:
            self.unit_ids.remove(unit_id)
            self.mark_updated()

    def get_unit_count(self) -> int:
        """Get number of units in garrison."""
        return len(self.unit_ids)

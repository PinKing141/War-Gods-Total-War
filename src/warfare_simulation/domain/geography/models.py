"""
Geography domain models.

Models for provinces, locations, and spatial relationships.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from warfare_simulation.core.base import GameEntity
from warfare_simulation.core.constants import DEFAULT_LOYALTY


@dataclass
class Province(GameEntity):
    """
    Represents a province/region in the kingdom.
    
    Attributes:
        kingdom_id: Kingdom this province belongs to
        name: Province name
        population: Resident population
        fort_level: Fortification level (0-5)
        food_stored: Grain reserves
        monthly_tax: Tax income from this province
        loyalty: Population loyalty (0-100)
        garrison_size: Current military garrison
        garrison_capacity: Maximum garrison capacity
        governor_name: Name of province governor
    """
    
    kingdom_id: int = 0
    name: str = ""
    population: int = 0
    fort_level: int = 0
    food_stored: int = 0
    monthly_tax: int = 0
    loyalty: int = DEFAULT_LOYALTY
    garrison_size: int = 0
    garrison_capacity: int = 1000
    governor_name: str = ""
    
    def set_loyalty(self, loyalty: int) -> None:
        """Set province loyalty (0-100)."""
        if not 0 <= loyalty <= 100:
            raise ValueError(f"Loyalty must be 0-100, got {loyalty}")
        self.loyalty = loyalty
        self.mark_updated()
    
    def add_garrison(self, soldiers: int) -> None:
        """Add soldiers to garrison."""
        if self.garrison_size + soldiers > self.garrison_capacity:
            raise ValueError(
                f"Garrison would exceed capacity: {self.garrison_size} + {soldiers} > {self.garrison_capacity}"
            )
        self.garrison_size += soldiers
        self.mark_updated()
    
    def remove_garrison(self, soldiers: int) -> None:
        """Remove soldiers from garrison."""
        if soldiers > self.garrison_size:
            raise ValueError(
                f"Cannot remove {soldiers} soldiers from garrison of {self.garrison_size}"
            )
        self.garrison_size -= soldiers
        self.mark_updated()
    
    def add_food(self, amount: int) -> None:
        """Add food to storage."""
        self.food_stored += amount
        self.mark_updated()
    
    def consume_food(self, amount: int) -> bool:
        """
        Consume food from storage.
        
        Returns:
            True if successful, False if insufficient food
        """
        if amount > self.food_stored:
            return False
        self.food_stored -= amount
        self.mark_updated()
        return True
    
    def get_garrison_free_space(self) -> int:
        """Get remaining garrison capacity."""
        return self.garrison_capacity - self.garrison_size


@dataclass
class Border(GameEntity):
    """
    Represents a border between two provinces.
    
    Can be defensive (harder to cross) or open (easy travel).
    """
    
    province_a_id: int = 0
    province_b_id: int = 0
    is_defensive: bool = False  # True = fortified border, harder to cross
    is_open: bool = True  # False = closed border, can't cross
    

@dataclass
class Location(GameEntity):
    """
    Specific location within a province (fortress, town, etc.).
    
    Used for more detailed tactical positioning.
    """
    
    province_id: int = 0
    name: str = ""
    location_type: str = ""  # "fortress", "town", "crossroads", etc.
    x_coord: float = 0.0
    y_coord: float = 0.0

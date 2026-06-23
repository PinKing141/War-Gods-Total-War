"""
Logistics domain models.

Models for resources, projects, and supply chains.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from warfare_simulation.core.base import GameEntity
from warfare_simulation.core.constants import ResourceType, ProjectType


@dataclass
class Resource(GameEntity):
    """
    Represents a type of resource in the kingdom.
    
    Attributes:
        kingdom_id: Kingdom this resource belongs to
        resource_type: Type of resource
        stored: Current amount stored
        monthly_production: Amount produced per turn
        monthly_consumption: Amount consumed per turn
        max_storage: Maximum storage capacity
    """
    
    kingdom_id: int = 0
    resource_type: ResourceType = ResourceType.FOOD
    stored: int = 0
    monthly_production: int = 0
    monthly_consumption: int = 0
    max_storage: int = 100000
    
    def get_monthly_change(self) -> int:
        """Get net change per month (production - consumption)."""
        return self.monthly_production - self.monthly_consumption
    
    def add_storage(self, amount: int) -> None:
        """Add to storage (clamped to max)."""
        self.stored = min(self.max_storage, self.stored + amount)
        self.mark_updated()
    
    def consume(self, amount: int) -> bool:
        """
        Consume resource.
        
        Returns:
            True if successful, False if insufficient
        """
        if amount > self.stored:
            return False
        self.stored -= amount
        self.mark_updated()
        return True
    
    def produce(self, amount: int) -> None:
        """Produce resource."""
        self.add_storage(amount)
    
    def advance_turn(self) -> None:
        """Advance resource by one turn (production - consumption)."""
        net_change = self.get_monthly_change()
        if net_change > 0:
            self.add_storage(net_change)
        else:
            # Try to consume; if not enough, take what's available
            self.consume(min(abs(net_change), self.stored))
        self.mark_updated()


@dataclass
class Project(GameEntity):
    """
    Represents a construction/development project.
    
    Attributes:
        kingdom_id: Kingdom building project
        name: Project name
        project_type: Type of project
        cost_silver: Total silver cost
        cost_resources: Resource requirements
        progress_percent: Completion percentage
        turns_remaining: Estimated turns to completion
        location_id: Location of project
    """
    
    kingdom_id: int = 0
    name: str = ""
    project_type: ProjectType = ProjectType.FORTIFICATION
    cost_silver: int = 0
    cost_resources: dict = field(default_factory=dict)  # {ResourceType: amount}
    progress_percent: int = 0
    turns_remaining: int = 5
    location_id: int = 0
    
    def advance_progress(self, percent: int = 10) -> None:
        """
        Advance project progress.
        
        Args:
            percent: Percentage to advance
        """
        self.progress_percent = min(100, self.progress_percent + percent)
        self.turns_remaining = max(0, self.turns_remaining - 1)
        self.mark_updated()
    
    def is_complete(self) -> bool:
        """Check if project is complete."""
        return self.progress_percent >= 100


@dataclass
class ArmyMovement(GameEntity):
    """
    Represents an army group moving through a planned route.

    The model is intentionally deterministic for the Living Chronicle logistics
    slice: callers provide weather/road modifiers, and each daily advance records
    the resulting progress, supply pressure, attrition, or contact state.
    """

    army_name: str = ""
    kingdom_id: int = 0
    unit_ids: List[int] = field(default_factory=list)
    route: List[int] = field(default_factory=list)
    current_leg_index: int = 0
    progress_on_leg: int = 0
    base_daily_progress: int = 25
    supply_days_remaining: int = 0
    shortage_level: str = "supplied"
    morale_penalty: int = 0
    attrition_taken: int = 0
    status: str = "marching"
    contact_detected: bool = False

    def current_location_id(self) -> Optional[int]:
        """Return the route node currently occupied or last reached."""
        if not self.route:
            return None
        return self.route[min(self.current_leg_index, len(self.route) - 1)]

    def destination_id(self) -> Optional[int]:
        """Return the final route destination."""
        return self.route[-1] if self.route else None

    def advance_day(
        self,
        *,
        weather_modifier: float = 1.0,
        road_modifier: float = 1.0,
        enemy_present: bool = False,
    ) -> dict:
        """Advance the army one day and return an auditable outcome."""
        if self.status in {"arrived", "turned_back", "destroyed"}:
            return {
                "status": self.status,
                "progress_gained": 0,
                "shortage_level": self.shortage_level,
            }
        if len(self.route) < 2:
            self.status = "arrived"
            return {
                "status": self.status,
                "progress_gained": 0,
                "shortage_level": self.shortage_level,
            }

        self.supply_days_remaining -= 1
        if self.supply_days_remaining >= 0:
            self.shortage_level = "supplied"
        elif self.supply_days_remaining >= -2:
            self.shortage_level = "strained"
            self.morale_penalty += 1
        elif self.supply_days_remaining >= -5:
            self.shortage_level = "hungry"
            self.morale_penalty += 2
            self.attrition_taken += 1
        else:
            self.shortage_level = "starving"
            self.morale_penalty += 4
            self.attrition_taken += 3

        if self.shortage_level == "starving" and weather_modifier < 0.75:
            self.status = "turned_back"
        else:
            progress_gained = max(
                1,
                int(self.base_daily_progress * weather_modifier * road_modifier),
            )
            self.progress_on_leg += progress_gained
            while self.progress_on_leg >= 100 and self.current_leg_index < len(self.route) - 1:
                self.progress_on_leg -= 100
                self.current_leg_index += 1
            if self.current_leg_index >= len(self.route) - 1:
                self.current_leg_index = len(self.route) - 1
                self.progress_on_leg = 100
                self.status = "arrived"
        self.contact_detected = bool(enemy_present and self.status == "marching")
        self.mark_updated()
        return {
            "status": self.status,
            "progress_gained": (
                0
                if self.status == "turned_back"
                else max(
                    1,
                    int(self.base_daily_progress * weather_modifier * road_modifier),
                )
            ),
            "shortage_level": self.shortage_level,
            "morale_penalty": self.morale_penalty,
            "attrition_taken": self.attrition_taken,
            "contact_detected": self.contact_detected,
            "current_location_id": self.current_location_id(),
            "destination_id": self.destination_id(),
        }


@dataclass
class SupplyRoute(GameEntity):
    """
    Represents a supply/trade route.
    
    Attributes:
        kingdom_id: Kingdom controlling route
        name: Route name
        from_location_id: Starting location
        to_location_id: Destination location
        resource_type: Primary resource transported
        capacity: Capacity per turn
        travel_time: Turns to traverse route
        is_active: Whether route is active
    """
    
    kingdom_id: int = 0
    name: str = ""
    from_location_id: int = 0
    to_location_id: int = 0
    resource_type: ResourceType = ResourceType.FOOD
    capacity: int = 1000
    travel_time: int = 1
    is_active: bool = True
    
    def toggle_active(self) -> None:
        """Toggle route active status."""
        self.is_active = not self.is_active
        self.mark_updated()

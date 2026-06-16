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

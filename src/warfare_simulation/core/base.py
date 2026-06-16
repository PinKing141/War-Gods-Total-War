"""
Base classes and interfaces for the campaign engine.

This module defines the core abstractions that all domains, services, and generators inherit from.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class GameEntity(ABC):
    """
    Base class for all game entities (kingdoms, units, provinces, factions, etc.).
    
    GameEntity provides:
    - ID tracking
    - Timestamp tracking (creation, last update)
    - Serialization/deserialization
    - Type hints and basic structure
    """
    
    id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary for serialization."""
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GameEntity":
        """Create entity from dictionary (override in subclasses)."""
        raise NotImplementedError(f"{cls.__name__} must implement from_dict()")
    
    def mark_updated(self) -> None:
        """Update the updated_at timestamp (call before persisting changes)."""
        self.updated_at = datetime.now()


class GameSystem(ABC):
    """
    Base class for all domain services (KingdomService, MilitaryService, etc.).
    
    GameSystem provides:
    - Standardized service interface
    - Repository injection point
    - Validation integration
    - Turn advancement hooks
    """
    
    def __init__(self, name: str):
        """
        Initialize a game system.
        
        Args:
            name: Human-readable name for logging (e.g., "Kingdom", "Military")
        """
        self.name = name
        self._initialized = False
    
    @abstractmethod
    def initialize(self) -> None:
        """
        Initialize the service (load data, set up repositories, etc.).
        Called once at application startup.
        """
        self._initialized = True
    
    @abstractmethod
    def advance_turn(self, turn_number: int) -> None:
        """
        Execute one turn of this system's logic.
        
        Args:
            turn_number: Current turn number in the campaign
        
        Raises:
            InvalidCampaignStateError: If the system state is invalid
            ResourceError: If resources are insufficient
        """
        pass
    
    @abstractmethod
    def validate_state(self) -> List[str]:
        """
        Validate the system's current state.
        
        Returns:
            List of validation error messages (empty if state is valid)
        """
        pass
    
    def is_initialized(self) -> bool:
        """Check if the system has been initialized."""
        return self._initialized


class SheetGenerator(ABC):
    """
    Base class for all spreadsheet generators (DashboardGenerator, ArmyGenerator, etc.).
    
    SheetGenerator provides:
    - Standardized generation interface
    - Shared formatting utilities
    - Style manager integration
    - Header/data row formatting
    """
    
    def __init__(self, sheet_name: str):
        """
        Initialize a sheet generator.
        
        Args:
            sheet_name: Name of the sheet to be created in the workbook
        """
        self.sheet_name = sheet_name
        self._generated = False
    
    @abstractmethod
    def generate(self) -> None:
        """
        Generate the sheet and add it to the workbook.
        Subclasses implement their specific sheet creation logic.
        """
        self._generated = True
    
    def is_generated(self) -> bool:
        """Check if the sheet has been generated."""
        return self._generated


class IValidationRule(ABC):
    """
    Interface for domain-specific validation rules.
    
    Validation rules are applied before state mutations to prevent invalid states.
    Examples: "Cannot spend more silver than available", "Cannot deploy unit to non-existent province"
    """
    
    @abstractmethod
    def validate(self) -> bool:
        """
        Execute the validation rule.
        
        Returns:
            True if validation passes
        
        Raises:
            ValidationError: If validation fails (with descriptive message)
        """
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of what this rule validates."""
        pass

"""
Geography domain service.

Orchestrates province management, population, borders, etc.
"""

from warfare_simulation.core.base import GameSystem
from warfare_simulation.core.validation import ValidationService
from warfare_simulation.core.exceptions import InvalidCampaignStateError
from warfare_simulation.core.logger import get_logger
from .models import Province
from .repository import ProvinceRepository, BorderRepository, LocationRepository


logger = get_logger(__name__)


class GeographyService(GameSystem):
    """
    Service for geography/province management.
    
    Handles province state, population, loyalty, borders, and spatial logic.
    """
    
    def __init__(
        self,
        province_repo: ProvinceRepository,
        border_repo: BorderRepository,
        location_repo: LocationRepository,
        validator: ValidationService,
    ):
        """Initialize Geography service."""
        super().__init__("Geography")
        self.province_repo = province_repo
        self.border_repo = border_repo
        self.location_repo = location_repo
        self.validator = validator
    
    def initialize(self) -> None:
        """Initialize Geography service."""
        logger.info("Geography service initialized")
        self._initialized = True
    
    def create_province(
        self,
        kingdom_id: int,
        name: str,
        population: int,
        monthly_tax: int,
        loyalty: int = 85,
    ) -> Province:
        """
        Create a new province.
        
        Args:
            kingdom_id: Kingdom this province belongs to
            name: Province name
            population: Initial population
            monthly_tax: Monthly tax income
            loyalty: Initial loyalty (0-100)
        
        Returns:
            Created province
        """
        province = Province(
            kingdom_id=kingdom_id,
            name=name,
            population=population,
            monthly_tax=monthly_tax,
            loyalty=loyalty,
        )
        
        created = self.province_repo.create(province)
        logger.info(f"Province '{name}' created in kingdom {kingdom_id}")
        return created
    
    def set_province_loyalty(self, province_id: int, loyalty: int) -> Province:
        """
        Set province loyalty.
        
        Args:
            province_id: Province to update
            loyalty: New loyalty value (0-100)
        
        Returns:
            Updated province
        """
        province = self.province_repo.get(province_id)
        if not province:
            raise InvalidCampaignStateError(f"Province {province_id} not found")
        
        # Validate
        self.validator.validate_percent_value(loyalty, "loyalty")
        
        # Update
        province.set_loyalty(loyalty)
        
        # Persist
        updated = self.province_repo.update(province)
        logger.debug(f"Province '{province.name}' loyalty set to {loyalty}")
        
        return updated
    
    def advance_province_turn(self, province_id: int) -> Province:
        """
        Advance province by one turn.
        
        Updates:
        - Population changes
        - Morale/loyalty shifts
        - Food production/consumption
        
        Args:
            province_id: Province to advance
        
        Returns:
            Updated province
        """
        province = self.province_repo.get(province_id)
        if not province:
            raise InvalidCampaignStateError(f"Province {province_id} not found")
        
        # Validate before mutation
        errors = self.validator.validate_province_state(province)
        if errors:
            logger.warning(f"Province validation errors: {errors}")
        
        # Apply loyalty changes (simplified)
        # In full implementation, would include population growth, unrest, etc.
        
        province.mark_updated()
        
        # Persist
        updated = self.province_repo.update(province)
        logger.debug(f"Province '{updated.name}' turn advanced")
        
        return updated
    
    def advance_turn(self, turn_number: int) -> None:
        """
        Execute geography systems for this turn.
        
        Args:
            turn_number: Current campaign turn
        """
        for province in self.province_repo.list_all():
            self.advance_province_turn(province.id)
    
    def validate_state(self) -> list:
        """
        Validate all provinces.
        
        Returns:
            List of validation error messages
        """
        errors = []
        for province in self.province_repo.list_all():
            errors.extend(self.validator.validate_province_state(province))
        return errors

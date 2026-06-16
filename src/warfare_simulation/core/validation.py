"""
Cross-domain validation service.

ValidationService implements Tier 2 validation (runtime validation before mutations).
It provides centralized rules that prevent invalid state across all domains.

The three-tier validation strategy:
1. Schema validation (load-time): Pydantic validates JSON structure
2. Service validation (runtime): ValidationService checks invariants before mutations
3. Orchestration validation (turn-time): CampaignOrchestrator validates entire state
"""

from typing import List, Optional, Any
from .exceptions import ResourceError, InvalidCampaignStateError, ValidationError
from .logger import get_logger


logger = get_logger(__name__)


class ValidationService:
    """
    Centralized validation service for all domains.
    
    This service enforces cross-domain rules to prevent invalid campaign states.
    All domain services should use this before mutating state.
    
    Usage example:
        validator = ValidationService()
        
        # Before kingdom spends silver:
        validator.validate_silver_transaction(kingdom, amount)
        
        # Before deploying unit:
        validator.validate_unit_deployment(unit, location)
    """
    
    def __init__(self):
        """Initialize the validation service."""
        self._validation_rules: List[callable] = []
    
    # ========================================================================
    # KINGDOM VALIDATIONS
    # ========================================================================
    
    def validate_kingdom_state(self, kingdom: Any) -> List[str]:
        """
        Validate the overall state of a kingdom.
        
        Args:
            kingdom: Kingdom entity to validate
        
        Returns:
            List of error messages (empty if valid)
        
        Rules:
        - Population must be >= 1000 (minimum civilization size)
        - Treasury must be >= 0 (cannot have negative silver)
        - Monthly income must be >= 0
        - Monthly expenses must be >= 0
        """
        errors = []
        
        if hasattr(kingdom, 'population') and kingdom.population < 1000:
            errors.append(f"Kingdom population ({kingdom.population}) below minimum (1000)")
        
        if hasattr(kingdom, 'treasury_silver') and kingdom.treasury_silver < 0:
            errors.append(f"Kingdom treasury negative: {kingdom.treasury_silver}")
        
        if hasattr(kingdom, 'monthly_income') and kingdom.monthly_income < 0:
            errors.append(f"Monthly income cannot be negative: {kingdom.monthly_income}")
        
        if hasattr(kingdom, 'monthly_expenses') and kingdom.monthly_expenses < 0:
            errors.append(f"Monthly expenses cannot be negative: {kingdom.monthly_expenses}")
        
        return errors
    
    def validate_resource_transaction(self, source: Any, target: Any, amount: int) -> bool:
        """
        Validate a resource transfer between entities.
        
        For silver transfers, delegates to validate_silver_transaction on source.
        """
        if hasattr(source, "treasury_silver"):
            self.validate_silver_transaction(source, amount)
        return True
    
    def validate_silver_transaction(
        self,
        kingdom: Any,
        amount: int,
        transaction_type: str = "spend",
    ) -> bool:
        """
        Validate a silver transaction (income or expense).
        
        Args:
            kingdom: Kingdom entity performing the transaction
            amount: Amount of silver to transaction
            transaction_type: "spend", "gain", or "refund"
        
        Returns:
            True if valid
        
        Raises:
            ResourceError: If transaction would create invalid state
            ValidationError: If inputs are invalid
        
        Rules:
        - Cannot spend more silver than available
        - Cannot transact negative amounts
        - Transaction amount must be integer
        """
        if not isinstance(amount, int):
            raise ValidationError(f"Transaction amount must be integer, got {type(amount)}")
        
        if amount < 0:
            raise ValidationError(f"Transaction amount cannot be negative: {amount}")
        
        if transaction_type == "spend":
            if amount > kingdom.treasury_silver:
                raise ResourceError(
                    f"Kingdom cannot spend {amount} silver; "
                    f"only has {kingdom.treasury_silver}"
                )
        
        logger.debug(
            f"Silver transaction validated: {transaction_type} {amount} "
            f"(balance: {kingdom.treasury_silver})"
        )
        return True
    
    # ========================================================================
    # MILITARY VALIDATIONS
    # ========================================================================
    
    def validate_unit_deployment(
        self,
        unit: Any,
        location: Any,
    ) -> bool:
        """
        Validate unit deployment to a location.
        
        Args:
            unit: Unit entity being deployed
            location: Location (province) entity
        
        Returns:
            True if valid
        
        Raises:
            InvalidCampaignStateError: If deployment is invalid
            ValidationError: If entities are incomplete
        
        Rules:
        - Unit must exist
        - Location must exist
        - Location must have space for unit
        - Location must be accessible
        """
        if not hasattr(unit, 'soldiers'):
            raise ValidationError("Unit missing soldiers attribute")
        
        if not hasattr(location, 'garrison_capacity'):
            raise ValidationError("Location missing garrison_capacity attribute")
        
        if unit.soldiers > location.garrison_capacity:
            raise InvalidCampaignStateError(
                f"Location {location.name} (capacity {location.garrison_capacity}) "
                f"cannot garrison unit {unit.name} ({unit.soldiers} soldiers)"
            )
        
        logger.debug(
            f"Unit deployment validated: {unit.name} "
            f"({unit.soldiers} soldiers) → {location.name}"
        )
        return True
    
    def validate_unit_morale(self, unit: Any) -> bool:
        """
        Validate unit morale is within valid range.
        
        Args:
            unit: Unit entity to check
        
        Returns:
            True if valid
        
        Raises:
            InvalidCampaignStateError: If morale is out of range
        
        Rules:
        - Morale must be 0-100
        """
        if not hasattr(unit, 'morale'):
            raise ValidationError("Unit missing morale attribute")
        
        if unit.morale < 0 or unit.morale > 100:
            raise InvalidCampaignStateError(
                f"Unit morale out of range: {unit.morale} (must be 0-100)"
            )
        
        return True
    
    # ========================================================================
    # GEOGRAPHY VALIDATIONS
    # ========================================================================
    
    def validate_province_state(self, province: Any) -> List[str]:
        """
        Validate the overall state of a province.
        
        Args:
            province: Province entity to validate
        
        Returns:
            List of error messages (empty if valid)
        
        Rules:
        - Population >= 0
        - Food stores >= 0
        - Loyalty 0-100
        - Fort level 0-5
        """
        errors = []
        
        if hasattr(province, 'population') and province.population < 0:
            errors.append(f"Province {province.name} has negative population")
        
        if hasattr(province, 'food_stored') and province.food_stored < 0:
            errors.append(f"Province {province.name} has negative food stores")
        
        if hasattr(province, 'loyalty'):
            if province.loyalty < 0 or province.loyalty > 100:
                errors.append(
                    f"Province {province.name} loyalty out of range: {province.loyalty}"
                )
        
        if hasattr(province, 'fort_level'):
            if province.fort_level < 0 or province.fort_level > 5:
                errors.append(
                    f"Province {province.name} fort level out of range: {province.fort_level}"
                )
        
        return errors
    
    # ========================================================================
    # DIPLOMACY VALIDATIONS
    # ========================================================================
    
    def validate_faction_opinion(
        self,
        faction_a: Any,
        faction_b: Any,
        opinion_delta: int,
    ) -> bool:
        """
        Validate a change in faction opinion.
        
        Args:
            faction_a: First faction
            faction_b: Second faction
            opinion_delta: Change in opinion (-100 to +100)
        
        Returns:
            True if valid
        
        Raises:
            ValidationError: If input is invalid
        
        Rules:
        - Cannot change opinion of same faction
        - Opinion delta must be -100 to +100
        - Resulting opinion must be -100 to +100
        """
        if faction_a.id == faction_b.id:
            raise ValidationError("Cannot change opinion of same faction")
        
        if not -100 <= opinion_delta <= 100:
            raise ValidationError(
                f"Opinion delta must be -100 to +100, got {opinion_delta}"
            )
        
        new_opinion = getattr(faction_a, 'opinion_of_b', 0) + opinion_delta
        if not -100 <= new_opinion <= 100:
            raise InvalidCampaignStateError(
                f"Opinion change would result in {new_opinion} "
                f"(must be -100 to +100)"
            )
        
        return True
    
    # ========================================================================
    # RESOURCE VALIDATIONS
    # ========================================================================
    
    def validate_resource_production(
        self,
        production: int,
        consumption: int,
    ) -> bool:
        """
        Validate resource production/consumption levels.
        
        Args:
            production: Resource units produced per turn
            consumption: Resource units consumed per turn
        
        Returns:
            True if valid (regardless of surplus/deficit)
        
        Raises:
            ValidationError: If values are invalid
        
        Rules:
        - Both must be non-negative integers
        """
        if not isinstance(production, int) or production < 0:
            raise ValidationError(f"Production must be non-negative integer, got {production}")
        
        if not isinstance(consumption, int) or consumption < 0:
            raise ValidationError(f"Consumption must be non-negative integer, got {consumption}")
        
        return True
    
    # ========================================================================
    # GENERAL VALIDATIONS
    # ========================================================================
    
    def validate_percent_value(self, value: int, name: str = "value") -> bool:
        """
        Validate a percentage value (0-100).
        
        Args:
            value: Value to check
            name: Name for error message
        
        Returns:
            True if valid
        
        Raises:
            ValidationError: If value is outside 0-100 range
        """
        if not isinstance(value, int):
            raise ValidationError(f"{name} must be integer, got {type(value)}")
        
        if value < 0 or value > 100:
            raise ValidationError(f"{name} must be 0-100, got {value}")
        
        return True
    
    def validate_positive_int(self, value: int, name: str = "value") -> bool:
        """
        Validate a positive integer value.
        
        Args:
            value: Value to check
            name: Name for error message
        
        Returns:
            True if valid
        
        Raises:
            ValidationError: If value is not a positive integer
        """
        if not isinstance(value, int):
            raise ValidationError(f"{name} must be integer, got {type(value)}")
        
        if value <= 0:
            raise ValidationError(f"{name} must be positive, got {value}")
        
        return True
    
    def validate_non_negative_int(self, value: int, name: str = "value") -> bool:
        """
        Validate a non-negative integer value.
        
        Args:
            value: Value to check
            name: Name for error message
        
        Returns:
            True if valid
        
        Raises:
            ValidationError: If value is not a non-negative integer
        """
        if not isinstance(value, int):
            raise ValidationError(f"{name} must be integer, got {type(value)}")
        
        if value < 0:
            raise ValidationError(f"{name} must be non-negative, got {value}")
        
        return True

"""
Kingdom domain service.

Orchestrates kingdom business logic and turn advancement.
"""

from warfare_simulation.core.base import GameSystem
from warfare_simulation.core.validation import ValidationService
from warfare_simulation.core.exceptions import InvalidCampaignStateError, ResourceError
from warfare_simulation.core.logger import get_logger
from .models import Kingdom, Treasury
from .repository import KingdomRepository, TreasuryRepository


logger = get_logger(__name__)


class KingdomService(GameSystem):
    """
    Service for kingdom management and turn advancement.
    
    Coordinates kingdom state changes, validates invariants, and logs events.
    """
    
    def __init__(self, kingdom_repo: KingdomRepository, validator: ValidationService):
        """
        Initialize Kingdom service.
        
        Args:
            kingdom_repo: Kingdom repository for data access
            validator: Validation service for invariant checking
        """
        super().__init__("Kingdom")
        self.kingdom_repo = kingdom_repo
        self.validator = validator
    
    def initialize(self) -> None:
        """Initialize the Kingdom service."""
        logger.info("Kingdom service initialized")
        self._initialized = True
    
    def create_kingdom(
        self,
        name: str,
        ruler_name: str,
        initial_population: int = 450000,
        initial_treasury: int = 500000,
        monthly_income: int = 18500,
        monthly_expenses: int = 12800,
    ) -> Kingdom:
        """
        Create a new kingdom.
        
        Args:
            name: Kingdom name
            ruler_name: Ruler name
            initial_population: Starting population
            initial_treasury: Starting silver
            monthly_income: Monthly income
            monthly_expenses: Monthly expenses
        
        Returns:
            Created kingdom
        """
        kingdom = Kingdom(
            name=name,
            ruler_name=ruler_name,
            population=initial_population,
            treasury_silver=initial_treasury,
            monthly_income=monthly_income,
            monthly_expenses=monthly_expenses,
            morale=85,
            loyalty=85,
            grain_stores=12,
        )
        
        created = self.kingdom_repo.create(kingdom)
        logger.info(f"Kingdom '{name}' created with treasury {initial_treasury}")
        return created
    
    def advance_kingdom_turn(self, kingdom_id: int) -> Kingdom:
        """
        Advance a kingdom by one turn.
        
        Updates:
        - Treasury (income/expenses)
        - Turn counter
        - Month/year
        
        Args:
            kingdom_id: Kingdom to advance
        
        Returns:
            Updated kingdom
        
        Raises:
            InvalidCampaignStateError: If kingdom is invalid
        """
        kingdom = self.kingdom_repo.get(kingdom_id)
        if not kingdom:
            raise InvalidCampaignStateError(f"Kingdom {kingdom_id} not found")
        
        # Validate before mutation
        errors = self.validator.validate_kingdom_state(kingdom)
        if errors:
            logger.warning(f"Kingdom validation errors: {errors}")
        
        # Advance
        kingdom.advance_turn()
        
        # Persist
        updated = self.kingdom_repo.update(kingdom)
        logger.debug(
            f"Kingdom turn advanced: turn={updated.current_turn}, "
            f"treasury={updated.treasury_silver}"
        )
        
        return updated
    
    def spend_silver(self, kingdom_id: int, amount: int, reason: str = "") -> Kingdom:
        """
        Spend silver from kingdom treasury.
        
        Args:
            kingdom_id: Kingdom spending
            amount: Amount to spend
            reason: Reason for spending (logging)
        
        Returns:
            Updated kingdom
        
        Raises:
            ResourceError: If insufficient silver
        """
        kingdom = self.kingdom_repo.get(kingdom_id)
        if not kingdom:
            raise InvalidCampaignStateError(f"Kingdom {kingdom_id} not found")
        
        # Validate transaction
        self.validator.validate_silver_transaction(kingdom, amount, "spend")
        
        # Spend
        kingdom.spend_silver(amount)
        
        # Persist
        updated = self.kingdom_repo.update(kingdom)
        logger.info(f"Kingdom spent {amount} silver. Reason: {reason}. Balance: {updated.treasury_silver}")
        
        return updated
    
    def gain_silver(self, kingdom_id: int, amount: int, reason: str = "") -> Kingdom:
        """
        Add silver to kingdom treasury.
        
        Args:
            kingdom_id: Kingdom gaining silver
            amount: Amount to gain
            reason: Reason for gain (logging)
        
        Returns:
            Updated kingdom
        """
        kingdom = self.kingdom_repo.get(kingdom_id)
        if not kingdom:
            raise InvalidCampaignStateError(f"Kingdom {kingdom_id} not found")
        
        # Validate
        self.validator.validate_non_negative_int(amount, "silver amount")
        
        # Gain
        kingdom.gain_silver(amount)
        
        # Persist
        updated = self.kingdom_repo.update(kingdom)
        logger.info(f"Kingdom gained {amount} silver. Reason: {reason}. Balance: {updated.treasury_silver}")
        
        return updated
    
    def set_morale(self, kingdom_id: int, morale: int) -> Kingdom:
        """
        Set kingdom morale.
        
        Args:
            kingdom_id: Kingdom to update
            morale: New morale value (0-100)
        
        Returns:
            Updated kingdom
        """
        kingdom = self.kingdom_repo.get(kingdom_id)
        if not kingdom:
            raise InvalidCampaignStateError(f"Kingdom {kingdom_id} not found")
        
        # Validate
        self.validator.validate_percent_value(morale, "morale")
        
        # Update
        kingdom.set_morale(morale)
        
        # Persist
        updated = self.kingdom_repo.update(kingdom)
        logger.info(f"Kingdom morale set to {morale}")
        
        return updated
    
    def set_loyalty(self, kingdom_id: int, loyalty: int) -> Kingdom:
        """
        Set noble loyalty.
        
        Args:
            kingdom_id: Kingdom to update
            loyalty: New loyalty value (0-100)
        
        Returns:
            Updated kingdom
        """
        kingdom = self.kingdom_repo.get(kingdom_id)
        if not kingdom:
            raise InvalidCampaignStateError(f"Kingdom {kingdom_id} not found")
        
        # Validate
        self.validator.validate_percent_value(loyalty, "loyalty")
        
        # Update
        kingdom.set_loyalty(loyalty)
        
        # Persist
        updated = self.kingdom_repo.update(kingdom)
        logger.info(f"Kingdom loyalty set to {loyalty}")
        
        return updated
    
    def advance_turn(self, turn_number: int) -> None:
        """
        Execute kingdom systems for this turn.
        
        Args:
            turn_number: Current campaign turn
        """
        kingdom = self.kingdom_repo.get_current_kingdom()
        if kingdom:
            self.advance_kingdom_turn(kingdom.id)
    
    def validate_state(self) -> list:
        """
        Validate all kingdom states.
        
        Returns:
            List of validation error messages
        """
        errors = []
        for kingdom in self.kingdom_repo.list_all():
            errors.extend(self.validator.validate_kingdom_state(kingdom))
        return errors

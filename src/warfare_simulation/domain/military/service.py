"""
Military domain service.

Orchestrates military operations, unit management, and commander actions.
"""

from warfare_simulation.core.base import GameSystem
from warfare_simulation.core.validation import ValidationService
from warfare_simulation.core.exceptions import InvalidCampaignStateError, ResourceError
from warfare_simulation.core.logger import get_logger
from warfare_simulation.core.constants import UnitType, ArmorType, CommanderRole, UnitStatus
from .models import Unit, Commander
from .repository import UnitRepository, CommanderRepository, GarrisonRepository


logger = get_logger(__name__)


class MilitaryService(GameSystem):
    """
    Service for military management.
    
    Handles unit creation, morale, fatigue, and commander operations.
    """
    
    def __init__(
        self,
        unit_repo: UnitRepository,
        commander_repo: CommanderRepository,
        garrison_repo: GarrisonRepository,
        validator: ValidationService,
    ):
        """Initialize Military service."""
        super().__init__("Military")
        self.unit_repo = unit_repo
        self.commander_repo = commander_repo
        self.garrison_repo = garrison_repo
        self.validator = validator
    
    def initialize(self) -> None:
        """Initialize Military service."""
        logger.info("Military service initialized")
        self._initialized = True
    
    def create_unit(
        self,
        kingdom_id: int,
        name: str,
        unit_type: UnitType,
        soldiers: int,
        armor: ArmorType = ArmorType.BRIGANDINE,
        location_id: int = 1,
    ) -> Unit:
        """
        Create a new military unit.
        
        Args:
            kingdom_id: Kingdom raising this unit
            name: Unit name
            unit_type: Type of unit
            soldiers: Number of soldiers
            armor: Armor type
            location_id: Starting location
        
        Returns:
            Created unit
        """
        # Validate
        self.validator.validate_positive_int(soldiers, "soldiers")
        
        unit = Unit(
            kingdom_id=kingdom_id,
            name=name,
            unit_type=unit_type,
            soldiers=soldiers,
            veterans=0,
            armor=armor,
            location_id=location_id,
            status=UnitStatus.ACTIVE,
        )
        
        created = self.unit_repo.create(unit)
        logger.info(f"Unit '{name}' created: {soldiers} soldiers")
        return created
    
    def create_commander(
        self,
        kingdom_id: int,
        name: str,
        role: CommanderRole,
        leadership: int = 50,
        tactics: int = 50,
        logistics: int = 50,
    ) -> Commander:
        """
        Create a new commander.
        
        Args:
            kingdom_id: Kingdom employing this commander
            name: Commander name
            role: Position held
            leadership: Leadership skill
            tactics: Tactical skill
            logistics: Logistics skill
        
        Returns:
            Created commander
        """
        # Validate skills
        self.validator.validate_percent_value(leadership, "leadership")
        self.validator.validate_percent_value(tactics, "tactics")
        self.validator.validate_percent_value(logistics, "logistics")
        
        commander = Commander(
            kingdom_id=kingdom_id,
            name=name,
            role=role,
            leadership=leadership,
            tactics=tactics,
            logistics=logistics,
        )
        
        created = self.commander_repo.create(commander)
        logger.info(f"Commander '{name}' created with role {role.value}")
        return created
    
    def set_unit_morale(self, unit_id: int, morale: int) -> Unit:
        """
        Set unit morale.
        
        Args:
            unit_id: Unit to update
            morale: New morale value (0-100)
        
        Returns:
            Updated unit
        """
        unit = self.unit_repo.get(unit_id)
        if not unit:
            raise InvalidCampaignStateError(f"Unit {unit_id} not found")
        
        # Validate
        self.validator.validate_percent_value(morale, "morale")
        
        # Update
        unit.set_morale(morale)
        
        # Persist
        updated = self.unit_repo.update(unit)
        logger.debug(f"Unit '{unit.name}' morale set to {morale}")
        
        return updated
    
    def update_all_units(self) -> None:
        """
        Update all units (morale, fatigue decay, etc).
        
        Called once per turn for all units.
        """
        for unit in self.unit_repo.list_all():
            # Morale adjusts based on fatigue
            morale_penalty = unit.fatigue // 10
            new_morale = max(0, unit.morale - morale_penalty)
            unit.set_morale(new_morale)
            
            # Fatigue decays slightly (rest)
            unit.reduce_fatigue(5)
            
            self.unit_repo.update(unit)
            logger.debug(f"Unit '{unit.name}' updated: morale={new_morale}, fatigue={unit.fatigue}")
    
    def apply_casualties(
        self, unit_id: int, regular_casualties: int, veteran_casualties: int
    ) -> Unit:
        """
        Apply casualties to a unit.
        
        Args:
            unit_id: Unit taking casualties
            regular_casualties: Regular soldier losses
            veteran_casualties: Veteran soldier losses
        
        Returns:
            Updated unit
        """
        unit = self.unit_repo.get(unit_id)
        if not unit:
            raise InvalidCampaignStateError(f"Unit {unit_id} not found")
        
        unit.take_casualties(regular_casualties, veteran_casualties)
        
        updated = self.unit_repo.update(unit)
        logger.info(
            f"Unit '{unit.name}' suffered casualties: "
            f"{regular_casualties} regulars, {veteran_casualties} veterans"
        )
        
        return updated
    
    def advance_turn(self, turn_number: int) -> None:
        """
        Execute military systems for this turn.
        
        Args:
            turn_number: Current campaign turn
        """
        self.update_all_units()
    
    def validate_state(self) -> list:
        """
        Validate all military state.
        
        Returns:
            List of validation error messages
        """
        errors = []
        for unit in self.unit_repo.list_all():
            try:
                self.validator.validate_unit_morale(unit)
            except Exception as e:
                errors.append(str(e))
        return errors

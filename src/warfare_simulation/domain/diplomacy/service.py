"""
Diplomacy domain service.

Orchestrates diplomatic relations, factions, spies, and missions.
"""

from warfare_simulation.core.base import GameSystem
from warfare_simulation.core.validation import ValidationService
from warfare_simulation.core.exceptions import InvalidCampaignStateError
from warfare_simulation.core.logger import get_logger
from warfare_simulation.core.constants import FactionStatus
from .models import Faction, Relation, Spy, Mission
from .repository import FactionRepository, RelationRepository, SpyRepository, MissionRepository


logger = get_logger(__name__)


class DiplomacyService(GameSystem):
    """
    Service for diplomacy, factions, and espionage.
    
    Manages diplomatic relations, spy networks, and mission execution.
    """
    
    def __init__(
        self,
        faction_repo: FactionRepository,
        relation_repo: RelationRepository,
        spy_repo: SpyRepository,
        mission_repo: MissionRepository,
        validator: ValidationService,
    ):
        """Initialize Diplomacy service."""
        super().__init__("Diplomacy")
        self.faction_repo = faction_repo
        self.relation_repo = relation_repo
        self.spy_repo = spy_repo
        self.mission_repo = mission_repo
        self.validator = validator
    
    def initialize(self) -> None:
        """Initialize Diplomacy service."""
        logger.info("Diplomacy service initialized")
        self._initialized = True
    
    def create_faction(
        self,
        name: str,
        faction_type: str = "nation",
        power_level: int = 50,
        wealth: int = 50,
    ) -> Faction:
        """
        Create a new faction.
        
        Args:
            name: Faction name
            faction_type: Type of faction
            power_level: Military power
            wealth: Economic power
        
        Returns:
            Created faction
        """
        faction = Faction(
            name=name,
            faction_type=faction_type,
            power_level=power_level,
            wealth=wealth,
        )
        
        created = self.faction_repo.create(faction)
        logger.info(f"Faction '{name}' created (type: {faction_type})")
        return created
    
    def establish_relation(
        self,
        faction_a_id: int,
        faction_b_id: int,
        initial_opinion: int = 0,
    ) -> Relation:
        """
        Establish a diplomatic relation between two factions.
        
        Args:
            faction_a_id: First faction
            faction_b_id: Second faction
            initial_opinion: Starting opinion (-100 to +100)
        
        Returns:
            Created relation
        """
        # Validate factions exist
        if not self.faction_repo.get(faction_a_id):
            raise InvalidCampaignStateError(f"Faction {faction_a_id} not found")
        if not self.faction_repo.get(faction_b_id):
            raise InvalidCampaignStateError(f"Faction {faction_b_id} not found")
        
        # Validate opinion (-100 to +100)
        if not -100 <= initial_opinion <= 100:
            raise InvalidCampaignStateError(f"Opinion must be -100 to +100, got {initial_opinion}")
        
        relation = Relation(
            faction_a_id=faction_a_id,
            faction_b_id=faction_b_id,
            opinion=initial_opinion,
        )
        
        created = self.relation_repo.create(relation)
        logger.info(f"Relation established between {faction_a_id} and {faction_b_id}")
        return created
    
    def shift_opinion(
        self, faction_a_id: int, faction_b_id: int, delta: int
    ) -> Relation:
        """
        Shift opinion between factions.
        
        Args:
            faction_a_id: First faction
            faction_b_id: Second faction
            delta: Change in opinion
        
        Returns:
            Updated relation
        """
        relation = self.relation_repo.get_between(faction_a_id, faction_b_id)
        if not relation:
            raise InvalidCampaignStateError(
                f"No relation between {faction_a_id} and {faction_b_id}"
            )
        
        relation.shift_opinion(delta)
        updated = self.relation_repo.update(relation)
        
        logger.debug(f"Opinion shifted by {delta}: now {updated.opinion}")
        return updated
    
    def recruit_spy(
        self,
        kingdom_id: int,
        codename: str,
        target_faction_id: int,
        skill_level: int = 50,
    ) -> Spy:
        """
        Recruit a new spy.
        
        Args:
            kingdom_id: Kingdom recruiting spy
            codename: Spy codename
            target_faction_id: Faction being spied on
            skill_level: Spy skill
        
        Returns:
            Created spy
        """
        # Validate skill
        self.validator.validate_percent_value(skill_level, "skill_level")
        
        spy = Spy(
            kingdom_id=kingdom_id,
            codename=codename,
            target_faction_id=target_faction_id,
            skill_level=skill_level,
        )
        
        created = self.spy_repo.create(spy)
        logger.info(f"Spy '{codename}' recruited (skill: {skill_level})")
        return created
    
    def process_diplomatic_events(self) -> None:
        """
        Process all diplomatic events for this turn.
        
        Updates:
        - Mission progress
        - Spy risks
        - Opinion shifts
        """
        # Advance all active missions
        for mission in self.mission_repo.get_active():
            mission.advance_turn()
            self.mission_repo.update(mission)
            logger.debug(f"Mission in faction {mission.target_faction_id} advanced")
        
        # Increase spy discovery risk
        for spy in self.spy_repo.list_all():
            if spy.status == "Active":
                spy.increase_risk(2)  # 2% per turn
                self.spy_repo.update(spy)
    
    def advance_turn(self, turn_number: int) -> None:
        """
        Execute diplomacy systems for this turn.
        
        Args:
            turn_number: Current campaign turn
        """
        self.process_diplomatic_events()
    
    def validate_state(self) -> list:
        """
        Validate all diplomatic state.
        
        Returns:
            List of validation error messages
        """
        errors = []
        # Add diplomacy-specific validation as needed
        return errors

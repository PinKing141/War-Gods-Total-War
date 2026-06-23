"""
Military domain service.

Orchestrates military operations, unit management, and commander actions.
"""

from warfare_simulation.core.base import GameSystem
from warfare_simulation.core.validation import ValidationService
from warfare_simulation.core.exceptions import InvalidCampaignStateError, ResourceError
from warfare_simulation.core.logger import get_logger
from warfare_simulation.core.constants import UnitType, ArmorType, CommanderRole, UnitStatus
from .models import Unit, Commander, BattleReport
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

    def resolve_battle(
        self,
        attacker_unit_id: int,
        defender_unit_id: int,
        *,
        location_id: int | None = None,
        fortification_bonus: int = 0,
    ) -> BattleReport:
        """Resolve one deterministic field battle and return an auditable report.

        Combat power combines headcount, veteran quality, morale, fatigue, armor,
        unit role, commander skill, and optional defensive works. The method
        mutates both units with casualties, morale shifts, fatigue shifts, and
        retreat status before producing a chronicle-ready report.
        """
        attacker = self.unit_repo.get(attacker_unit_id)
        defender = self.unit_repo.get(defender_unit_id)
        if not attacker:
            raise InvalidCampaignStateError(f"Attacker unit {attacker_unit_id} not found")
        if not defender:
            raise InvalidCampaignStateError(f"Defender unit {defender_unit_id} not found")
        if attacker.kingdom_id == defender.kingdom_id:
            raise InvalidCampaignStateError("Battle requires opposing kingdoms")

        battle_location_id = location_id or attacker.location_id or defender.location_id
        attacker_commander = (
            self.commander_repo.get(attacker.commander_id) if attacker.commander_id else None
        )
        defender_commander = (
            self.commander_repo.get(defender.commander_id) if defender.commander_id else None
        )
        attacker_power = self._combat_power(attacker, attacker_commander)
        defender_power = self._combat_power(defender, defender_commander) + max(
            0, fortification_bonus
        )

        if attacker_power > defender_power:
            winner, loser, retreating_side = "attacker", defender, "defender"
            power_margin = attacker_power - defender_power
        elif defender_power > attacker_power:
            winner, loser, retreating_side = "defender", attacker, "attacker"
            power_margin = defender_power - attacker_power
        else:
            winner, loser, retreating_side, power_margin = "draw", None, None, 0

        attacker_casualties = self._casualties(
            attacker, defender_power, attacker_power, winner == "defender"
        )
        defender_casualties = self._casualties(
            defender, attacker_power, defender_power, winner == "attacker"
        )
        pursuit_casualties = 0
        if loser is not None and power_margin >= 40:
            pursuit_casualties = max(1, loser.get_total_strength() // 20)
            if retreating_side == "attacker":
                attacker_casualties += pursuit_casualties
            else:
                defender_casualties += pursuit_casualties

        attacker_before_morale, defender_before_morale = attacker.morale, defender.morale
        attacker_before_fatigue, defender_before_fatigue = attacker.fatigue, defender.fatigue
        attacker.take_casualties(
            attacker_casualties, min(attacker.veterans, attacker_casualties // 5)
        )
        defender.take_casualties(
            defender_casualties, min(defender.veterans, defender_casualties // 5)
        )
        self._apply_battle_condition(attacker, winner == "attacker", winner == "defender")
        self._apply_battle_condition(defender, winner == "defender", winner == "attacker")
        if retreating_side == "attacker":
            attacker.status = UnitStatus.RECOVERING
        elif retreating_side == "defender":
            defender.status = UnitStatus.RECOVERING
        if attacker.get_total_strength() == 0:
            attacker.status = UnitStatus.DEPLETED
        if defender.get_total_strength() == 0:
            defender.status = UnitStatus.DEPLETED
        self.unit_repo.update(attacker)
        self.unit_repo.update(defender)

        commander_risk = self._commander_risk(
            attacker_casualties + defender_casualties,
            attacker_before_fatigue + defender_before_fatigue,
        )
        report = BattleReport(
            location_id=battle_location_id,
            attacker_unit_id=attacker.id,
            defender_unit_id=defender.id,
            attacker_commander_id=attacker.commander_id,
            defender_commander_id=defender.commander_id,
            attacker_power=attacker_power,
            defender_power=defender_power,
            attacker_casualties=attacker_casualties,
            defender_casualties=defender_casualties,
            attacker_morale_shift=attacker.morale - attacker_before_morale,
            defender_morale_shift=defender.morale - defender_before_morale,
            attacker_fatigue_shift=attacker.fatigue - attacker_before_fatigue,
            defender_fatigue_shift=defender.fatigue - defender_before_fatigue,
            winner=winner,
            retreating_side=retreating_side,
            pursuit_casualties=pursuit_casualties,
            commander_risk=commander_risk,
        )
        report.battle_log = [
            f"Battle at location {battle_location_id}: attacker power {attacker_power}, defender power {defender_power}.",
            f"Casualties: attacker {attacker_casualties}, defender {defender_casualties}.",
            f"Outcome: {winner}; retreating side: {retreating_side or 'none'}; commander risk: {commander_risk}.",
        ]
        report.chronicle_entry = (
            f"At location {battle_location_id}, {attacker.name} met {defender.name}; "
            f"the {winner} prevailed after {attacker_casualties + defender_casualties} losses."
        )
        return report

    def _combat_power(self, unit: Unit, commander: Commander | None) -> int:
        armor_bonus = {
            ArmorType.PLATE: 24,
            ArmorType.PLATE_MAIL: 20,
            ArmorType.MAIL: 16,
            ArmorType.BRIGANDINE: 12,
            ArmorType.GAMBESON: 8,
            ArmorType.LEATHER: 5,
            ArmorType.UNARMORED: 0,
        }[unit.armor]
        role_bonus = (
            18 if unit.unit_type in {UnitType.HEAVY_INFANTRY, UnitType.HEAVY_SPEARMEN} else 10
        )
        commander_bonus = ((commander.leadership + commander.tactics) // 4) if commander else 0
        return max(
            1,
            unit.soldiers
            + (unit.veterans * 2)
            + unit.morale
            - unit.fatigue
            + armor_bonus
            + role_bonus
            + commander_bonus,
        )

    def _casualties(self, unit: Unit, opposing_power: int, own_power: int, lost: bool) -> int:
        pressure = max(1, opposing_power - (own_power // 2))
        divisor = 7 if lost else 12
        return min(unit.get_total_strength(), max(1, pressure // divisor))

    def _apply_battle_condition(self, unit: Unit, won: bool, lost: bool) -> None:
        unit.add_fatigue(18 if lost else 10)
        morale_delta = 8 if won else (-12 if lost else -4)
        unit.set_morale(max(0, min(100, unit.morale + morale_delta)))

    def _commander_risk(self, casualties: int, fatigue_total: int) -> str:
        score = casualties + (fatigue_total // 2)
        if score >= 180:
            return "severe"
        if score >= 90:
            return "elevated"
        return "low"

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

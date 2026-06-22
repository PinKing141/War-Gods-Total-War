"""
Campaign bootstrap: seed SQLite from JSON config and hydrate domain repositories.

JSON is the immutable campaign definition; SQLite is the mutable runtime state.
On first run, configs are loaded, validated, and inserted into the database.
"""

import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional, Type, TypeVar

from warfare_simulation.config.config import ConfigManager
from warfare_simulation.core.constants import (
    ArmorType,
    CommanderRole,
    EventCategory,
    FactionStatus,
    ResourceType,
    EventCategory,
    UnitStatus,
    UnitType,
)
from warfare_simulation.core.logger import get_logger
from warfare_simulation.domain.diplomacy.models import Faction, Relation
from warfare_simulation.domain.diplomacy.repository import FactionRepository, RelationRepository
from warfare_simulation.domain.events.models import AuditLog, Event, ObserverLog, TurnSummary
from warfare_simulation.domain.events.repository import AuditLogRepository, EventRepository, ObserverLogRepository, TurnSummaryRepository
from warfare_simulation.domain.geography.models import Province
from warfare_simulation.domain.geography.repository import ProvinceRepository
from warfare_simulation.domain.kingdom.models import Kingdom
from warfare_simulation.domain.kingdom.repository import KingdomRepository
from warfare_simulation.domain.logistics.models import Resource
from warfare_simulation.domain.logistics.repository import ResourceRepository
from warfare_simulation.domain.military.models import Commander, Unit
from warfare_simulation.domain.military.repository import CommanderRepository, UnitRepository
from warfare_simulation.persistence.database import DatabaseManager

logger = get_logger(__name__)

E = TypeVar("E", bound=Enum)

RESOURCE_TYPE_ALIASES = {
    "WOOD": ResourceType.TIMBER,
}


@dataclass
class CampaignRepositories:
    """Domain repositories hydrated from SQLite."""

    kingdom: KingdomRepository
    province: ProvinceRepository
    unit: UnitRepository
    commander: CommanderRepository
    faction: FactionRepository
    relation: RelationRepository
    resource: ResourceRepository
    event: EventRepository
    audit_log: AuditLogRepository
    observer_log: ObserverLogRepository
    turn_summary: TurnSummaryRepository


class CampaignBootstrap:
    """Load campaign config into SQLite and hydrate in-memory repositories."""

    @staticmethod
    def is_seeded(db: DatabaseManager, kingdom_name: Optional[str] = None) -> bool:
        """Return True if the campaign has already been seeded."""
        if not db.conn:
            db.connect()
        cursor = db.execute("SELECT COUNT(*) FROM kingdom")
        count = cursor.fetchone()[0]
        if count == 0:
            return False
        if kingdom_name is None:
            return True
        cursor = db.execute("SELECT COUNT(*) FROM kingdom WHERE name = ?", (kingdom_name,))
        return cursor.fetchone()[0] > 0

    @classmethod
    def seed_from_config(
        cls,
        config_mgr: ConfigManager,
        db: DatabaseManager,
        *,
        force: bool = False,
    ) -> int:
        """
        Load validated JSON configs into SQLite (idempotent unless force=True).

        Returns:
            kingdom_id of the seeded kingdom
        """
        if not db.conn:
            db.connect()
        db.initialize_schema()

        configs = config_mgr.load_all_configs()
        kingdom_cfg = configs["kingdom"].kingdom

        if cls.is_seeded(db, kingdom_cfg.name) and not force:
            logger.info("Campaign already seeded for %s — skipping", kingdom_cfg.name)
            cursor = db.execute("SELECT id FROM kingdom WHERE name = ?", (kingdom_cfg.name,))
            return cursor.fetchone()[0]

        if force:
            cls._clear_campaign_tables(db)

        cursor = db.execute(
            """
            INSERT INTO kingdom (
                name, ruler_name, population, treasury_silver,
                monthly_income, monthly_expenses, morale, loyalty,
                grain_stores, current_day, current_turn, current_month, current_year
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                kingdom_cfg.name,
                kingdom_cfg.ruler_name,
                kingdom_cfg.population,
                kingdom_cfg.treasury_silver,
                kingdom_cfg.monthly_income,
                kingdom_cfg.monthly_expenses,
                kingdom_cfg.morale,
                kingdom_cfg.loyalty,
                kingdom_cfg.grain_stores,
                kingdom_cfg.current_day,
                kingdom_cfg.current_turn,
                kingdom_cfg.current_month,
                kingdom_cfg.current_year,
            ),
        )
        kingdom_id = cursor.lastrowid

        for prov in configs["provinces"].provinces:
            db.execute(
                """
                INSERT INTO province (
                    kingdom_id, name, population, fort_level, food_stored,
                    monthly_tax, loyalty, garrison_size, garrison_capacity, governor_name
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    kingdom_id,
                    prov.name,
                    prov.population,
                    prov.fort_level,
                    prov.food_stored,
                    prov.monthly_tax,
                    prov.loyalty,
                    prov.garrison_size,
                    prov.garrison_capacity,
                    prov.governor_name,
                ),
            )

        for cmd in configs["commanders"].commanders:
            db.execute(
                """
                INSERT INTO commander (
                    kingdom_id, name, role, leadership, tactics, logistics,
                    loyalty, status, traits
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    kingdom_id,
                    cmd.name,
                    cmd.role,
                    cmd.leadership,
                    cmd.tactics,
                    cmd.logistics,
                    cmd.loyalty,
                    cmd.status,
                    cmd.traits,
                ),
            )

        for unit in configs["units"].units:
            db.execute(
                """
                INSERT INTO unit (
                    kingdom_id, name, unit_type, soldiers, veterans, morale,
                    fatigue, armor, location_id, commander_id, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    kingdom_id,
                    unit.name,
                    unit.unit_type,
                    unit.soldiers,
                    unit.veterans,
                    unit.morale,
                    unit.fatigue,
                    unit.armor,
                    unit.location_id,
                    None,
                    unit.status,
                ),
            )

        faction_id_map: Dict[int, int] = {}
        for config_id, faction in enumerate(configs["diplomacy"].factions, start=1):
            cursor = db.execute(
                """
                INSERT INTO faction (
                    name, faction_type, government_type, power_level, wealth, stability
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    faction.name,
                    faction.faction_type,
                    faction.government_type,
                    faction.power_level,
                    faction.wealth,
                    faction.stability,
                ),
            )
            faction_id_map[config_id] = cursor.lastrowid

        for relation in configs["diplomacy"].relations:
            db.execute(
                """
                INSERT INTO relation (
                    faction_a_id, faction_b_id, status, opinion, trust,
                    trade_agreement, military_alliance
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    faction_id_map[relation.faction_a_id],
                    faction_id_map[relation.faction_b_id],
                    relation.status,
                    relation.opinion,
                    relation.trust,
                    int(relation.trade_agreement),
                    int(relation.military_alliance),
                ),
            )

        for resource in configs["resources"].resources:
            db.execute(
                """
                INSERT INTO resource (
                    kingdom_id, resource_type, stored, monthly_production,
                    monthly_consumption, max_storage
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    kingdom_id,
                    resource.resource_type,
                    resource.stored,
                    resource.monthly_production,
                    resource.monthly_consumption,
                    resource.max_storage,
                ),
            )

        db.commit()
        logger.info("Campaign seeded into SQLite (kingdom_id=%s)", kingdom_id)
        return kingdom_id

    @classmethod
    def load_repositories(cls, db: DatabaseManager) -> CampaignRepositories:
        """Hydrate domain repositories from SQLite."""
        if not db.conn:
            db.connect()

        kingdom_repo = KingdomRepository(db)
        province_repo = ProvinceRepository(db)
        unit_repo = UnitRepository(db)
        commander_repo = CommanderRepository(db)
        faction_repo = FactionRepository(db)
        relation_repo = RelationRepository(db)
        resource_repo = ResourceRepository(db)
        event_repo = EventRepository(db)
        audit_log_repo = AuditLogRepository(db)
        observer_log_repo = ObserverLogRepository(db)
        turn_summary_repo = TurnSummaryRepository(db)

        cls._hydrate_kingdoms(db, kingdom_repo)
        cls._hydrate_provinces(db, province_repo)
        cls._hydrate_commanders(db, commander_repo)
        cls._hydrate_units(db, unit_repo)
        cls._hydrate_factions(db, faction_repo)
        cls._hydrate_relations(db, relation_repo)
        cls._hydrate_resources(db, resource_repo)
        cls._hydrate_events(db, event_repo)
        cls._hydrate_audit_logs(db, audit_log_repo)
        cls._hydrate_observer_logs(db, observer_log_repo)
        cls._hydrate_turn_summaries(db, turn_summary_repo)

        return CampaignRepositories(
            kingdom=kingdom_repo,
            province=province_repo,
            unit=unit_repo,
            commander=commander_repo,
            faction=faction_repo,
            relation=relation_repo,
            resource=resource_repo,
            event=event_repo,
            audit_log=audit_log_repo,
            observer_log=observer_log_repo,
            turn_summary=turn_summary_repo,
        )

    @classmethod
    def initialize(
        cls,
        config_mgr: ConfigManager,
        db: DatabaseManager,
        *,
        force: bool = False,
    ) -> CampaignRepositories:
        """Seed SQLite from config (if needed) and return hydrated repositories."""
        cls.seed_from_config(config_mgr, db, force=force)
        return cls.load_repositories(db)

    @staticmethod
    def _clear_campaign_tables(db: DatabaseManager) -> None:
        """Remove seeded campaign data (for tests)."""
        for table in (
            "observer_log",
            "audit_log",
            "turn_summary",
            "event",
            "resource",
            "relation",
            "unit",
            "commander",
            "province",
            "faction",
            "kingdom",
        ):
            db.execute(f"DELETE FROM {table}")
        db.commit()

    @staticmethod
    def _enum_value(enum_cls: Type[E], raw: str, aliases: Optional[Dict[str, E]] = None) -> E:
        if aliases and raw in aliases:
            return aliases[raw]
        try:
            return enum_cls[raw]
        except KeyError:
            for member in enum_cls:
                if member.value == raw:
                    return member
            raise

    @classmethod
    def _hydrate_kingdoms(cls, db: DatabaseManager, repo: KingdomRepository) -> None:
        for row in db.execute(
            """
            SELECT
                id,
                name,
                ruler_name,
                population,
                treasury_silver,
                monthly_income,
                monthly_expenses,
                morale,
                loyalty,
                grain_stores,
                current_day,
                current_turn,
                current_month,
                current_year
            FROM kingdom
            """
        ).fetchall():
            entity = Kingdom(
                id=row[0],
                name=row[1],
                ruler_name=row[2],
                population=row[3],
                treasury_silver=row[4],
                monthly_income=row[5],
                monthly_expenses=row[6],
                morale=row[7],
                loyalty=row[8],
                grain_stores=row[9],
                current_day=int(row[10]),
                current_turn=int(row[11]),
                current_month=int(row[12]),
                current_year=int(row[13]),
            )
            repo.hydrate(entity)

    @classmethod
    def _hydrate_provinces(cls, db: DatabaseManager, repo: ProvinceRepository) -> None:
        for row in db.execute(
            """
            SELECT
                id,
                kingdom_id,
                name,
                population,
                fort_level,
                food_stored,
                monthly_tax,
                loyalty,
                garrison_size,
                garrison_capacity,
                governor_name
            FROM province
            """
        ).fetchall():
            entity = Province(
                id=row[0],
                kingdom_id=row[1],
                name=row[2],
                population=row[3],
                fort_level=row[4],
                food_stored=row[5],
                monthly_tax=row[6],
                loyalty=row[7],
                garrison_size=row[8],
                garrison_capacity=row[9],
                governor_name=row[10] or "",
            )
            repo.hydrate(entity)

    @classmethod
    def _hydrate_commanders(cls, db: DatabaseManager, repo: CommanderRepository) -> None:
        for row in db.execute("SELECT * FROM commander").fetchall():
            role_raw = row[3]
            try:
                role = cls._enum_value(CommanderRole, role_raw)
            except KeyError:
                role = CommanderRole.CAPTAIN
            entity = Commander(
                id=row[0],
                kingdom_id=row[1],
                name=row[2],
                role=role,
                leadership=row[4],
                tactics=row[5],
                logistics=row[6],
                loyalty=row[7],
                status=row[8],
                traits=row[9] or "",
            )
            repo.hydrate(entity)

    @classmethod
    def _hydrate_units(cls, db: DatabaseManager, repo: UnitRepository) -> None:
        for row in db.execute("SELECT * FROM unit").fetchall():
            entity = Unit(
                id=row[0],
                kingdom_id=row[1],
                name=row[2],
                unit_type=cls._enum_value(UnitType, row[3]),
                soldiers=row[4],
                veterans=row[5],
                morale=row[6],
                fatigue=row[7],
                armor=cls._enum_value(ArmorType, row[8]),
                location_id=row[9],
                commander_id=row[10],
                status=cls._enum_value(UnitStatus, row[11]),
            )
            repo.hydrate(entity)

    @classmethod
    def _hydrate_factions(cls, db: DatabaseManager, repo: FactionRepository) -> None:
        for row in db.execute("SELECT * FROM faction").fetchall():
            entity = Faction(
                id=row[0],
                name=row[1],
                faction_type=row[2],
                government_type=row[3] or "",
                power_level=row[4],
                wealth=row[5],
                stability=row[6],
            )
            repo.hydrate(entity)

    @classmethod
    def _hydrate_relations(cls, db: DatabaseManager, repo: RelationRepository) -> None:
        for row in db.execute("SELECT * FROM relation").fetchall():
            entity = Relation(
                id=row[0],
                faction_a_id=row[1],
                faction_b_id=row[2],
                status=cls._enum_value(FactionStatus, row[3]),
                opinion=row[4],
                trust=row[5],
                trade_agreement=bool(row[6]),
                military_alliance=bool(row[7]),
            )
            repo.hydrate(entity)

    @classmethod
    def _hydrate_resources(cls, db: DatabaseManager, repo: ResourceRepository) -> None:
        for row in db.execute("SELECT * FROM resource").fetchall():
            entity = Resource(
                id=row[0],
                kingdom_id=row[1],
                resource_type=cls._enum_value(ResourceType, row[2], RESOURCE_TYPE_ALIASES),
                stored=row[3],
                monthly_production=row[4],
                monthly_consumption=row[5],
                max_storage=row[6],
            )
            repo.hydrate(entity)

    @classmethod
    def _hydrate_events(cls, db: DatabaseManager, repo: EventRepository) -> None:
        for row in db.execute("SELECT * FROM event ORDER BY turn, id").fetchall():
            affected_entities = []
            if row[5]:
                try:
                    affected_entities = json.loads(row[5])
                except (TypeError, json.JSONDecodeError):
                    affected_entities = [row[5]]

            cause_chain = []
            if len(row) > 12 and row[12]:
                try:
                    cause_chain = json.loads(row[12])
                except (TypeError, json.JSONDecodeError):
                    cause_chain = [row[12]]

            entity = Event(
                id=row[0],
                turn=row[1],
                category=cls._enum_value(EventCategory, row[2]),
                description=row[3],
                impact=row[4] or "",
                affected_entities=affected_entities,
                day=row[6] if len(row) > 6 and row[6] is not None else 1,
                month=row[7] if len(row) > 7 and row[7] is not None else 1,
                year=row[8] if len(row) > 8 and row[8] is not None else 1,
                actor=row[9] if len(row) > 9 and row[9] else "system",
                target=row[10] if len(row) > 10 and row[10] else "",
                source_system=row[11] if len(row) > 11 and row[11] else "System",
                cause_chain=cause_chain,
                effect_summary=row[13] if len(row) > 13 and row[13] else "",
            )
            repo.hydrate(entity)

    @classmethod
    def _hydrate_audit_logs(cls, db: DatabaseManager, repo: AuditLogRepository) -> None:
        for row in db.execute("SELECT * FROM audit_log").fetchall():
            entity = AuditLog(
                id=row[0],
                turn=row[1],
                month=row[2],
                year=row[3],
                actor=row[4],
                target=row[5],
                system=row[6],
                action=row[7],
                previous_value=json.loads(row[8]) if row[8] is not None else None,
                new_value=json.loads(row[9]) if row[9] is not None else None,
                reason=row[10] or "",
                source_event_id=row[11],
            )
            repo.hydrate(entity)


    @classmethod
    def _hydrate_observer_logs(cls, db: DatabaseManager, repo: ObserverLogRepository) -> None:
        for row in db.execute("SELECT * FROM observer_log").fetchall():
            entity = ObserverLog(
                id=row[0],
                turn=row[1],
                day=row[2],
                month=row[3],
                year=row[4],
                stream=row[5],
                actor=row[6],
                target=row[7],
                source_system=row[8],
                summary=row[9],
                details=json.loads(row[10] or "{}"),
                source_event_id=row[11],
                source_audit_id=row[12],
            )
            repo.hydrate(entity)


    @classmethod
    def _hydrate_turn_summaries(cls, db: DatabaseManager, repo: TurnSummaryRepository) -> None:
        for row in db.execute("SELECT * FROM turn_summary").fetchall():
            entity = TurnSummary(
                id=row[0],
                turn=row[1],
                month=row[2],
                year=row[3],
                title=row[4],
                narrative=row[5],
                event_count=row[6],
                audit_count=row[7],
                highlights=json.loads(row[8] or "[]"),
            )
            repo.hydrate(entity)

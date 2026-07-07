"""Activate CSV seed-frontier rows into the legacy runtime tables."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from warfare_simulation.core.constants import CommanderRole, FactionStatus
from warfare_simulation.core.exceptions import DatabaseError
from warfare_simulation.persistence.database import DatabaseManager


DEFAULT_SEED_FRONTIER_ID = "SEED_ROV_NE_FRONTIER"


@dataclass(frozen=True)
class SeedFrontierActivationResult:
    """Summary of seed rows linked to active runtime entities."""

    kingdom_id: int
    factions: int
    provinces: int
    relations: int
    commanders: int
    linked_claims: int
    linked_mages: int


class SeedFrontierActivation:
    """Convert the lore seed frontier into active runtime rows."""

    @classmethod
    def activate(
        cls,
        db: DatabaseManager,
        *,
        seed_id: str = DEFAULT_SEED_FRONTIER_ID,
        kingdom_id: int | None = None,
        force: bool = False,
    ) -> SeedFrontierActivationResult:
        if not db.conn:
            db.connect()
        db.initialize_schema()

        if force:
            cls.clear_activation(db)

        cls._ensure_seed_exists(db, seed_id)
        active_kingdom_id = kingdom_id or cls._ensure_runtime_kingdom(db, seed_id)

        faction_map = cls._activate_factions(db)
        province_map = cls._activate_provinces(db, active_kingdom_id, faction_map)
        relation_count = cls._activate_relations(db, faction_map)
        commander_map = cls._activate_commanders(db, active_kingdom_id, faction_map)
        linked_claims = cls._link_claims(db, faction_map, province_map)
        linked_mages = cls._link_mages(db, faction_map, commander_map)

        db.commit()
        return SeedFrontierActivationResult(
            kingdom_id=active_kingdom_id,
            factions=len(faction_map),
            provinces=len(province_map),
            relations=relation_count,
            commanders=len(commander_map),
            linked_claims=linked_claims,
            linked_mages=linked_mages,
        )

    @classmethod
    def clear_activation(cls, db: DatabaseManager) -> None:
        """Delete only runtime rows previously created from seed-frontier rows."""
        if not db.conn:
            db.connect()
        db.initialize_schema()

        db.execute(
            """
            UPDATE claim
            SET active_claimant_faction_id = NULL,
                active_target_province_id = NULL
            """
        )
        db.execute(
            """
            UPDATE mage
            SET active_character_commander_id = NULL,
                active_patron_faction_id = NULL
            """
        )

        for runtime_table in ("relation", "commander", "province", "faction"):
            rows = cls._fetch_dicts(
                db,
                """
                SELECT runtime_id
                FROM seed_frontier_runtime_map
                WHERE runtime_table = ?
                """,
                (runtime_table,),
            )
            for row in rows:
                db.execute(f"DELETE FROM {runtime_table} WHERE id = ?", (row["runtime_id"],))

        db.execute("DELETE FROM seed_frontier_runtime_map")
        db.commit()

    @classmethod
    def _activate_factions(cls, db: DatabaseManager) -> dict[str, int]:
        rows = cls._fetch_dicts(db, "SELECT * FROM seed_faction ORDER BY faction_id")
        faction_map: dict[str, int] = {}

        for row in rows:
            seed_faction_id = row["faction_id"]
            mapped_id = cls._existing_runtime_id(db, seed_faction_id, "faction", "faction")
            if mapped_id is not None:
                faction_map[seed_faction_id] = mapped_id
                continue

            pressure_stats = cls._faction_pressure_stats(db, seed_faction_id)
            cursor = db.execute(
                """
                INSERT INTO faction (
                    name, faction_type, government_type, power_level, wealth,
                    stability, personality_traits, seed_faction_id, dominant_culture,
                    dominant_species, religion_id, tier, primary_goal, conflict_pressure
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row["name"],
                    row["identity"] or "seed_frontier_faction",
                    row["government"],
                    pressure_stats["power_level"],
                    pressure_stats["wealth"],
                    pressure_stats["stability"],
                    cls._personality_traits(db, row),
                    seed_faction_id,
                    row["dominant_culture"],
                    row["dominant_species"],
                    row["religion_id"],
                    row.get("tier", "tier_3"),
                    row["primary_goal"],
                    row["conflict_pressure"],
                ),
            )
            runtime_id = int(cursor.lastrowid)
            cls._remember_mapping(db, seed_faction_id, "faction", "faction", runtime_id)
            faction_map[seed_faction_id] = runtime_id

        return faction_map

    @classmethod
    def _activate_provinces(
        cls,
        db: DatabaseManager,
        kingdom_id: int,
        faction_map: dict[str, int],
    ) -> dict[str, int]:
        rows = cls._fetch_dicts(db, "SELECT * FROM seed_province ORDER BY province_id")
        province_map: dict[str, int] = {}

        for row in rows:
            seed_province_id = row["province_id"]
            mapped_id = cls._existing_runtime_id(db, seed_province_id, "province", "province")
            if mapped_id is not None:
                province_map[seed_province_id] = mapped_id
                continue

            strategic_value = int(row["strategic_value"])
            road_level = int(row["road_level"])
            port_level = int(row["port_level"])
            fort_level = int(row["fort_level"])
            controller_faction_id = faction_map.get(row["controller"])
            province_name = row["common_name"] or row["local_name"]
            food_stored = cls._food_stored(row["primary_resource"], strategic_value)
            garrison_size = fort_level * 250 + max(0, strategic_value - 50) * 6

            cursor = db.execute(
                """
                INSERT INTO province (
                    kingdom_id, name, population, fort_level, food_stored,
                    monthly_tax, loyalty, garrison_size, garrison_capacity,
                    governor_name, seed_province_id, controller_faction_id,
                    region_id, terrain, primary_resource, road_level,
                    port_level, mana_site_level, strategic_value
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    kingdom_id,
                    province_name,
                    max(5000, strategic_value * 1000),
                    fort_level,
                    food_stored,
                    max(500, strategic_value * 80 + road_level * 150 + port_level * 250),
                    cls._province_loyalty(row),
                    garrison_size,
                    max(1000, garrison_size + 600),
                    row["controller"],
                    seed_province_id,
                    controller_faction_id,
                    row["region_id"],
                    row["terrain"],
                    row["primary_resource"],
                    road_level,
                    port_level,
                    int(row["mana_site_level"]),
                    strategic_value,
                ),
            )
            runtime_id = int(cursor.lastrowid)
            cls._remember_mapping(db, seed_province_id, "province", "province", runtime_id)
            province_map[seed_province_id] = runtime_id

        return province_map

    @classmethod
    def _activate_relations(cls, db: DatabaseManager, faction_map: dict[str, int]) -> int:
        rows = cls._fetch_dicts(db, "SELECT * FROM seed_relation ORDER BY relation_id")
        active_count = 0

        for row in rows:
            seed_relation_id = row["relation_id"]
            mapped_id = cls._existing_runtime_id(db, seed_relation_id, "relation", "relation")
            if mapped_id is not None:
                active_count += 1
                continue

            faction_a_id = faction_map[row["faction_a"]]
            faction_b_id = faction_map[row["faction_b"]]
            score = int(row["score"])
            war_risk = int(row["war_risk"])
            status = cls._relation_status(score, war_risk)

            cursor = db.execute(
                """
                INSERT INTO relation (
                    faction_a_id, faction_b_id, status, opinion, trust,
                    trade_agreement, military_alliance, seed_relation_id,
                    main_tension, war_risk
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    faction_a_id,
                    faction_b_id,
                    status.name,
                    cls._clamp(score, -100, 100),
                    cls._clamp(score // 2, -100, 100),
                    int(score >= 25),
                    int(score >= 65),
                    seed_relation_id,
                    row["main_tension"],
                    war_risk,
                ),
            )
            runtime_id = int(cursor.lastrowid)
            cls._remember_mapping(db, seed_relation_id, "relation", "relation", runtime_id)
            active_count += 1

        return active_count

    @classmethod
    def _activate_commanders(
        cls,
        db: DatabaseManager,
        kingdom_id: int,
        faction_map: dict[str, int],
    ) -> dict[str, int]:
        rows = cls._fetch_dicts(db, "SELECT * FROM seed_character ORDER BY character_id")
        commander_map: dict[str, int] = {}

        for row in rows:
            seed_character_id = row["character_id"]
            mapped_id = cls._existing_runtime_id(db, seed_character_id, "commander", "commander")
            if mapped_id is not None:
                commander_map[seed_character_id] = mapped_id
                continue

            role = cls._commander_role(row["role"])
            age = int(row["age"])
            active_faction_id = faction_map.get(row["faction_id"])
            base_skill = cls._clamp(45 + age // 3, 45, 82)

            cursor = db.execute(
                """
                INSERT INTO commander (
                    kingdom_id, name, role, leadership, tactics, logistics,
                    loyalty, status, traits, seed_character_id, species_id,
                    culture_id, source_faction_id, active_faction_id, core_pressure
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    kingdom_id,
                    row["name"],
                    role.name,
                    cls._clamp(base_skill + cls._role_leadership_bonus(role), 0, 100),
                    cls._clamp(base_skill + cls._role_tactics_bonus(role), 0, 100),
                    cls._clamp(base_skill + cls._role_logistics_bonus(role), 0, 100),
                    cls._loyalty_for_pressure(row["core_pressure"]),
                    "Active",
                    cls._character_traits(row),
                    seed_character_id,
                    row["species_id"],
                    row["culture_id"],
                    row["faction_id"],
                    active_faction_id,
                    row["core_pressure"],
                ),
            )
            runtime_id = int(cursor.lastrowid)
            cls._remember_mapping(db, seed_character_id, "commander", "commander", runtime_id)
            commander_map[seed_character_id] = runtime_id

        return commander_map

    @classmethod
    def _link_claims(
        cls,
        db: DatabaseManager,
        faction_map: dict[str, int],
        province_map: dict[str, int],
    ) -> int:
        rows = cls._fetch_dicts(db, "SELECT claim_id, claimant, target FROM claim")
        linked = 0

        for row in rows:
            claimant_id = faction_map.get(row["claimant"])
            target_id = province_map.get(row["target"])
            if claimant_id is None and target_id is None:
                continue
            db.execute(
                """
                UPDATE claim
                SET active_claimant_faction_id = ?,
                    active_target_province_id = ?
                WHERE claim_id = ?
                """,
                (claimant_id, target_id, row["claim_id"]),
            )
            linked += 1

        return linked

    @classmethod
    def _link_mages(
        cls,
        db: DatabaseManager,
        faction_map: dict[str, int],
        commander_map: dict[str, int],
    ) -> int:
        rows = cls._fetch_dicts(
            db,
            "SELECT mage_id, character_id, patron_faction FROM mage ORDER BY mage_id",
        )
        linked = 0

        for row in rows:
            commander_id = commander_map.get(row["character_id"])
            patron_faction_id = faction_map.get(row["patron_faction"])
            if commander_id is None and patron_faction_id is None:
                continue
            db.execute(
                """
                UPDATE mage
                SET active_character_commander_id = ?,
                    active_patron_faction_id = ?
                WHERE mage_id = ?
                """,
                (commander_id, patron_faction_id, row["mage_id"]),
            )
            linked += 1

        return linked

    @classmethod
    def _ensure_seed_exists(cls, db: DatabaseManager, seed_id: str) -> None:
        row = db.execute("SELECT 1 FROM seed_region WHERE seed_id = ?", (seed_id,)).fetchone()
        if row is None:
            raise DatabaseError(f"Seed frontier not found: {seed_id}")

    @classmethod
    def _ensure_runtime_kingdom(cls, db: DatabaseManager, seed_id: str) -> int:
        row = db.execute("SELECT id FROM kingdom ORDER BY id LIMIT 1").fetchone()
        if row is not None:
            return int(row[0])

        seed_region = cls._fetch_dicts(
            db,
            "SELECT name FROM seed_region WHERE seed_id = ?",
            (seed_id,),
        )[0]
        cursor = db.execute(
            """
            INSERT INTO kingdom (
                name, ruler_name, population, treasury_silver, monthly_income,
                monthly_expenses, morale, loyalty, grain_stores
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                seed_region["name"],
                "Frontier Chronicle",
                1_000_000,
                250_000,
                12_000,
                9_000,
                70,
                70,
                20_000,
            ),
        )
        return int(cursor.lastrowid)

    @classmethod
    def _existing_runtime_id(
        cls,
        db: DatabaseManager,
        seed_id: str,
        entity_type: str,
        runtime_table: str,
    ) -> int | None:
        mapped = db.execute(
            """
            SELECT runtime_id
            FROM seed_frontier_runtime_map
            WHERE seed_id = ? AND entity_type = ? AND runtime_table = ?
            """,
            (seed_id, entity_type, runtime_table),
        ).fetchone()
        if mapped is not None:
            exists = db.execute(
                f"SELECT 1 FROM {runtime_table} WHERE id = ?",
                (mapped[0],),
            ).fetchone()
            if exists is not None:
                return int(mapped[0])

        seed_column = {
            "faction": "seed_faction_id",
            "province": "seed_province_id",
            "relation": "seed_relation_id",
            "commander": "seed_character_id",
        }.get(runtime_table)
        if seed_column is None:
            return None

        found = db.execute(
            f"SELECT id FROM {runtime_table} WHERE {seed_column} = ?",
            (seed_id,),
        ).fetchone()
        if found is None:
            return None

        runtime_id = int(found[0])
        cls._remember_mapping(db, seed_id, entity_type, runtime_table, runtime_id)
        return runtime_id

    @staticmethod
    def _remember_mapping(
        db: DatabaseManager,
        seed_id: str,
        entity_type: str,
        runtime_table: str,
        runtime_id: int,
    ) -> None:
        db.execute(
            """
            INSERT OR REPLACE INTO seed_frontier_runtime_map (
                seed_id, entity_type, runtime_table, runtime_id
            ) VALUES (?, ?, ?, ?)
            """,
            (seed_id, entity_type, runtime_table, runtime_id),
        )

    @classmethod
    def _faction_pressure_stats(cls, db: DatabaseManager, seed_faction_id: str) -> dict[str, int]:
        province_values = [
            int(row["strategic_value"])
            for row in cls._fetch_dicts(
                db,
                "SELECT strategic_value FROM seed_province WHERE controller = ?",
                (seed_faction_id,),
            )
        ]
        claim_count = db.execute(
            "SELECT COUNT(*) FROM claim WHERE claimant = ?",
            (seed_faction_id,),
        ).fetchone()[0]
        avg_value = sum(province_values) // len(province_values) if province_values else 50
        power_level = cls._clamp(45 + len(province_values) * 5 + claim_count * 3, 20, 100)
        wealth = cls._clamp(40 + avg_value // 2, 20, 100)
        stability = cls._clamp(75 - claim_count * 4, 20, 100)
        return {
            "power_level": power_level,
            "wealth": wealth,
            "stability": stability,
        }

    @classmethod
    def _personality_traits(cls, db: DatabaseManager, row: dict[str, Any]) -> str:
        traits = [
            f"culture:{row['dominant_culture']}",
            f"religion:{row['religion_id']}",
            f"goal:{row['primary_goal']}",
        ]
        traits.extend(cls._modifier_traits(db, "culture_modifier", "culture_id", row["dominant_culture"]))
        traits.extend(cls._modifier_traits(db, "religion_modifier", "religion_id", row["religion_id"]))
        return ", ".join(trait for trait in traits if trait and not trait.endswith(":"))

    @staticmethod
    def _modifier_traits(
        db: DatabaseManager,
        table: str,
        id_column: str,
        row_id: str,
    ) -> list[str]:
        if not row_id:
            return []
        row = db.execute(
            f"SELECT modifiers_json FROM {table} WHERE {id_column} = ?",
            (row_id,),
        ).fetchone()
        if row is None:
            return []
        modifiers = json.loads(row[0] or "{}")
        priority_keys = (
            "road_control_priority",
            "legal_claim_weight",
            "lawful_claim_weight",
            "treaty_memory_years",
            "morale_oath_war_mod",
            "trade_trust_mod",
            "naval_power_mod",
            "food_need_mod",
            "counter_mage_mod",
        )
        return [f"{key}:{modifiers[key]}" for key in priority_keys if key in modifiers]

    @staticmethod
    def _relation_status(score: int, war_risk: int) -> FactionStatus:
        if score <= -50 or war_risk >= 70:
            return FactionStatus.ENEMY
        if score <= -20:
            return FactionStatus.RIVAL
        if score >= 60:
            return FactionStatus.ALLY
        if score >= 25:
            return FactionStatus.TRADE_PARTNER
        return FactionStatus.NEUTRAL

    @staticmethod
    def _commander_role(raw_role: str) -> CommanderRole:
        lowered = raw_role.lower()
        if any(token in lowered for token in ("king", "speaker", "prince", "matriarch", "lord")):
            return CommanderRole.SOVEREIGN
        if any(token in lowered for token in ("commander", "marshal", "warlord", "raid")):
            return CommanderRole.GENERAL
        if any(token in lowered for token in ("factor", "envoy", "agent", "ambassador")):
            return CommanderRole.AMBASSADOR
        if any(token in lowered for token in ("scribe", "keeper", "steward")):
            return CommanderRole.STEWARD
        return CommanderRole.CAPTAIN

    @staticmethod
    def _role_leadership_bonus(role: CommanderRole) -> int:
        return {
            CommanderRole.SOVEREIGN: 10,
            CommanderRole.GENERAL: 8,
            CommanderRole.AMBASSADOR: 2,
            CommanderRole.STEWARD: 0,
        }.get(role, 4)

    @staticmethod
    def _role_tactics_bonus(role: CommanderRole) -> int:
        return {
            CommanderRole.GENERAL: 10,
            CommanderRole.CAPTAIN: 6,
            CommanderRole.SOVEREIGN: 2,
        }.get(role, 0)

    @staticmethod
    def _role_logistics_bonus(role: CommanderRole) -> int:
        return {
            CommanderRole.STEWARD: 10,
            CommanderRole.AMBASSADOR: 6,
            CommanderRole.GENERAL: 2,
        }.get(role, 0)

    @staticmethod
    def _character_traits(row: dict[str, Any]) -> str:
        return (
            f"seed_character:{row['character_id']}, species:{row['species_id']}, "
            f"culture:{row['culture_id']}, faction:{row['faction_id']}, "
            f"pressure:{row['core_pressure']}"
        )

    @staticmethod
    def _loyalty_for_pressure(core_pressure: str) -> int:
        lowered = core_pressure.lower()
        if any(token in lowered for token in ("resist", "defend", "keep")):
            return 82
        if any(token in lowered for token in ("must", "prove", "control")):
            return 72
        return 68

    @staticmethod
    def _food_stored(primary_resource: str, strategic_value: int) -> int:
        if primary_resource == "GRAIN":
            return strategic_value * 500
        if primary_resource == "HORSES":
            return strategic_value * 180
        return max(3000, strategic_value * 120)

    @staticmethod
    def _province_loyalty(row: dict[str, Any]) -> int:
        controller = row["controller"]
        enemy_name = row["enemy_name"]
        base = 68
        if "FAC_ROV" in controller and "Tax" in enemy_name:
            base -= 8
        if "FAC_GHARU" in controller:
            base += 6
        return SeedFrontierActivation._clamp(base, 35, 95)

    @staticmethod
    def _clamp(value: int, minimum: int, maximum: int) -> int:
        return max(minimum, min(maximum, value))

    @staticmethod
    def _fetch_dicts(
        db: DatabaseManager,
        query: str,
        params: tuple[Any, ...] = (),
    ) -> list[dict[str, Any]]:
        cursor = db.execute(query, params)
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

"""Seed SQLite lore reference tables from authored CSV files."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

from warfare_simulation.config.csv_loader import CsvLoreLoader
from warfare_simulation.persistence.database import DatabaseManager


class LoreBootstrap:
    """Load CSV lore once into SQLite reference and seed tables."""

    @staticmethod
    def seed_lore(
        db: DatabaseManager,
        lore_dir: str | Path | None = None,
        *,
        force: bool = False,
    ) -> None:
        if not db.conn:
            db.connect()

        db.initialize_schema()
        loader = CsvLoreLoader(lore_dir)

        if force:
            LoreBootstrap.clear_lore_tables(db)

        LoreBootstrap.seed_species(db, loader.load_species())
        LoreBootstrap.seed_cultures(db, loader.load_cultures())
        LoreBootstrap.seed_religions(db, loader.load_religions())
        LoreBootstrap.seed_regions(db, loader.load_regions())
        LoreBootstrap.seed_lore_resources(db, loader.load_lore_resources())
        LoreBootstrap.seed_culture_modifiers(db, loader.load_culture_modifiers())
        LoreBootstrap.seed_religion_modifiers(db, loader.load_religion_modifiers())
        LoreBootstrap.seed_naming_styles(db, loader.load_naming_styles())
        LoreBootstrap.seed_ai_weights(db, loader.load_ai_weights())
        LoreBootstrap.seed_mechanic_hooks(db, loader.load_mechanic_hooks())
        LoreBootstrap.seed_seed_region(db, loader.load_seed_region())
        LoreBootstrap.seed_seed_factions(db, loader.load_seed_factions())
        LoreBootstrap.seed_seed_provinces(db, loader.load_seed_provinces())
        LoreBootstrap.seed_seed_relations(db, loader.load_seed_relations())
        LoreBootstrap.seed_seed_characters(db, loader.load_seed_characters())
        LoreBootstrap.seed_claims(db, loader.load_seed_claims())
        LoreBootstrap.seed_mages(db, loader.load_seed_mages())

        db.commit()

    @staticmethod
    def seed_species(db: DatabaseManager, rows: list[BaseModel]) -> None:
        for row in rows:
            data = row.model_dump()
            db.execute(
                """
                INSERT OR IGNORE INTO species (
                    species_id, common_name, self_name, avg_lifespan,
                    fertility_rate, food_need, population_recovery, magic_tendency,
                    strengths, weaknesses, political_pattern, legal_bias_notes,
                    self_name_meaning
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["species_id"],
                    data["common_name"],
                    data["self_name"],
                    data["avg_lifespan"],
                    data["fertility_rate"],
                    data["food_need"],
                    data["population_recovery"],
                    data["magic_tendency"],
                    data["strengths"],
                    data["weaknesses"],
                    data["political_pattern"],
                    data["legal_bias_notes"],
                    data["self_name_meaning"],
                ),
            )

    @staticmethod
    def seed_cultures(db: DatabaseManager, rows: list[BaseModel]) -> None:
        for row in rows:
            data = row.model_dump()
            db.execute(
                """
                INSERT OR IGNORE INTO culture (
                    culture_id, self_name, meaning, common_name, old_imperial_name,
                    enemy_insults, dominant_species, location, values_text,
                    military_style, government, contradiction
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["culture_id"],
                    data["self_name"],
                    data["meaning"],
                    data["common_name"],
                    data["old_imperial_name"],
                    data["enemy_insults"],
                    data["dominant_species"],
                    data["location"],
                    data["values"],
                    data["military_style"],
                    data["government"],
                    data["contradiction"],
                ),
            )

    @staticmethod
    def seed_culture_modifiers(db: DatabaseManager, rows: list[BaseModel]) -> None:
        for row in rows:
            data = row.model_dump()
            db.execute(
                """
                INSERT OR IGNORE INTO culture_modifier (culture_id, modifiers_json)
                VALUES (?, ?)
                """,
                (data["culture_id"], LoreBootstrap._modifier_payload(data, "culture_id")),
            )

    @staticmethod
    def seed_religions(db: DatabaseManager, rows: list[BaseModel]) -> None:
        for row in rows:
            data = row.model_dump()
            db.execute(
                """
                INSERT OR IGNORE INTO religion (
                    religion_id, name, type, core_claim, sacred, sinful,
                    war_stance, mage_stance, holy_war_triggers
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["religion_id"],
                    data["name"],
                    data["type"],
                    data["core_claim"],
                    data["sacred"],
                    data["sinful"],
                    data["war_stance"],
                    data["mage_stance"],
                    data["holy_war_triggers"],
                ),
            )

    @staticmethod
    def seed_religion_modifiers(db: DatabaseManager, rows: list[BaseModel]) -> None:
        for row in rows:
            data = row.model_dump()
            db.execute(
                """
                INSERT OR IGNORE INTO religion_modifier (religion_id, modifiers_json)
                VALUES (?, ?)
                """,
                (data["religion_id"], LoreBootstrap._modifier_payload(data, "religion_id")),
            )

    @staticmethod
    def seed_regions(db: DatabaseManager, rows: list[BaseModel]) -> None:
        for row in rows:
            data = row.model_dump()
            db.execute(
                """
                INSERT OR IGNORE INTO region (
                    region_id, name, climate, terrain, primary_resources, danger,
                    dominant_cultures, common_war_type
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["region_id"],
                    data["name"],
                    data["climate"],
                    data["terrain"],
                    data["primary_resources"],
                    data["danger"],
                    data["dominant_cultures"],
                    data["common_war_type"],
                ),
            )

    @staticmethod
    def seed_lore_resources(db: DatabaseManager, rows: list[BaseModel]) -> None:
        for row in rows:
            data = row.model_dump()
            db.execute(
                """
                INSERT OR IGNORE INTO lore_resource (
                    resource_id, name, category, why_it_matters,
                    scarcity_effect, war_relevance
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    data["resource_id"],
                    data["name"],
                    data["category"],
                    data["why_it_matters"],
                    data["scarcity_effect"],
                    data["war_relevance"],
                ),
            )

    @staticmethod
    def seed_naming_styles(db: DatabaseManager, rows: list[BaseModel]) -> None:
        for row in rows:
            data = row.model_dump()
            db.execute(
                """
                INSERT OR IGNORE INTO naming_style (
                    style_id, culture_id, sound, examples, place_suffixes, avoid
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    data["style_id"],
                    data["culture_id"],
                    data["sound"],
                    data["examples"],
                    data["place_suffixes"],
                    data["avoid"],
                ),
            )

    @staticmethod
    def seed_ai_weights(db: DatabaseManager, rows: list[BaseModel]) -> None:
        for row in rows:
            data = row.model_dump()
            db.execute(
                """
                INSERT OR IGNORE INTO ai_weight (ai_weight_id, applies_to, weight, drives)
                VALUES (?, ?, ?, ?)
                """,
                (
                    data["ai_weight_id"],
                    data["applies_to"],
                    data["weight"],
                    data["drives"],
                ),
            )

    @staticmethod
    def seed_mechanic_hooks(db: DatabaseManager, rows: list[BaseModel]) -> None:
        for row in rows:
            data = row.model_dump()
            db.execute(
                """
                INSERT OR IGNORE INTO mechanic_hook (hook_id, input_text, output_text)
                VALUES (?, ?, ?)
                """,
                (data["hook_id"], data["input"], data["output"]),
            )

    @staticmethod
    def seed_seed_region(db: DatabaseManager, rows: list[BaseModel]) -> None:
        for row in rows:
            data = row.model_dump()
            db.execute(
                """
                INSERT OR IGNORE INTO seed_region (seed_id, name, description, tests)
                VALUES (?, ?, ?, ?)
                """,
                (data["seed_id"], data["name"], data["description"], data["tests"]),
            )

    @staticmethod
    def seed_seed_factions(db: DatabaseManager, rows: list[BaseModel]) -> None:
        for row in rows:
            data = row.model_dump()
            db.execute(
                """
                INSERT OR IGNORE INTO seed_faction (
                    faction_id, name, identity, dominant_culture, dominant_species,
                    religion_id, government, tier, conflict_pressure, primary_goal
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["faction_id"],
                    data["name"],
                    data["identity"],
                    data["dominant_culture"],
                    data["dominant_species"],
                    data["religion_id"],
                    data["government"],
                    data.get("tier", "tier_3"),
                    data["conflict_pressure"],
                    data["primary_goal"],
                ),
            )

    @staticmethod
    def seed_seed_provinces(db: DatabaseManager, rows: list[BaseModel]) -> None:
        for row in rows:
            data = row.model_dump()
            db.execute(
                """
                INSERT OR IGNORE INTO seed_province (
                    province_id, local_name, common_name, old_imperial_name,
                    religious_name, enemy_name, region_id, controller, terrain,
                    primary_resource, road_level, port_level, fort_level,
                    mana_site_level, strategic_value
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["province_id"],
                    data["local_name"],
                    data["common_name"],
                    data["old_imperial_name"],
                    data["religious_name"],
                    data["enemy_name"],
                    data["region_id"],
                    data["controller"],
                    data["terrain"],
                    data["primary_resource"],
                    data["road_level"],
                    data["port_level"],
                    data["fort_level"],
                    data["mana_site_level"],
                    data["strategic_value"],
                ),
            )

    @staticmethod
    def seed_seed_relations(db: DatabaseManager, rows: list[BaseModel]) -> None:
        for row in rows:
            data = row.model_dump()
            db.execute(
                """
                INSERT OR IGNORE INTO seed_relation (
                    relation_id, faction_a, faction_b, score, main_tension, war_risk
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    data["relation_id"],
                    data["faction_a"],
                    data["faction_b"],
                    data["score"],
                    data["main_tension"],
                    data["war_risk"],
                ),
            )

    @staticmethod
    def seed_seed_characters(db: DatabaseManager, rows: list[BaseModel]) -> None:
        for row in rows:
            data = row.model_dump()
            db.execute(
                """
                INSERT OR IGNORE INTO seed_character (
                    character_id, name, species_id, culture_id, faction_id,
                    role, age, core_pressure
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["character_id"],
                    data["name"],
                    data["species_id"],
                    data["culture_id"],
                    data["faction_id"],
                    data["role"],
                    data["age"],
                    data["core_pressure"],
                ),
            )

    @staticmethod
    def seed_claims(db: DatabaseManager, rows: list[BaseModel]) -> None:
        for row in rows:
            data = row.model_dump()
            db.execute(
                """
                INSERT OR IGNORE INTO claim (
                    claim_id, claimant, target, claim_type, source, strength,
                    decay_rate, myth_status, recognized_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["claim_id"],
                    data["claimant"],
                    data["target"],
                    data["claim_type"],
                    data["source"],
                    data["strength"],
                    data["decay_rate"],
                    data["myth_status"],
                    data["recognized_by"],
                ),
            )

    @staticmethod
    def seed_mages(db: DatabaseManager, rows: list[BaseModel]) -> None:
        for row in rows:
            data = row.model_dump()
            db.execute(
                """
                INSERT OR IGNORE INTO mage (
                    mage_id, character_id, species_id, capacity, control, recovery,
                    strain_tolerance, specialization, legal_status, patron_faction,
                    risk_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["mage_id"],
                    data["character_id"],
                    data["species_id"],
                    data["capacity"],
                    data["control"],
                    data["recovery"],
                    data["strain_tolerance"],
                    data["specialization"],
                    data["legal_status"],
                    data["patron_faction"],
                    data["risk_score"],
                ),
            )

    @staticmethod
    def clear_lore_tables(db: DatabaseManager) -> None:
        for table in (
            "mage",
            "claim",
            "seed_character",
            "seed_relation",
            "seed_province",
            "seed_faction",
            "seed_region",
            "mechanic_hook",
            "ai_weight",
            "naming_style",
            "culture_modifier",
            "religion_modifier",
            "lore_resource",
            "region",
            "religion",
            "culture",
            "species",
        ):
            db.execute(f"DELETE FROM {table}")

    @staticmethod
    def _modifier_payload(data: dict[str, object], id_field: str) -> str:
        payload = {
            key: value
            for key, value in data.items()
            if key != id_field and value not in ("", None)
        }
        return json.dumps(payload, sort_keys=True)

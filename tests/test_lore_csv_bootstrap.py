"""Tests for CSV-backed lore loading and SQLite seeding."""

import json
from pathlib import Path

from warfare_simulation.config.config import ConfigManager
from warfare_simulation.config.csv_loader import CsvLoreLoader
from warfare_simulation.persistence.campaign_bootstrap import CampaignBootstrap
from warfare_simulation.persistence.database import DatabaseManager
from warfare_simulation.persistence.lore_bootstrap import LoreBootstrap


ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "src" / "warfare_simulation" / "config" / "data"


def test_lore_csv_loader_validates_core_files():
    """The first lore layer should load as typed, validated CSV rows."""
    loader = CsvLoreLoader()

    species = loader.load_species()
    cultures = loader.load_cultures()
    religions = loader.load_religions()
    regions = loader.load_regions()
    resources = loader.load_lore_resources()
    naming_styles = loader.load_naming_styles()
    seed_factions = loader.load_seed_factions()
    seed_provinces = loader.load_seed_provinces()
    seed_relations = loader.load_seed_relations()
    seed_characters = loader.load_seed_characters()
    seed_claims = loader.load_seed_claims()
    seed_mages = loader.load_seed_mages()

    assert {row.species_id for row in species} == {"human", "orc", "elf", "dwarf"}
    assert len(cultures) >= 8
    assert len(religions) >= 6
    assert len(regions) >= 5
    assert {row.resource_id for row in resources} >= {"GRAIN", "IRON"}
    assert all(style.culture_id.startswith("CULT_") for style in naming_styles)
    assert any(faction.faction_id == "FAC_ROV_HALEN" for faction in seed_factions)
    assert {faction.tier for faction in seed_factions} <= {"tier_1", "tier_2", "tier_3", "tier_4"}
    assert seed_provinces[0].road_level == 5
    assert seed_relations[0].score < 0
    assert seed_characters[0].age > 0
    assert seed_claims[0].decay_rate == -1
    assert seed_mages[0].capacity > 0


def test_lore_bootstrap_seeds_reference_tables_idempotently(tmp_path):
    """Lore CSVs seed SQLite once without duplicating rows on later startup."""
    loader = CsvLoreLoader()
    expected_counts = {
        "species": len(loader.load_species()),
        "culture": len(loader.load_cultures()),
        "culture_modifier": len(loader.load_culture_modifiers()),
        "religion": len(loader.load_religions()),
        "religion_modifier": len(loader.load_religion_modifiers()),
        "region": len(loader.load_regions()),
        "lore_resource": len(loader.load_lore_resources()),
        "naming_style": len(loader.load_naming_styles()),
        "ai_weight": len(loader.load_ai_weights()),
        "mechanic_hook": len(loader.load_mechanic_hooks()),
        "seed_region": len(loader.load_seed_region()),
        "seed_faction": len(loader.load_seed_factions()),
        "seed_province": len(loader.load_seed_provinces()),
        "seed_relation": len(loader.load_seed_relations()),
        "seed_character": len(loader.load_seed_characters()),
        "claim": len(loader.load_seed_claims()),
        "mage": len(loader.load_seed_mages()),
    }

    db = DatabaseManager(str(tmp_path / "lore.db"))
    db.connect()

    LoreBootstrap.seed_lore(db)
    LoreBootstrap.seed_lore(db)

    for table, expected_count in expected_counts.items():
        cursor = db.execute(f"SELECT COUNT(*) FROM {table}")
        assert cursor.fetchone()[0] == expected_count

    modifier_json = db.execute(
        "SELECT modifiers_json FROM culture_modifier WHERE culture_id = ?",
        ("CULT_ROVANT",),
    ).fetchone()[0]
    assert json.loads(modifier_json)["road_control_priority"] == "95"

    province = db.execute(
        """
        SELECT road_level, port_level, fort_level, mana_site_level, strategic_value
        FROM seed_province
        WHERE province_id = ?
        """,
        ("PROV_ROV_HALEM",),
    ).fetchone()
    assert province == (5, 2, 3, 1, 95)

    rov_tier = db.execute(
        "SELECT tier FROM seed_faction WHERE faction_id = ?",
        ("FAC_ROV_HALEN",),
    ).fetchone()[0]
    assert rov_tier == "tier_2"

    config_mgr = ConfigManager(str(CONFIG_DIR))
    kingdom_id = CampaignBootstrap.seed_from_config(config_mgr, db)
    assert kingdom_id == 1
    assert db.execute("SELECT COUNT(*) FROM kingdom").fetchone()[0] == 1

    db.close()

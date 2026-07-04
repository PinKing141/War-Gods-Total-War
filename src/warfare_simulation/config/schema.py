"""
Pydantic schemas for config validation.

Defines strongly-typed configuration structures with validation.
"""

from pydantic import BaseModel, ConfigDict, Field
from typing import List


class KingdomConfigSchema(BaseModel):
    """Schema for kingdom configuration."""
    
    name: str
    ruler_name: str
    population: int = Field(gt=0)
    treasury_silver: int = Field(ge=0)
    monthly_income: int = Field(ge=0)
    monthly_expenses: int = Field(ge=0)
    morale: int = Field(ge=0, le=100)
    loyalty: int = Field(ge=0, le=100)
    grain_stores: int = Field(ge=0)
    current_day: int = Field(default=1, ge=1, le=31)
    current_turn: int = Field(default=1, ge=1)
    current_month: int = Field(default=1, ge=1, le=12)
    current_year: int = Field(default=1, ge=1)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "The Dominion of Auster",
                "ruler_name": "Lord Protector Favour",
                "population": 450000,
                "treasury_silver": 520000,
                "monthly_income": 18500,
                "monthly_expenses": 12800,
                "morale": 85,
                "loyalty": 85,
                "grain_stores": 24,
            }
        }
    )


class ProvinceConfigSchema(BaseModel):
    """Schema for province configuration."""
    
    name: str
    population: int = Field(gt=0)
    fort_level: int = Field(ge=0, le=5)
    food_stored: int = Field(ge=0)
    monthly_tax: int = Field(ge=0)
    loyalty: int = Field(ge=0, le=100)
    garrison_size: int = Field(ge=0)
    garrison_capacity: int = Field(gt=0)
    governor_name: str
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Highreach",
                "population": 150000,
                "fort_level": 3,
                "food_stored": 120,
                "monthly_tax": 6000,
                "loyalty": 95,
                "garrison_size": 200,
                "garrison_capacity": 500,
                "governor_name": "Lady Clarissa",
            }
        }
    )


class UnitConfigSchema(BaseModel):
    """Schema for unit configuration."""
    
    name: str
    unit_type: str  # UnitType enum value
    soldiers: int = Field(ge=0)
    veterans: int = Field(ge=0)
    morale: int = Field(ge=0, le=100)
    fatigue: int = Field(ge=0, le=100)
    armor: str  # ArmorType enum value
    location_id: int = Field(ge=1)
    status: str  # UnitStatus enum value
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Auster Vanguard",
                "unit_type": "HEAVY_SPEARMEN",
                "soldiers": 500,
                "veterans": 50,
                "morale": 85,
                "fatigue": 0,
                "armor": "PLATE_MAIL",
                "location_id": 1,
                "status": "ACTIVE",
            }
        }
    )


class CommanderConfigSchema(BaseModel):
    """Schema for commander configuration."""
    
    name: str
    role: str  # CommanderRole enum value
    leadership: int = Field(ge=0, le=100)
    tactics: int = Field(ge=0, le=100)
    logistics: int = Field(ge=0, le=100)
    loyalty: int = Field(ge=0, le=100)
    status: str
    traits: str = ""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "General Marcus Thorn",
                "role": "GENERAL",
                "leadership": 85,
                "tactics": 80,
                "logistics": 75,
                "loyalty": 95,
                "status": "Active",
                "traits": "Courageous, Strategic",
            }
        }
    )


class FactionConfigSchema(BaseModel):
    """Schema for faction configuration."""
    
    name: str
    faction_type: str
    government_type: str
    power_level: int = Field(ge=0, le=100)
    wealth: int = Field(ge=0, le=100)
    stability: int = Field(ge=0, le=100)
    personality_traits: str = ""


class RelationConfigSchema(BaseModel):
    """Schema for diplomatic relation configuration."""
    
    faction_a_id: int = Field(ge=1)
    faction_b_id: int = Field(ge=1)
    status: str  # FactionStatus enum value
    opinion: int = Field(ge=-100, le=100)
    trust: int = Field(ge=-100, le=100)
    trade_agreement: bool = False
    military_alliance: bool = False


class ResourceConfigSchema(BaseModel):
    """Schema for resource configuration."""
    
    resource_type: str  # ResourceType enum value
    stored: int = Field(ge=0)
    monthly_production: int = Field(ge=0)
    monthly_consumption: int = Field(ge=0)
    max_storage: int = Field(gt=0)


class InitialKingdomConfigSchema(BaseModel):
    """Top-level schema for initial_kingdom.json."""
    
    kingdom: KingdomConfigSchema


class ProvincesConfigSchema(BaseModel):
    """Top-level schema for provinces.json."""
    
    provinces: List[ProvinceConfigSchema]


class UnitsConfigSchema(BaseModel):
    """Top-level schema for units.json."""
    
    units: List[UnitConfigSchema]


class CommandersConfigSchema(BaseModel):
    """Top-level schema for commanders.json."""
    
    commanders: List[CommanderConfigSchema]


class DiplomacyConfigSchema(BaseModel):
    """Top-level schema for diplomacy.json."""
    
    factions: List[FactionConfigSchema]
    relations: List[RelationConfigSchema]


class ResourcesConfigSchema(BaseModel):
    """Top-level schema for resources.json."""
    
    resources: List[ResourceConfigSchema]


class LoreCsvSchema(BaseModel):
    """Base schema for authored lore CSV rows."""

    model_config = ConfigDict(str_strip_whitespace=True)


class SpeciesCsvSchema(LoreCsvSchema):
    """Schema for lore_csv/03_species/species.csv."""

    species_id: str = Field(min_length=1)
    common_name: str = Field(min_length=1)
    self_name: str = ""
    avg_lifespan: str = ""
    fertility_rate: str = ""
    food_need: str = ""
    population_recovery: str = ""
    magic_tendency: str = ""
    strengths: str = ""
    weaknesses: str = ""
    political_pattern: str = ""
    legal_bias_notes: str = ""
    self_name_meaning: str = ""


class CultureCsvSchema(LoreCsvSchema):
    """Schema for lore_csv/05_cultures/cultures.csv."""

    culture_id: str = Field(min_length=1)
    self_name: str = Field(min_length=1)
    meaning: str = ""
    common_name: str = Field(min_length=1)
    old_imperial_name: str = ""
    enemy_insults: str = ""
    dominant_species: str = ""
    location: str = ""
    values: str = ""
    military_style: str = ""
    government: str = ""
    contradiction: str = ""


class CultureModifierCsvSchema(LoreCsvSchema):
    """Schema for lore_csv/05_cultures/culture_modifiers.csv."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="allow")

    culture_id: str = Field(min_length=1)


class ReligionCsvSchema(LoreCsvSchema):
    """Schema for lore_csv/06_religion/religions.csv."""

    religion_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    type: str = ""
    core_claim: str = ""
    sacred: str = ""
    sinful: str = ""
    war_stance: str = ""
    mage_stance: str = ""
    holy_war_triggers: str = ""


class ReligionModifierCsvSchema(LoreCsvSchema):
    """Schema for lore_csv/06_religion/religion_modifiers.csv."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="allow")

    religion_id: str = Field(min_length=1)


class RegionCsvSchema(LoreCsvSchema):
    """Schema for lore_csv/04_geography/regions.csv."""

    region_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    climate: str = ""
    terrain: str = ""
    primary_resources: str = ""
    danger: str = ""
    dominant_cultures: str = ""
    common_war_type: str = ""


class LoreResourceCsvSchema(LoreCsvSchema):
    """Schema for lore_csv/08_economy/resources.csv."""

    resource_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    category: str = ""
    why_it_matters: str = ""
    scarcity_effect: str = ""
    war_relevance: str = ""


class NamingStyleCsvSchema(LoreCsvSchema):
    """Schema for lore_csv/10_naming_data/naming_styles.csv."""

    style_id: str = Field(min_length=1)
    culture_id: str = Field(min_length=1)
    sound: str = ""
    examples: str = ""
    place_suffixes: str = ""
    avoid: str = ""


class AiWeightCsvSchema(LoreCsvSchema):
    """Schema for lore_csv/11_simulation_schemas/ai_weights.csv."""

    ai_weight_id: str = Field(min_length=1)
    applies_to: str = Field(min_length=1)
    weight: int
    drives: str = ""


class MechanicHookCsvSchema(LoreCsvSchema):
    """Schema for lore_csv/11_simulation_schemas/mechanic_hooks.csv."""

    hook_id: str = Field(min_length=1)
    input: str = ""
    output: str = ""


class SeedRegionCsvSchema(LoreCsvSchema):
    """Schema for lore_csv/12_seed_frontier/seed_region.csv."""

    seed_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = ""
    tests: str = ""


class SeedFactionCsvSchema(LoreCsvSchema):
    """Schema for lore_csv/12_seed_frontier/seed_factions.csv."""

    faction_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    identity: str = ""
    dominant_culture: str = ""
    dominant_species: str = ""
    religion_id: str = ""
    government: str = ""
    conflict_pressure: str = ""
    primary_goal: str = ""


class SeedProvinceCsvSchema(LoreCsvSchema):
    """Schema for lore_csv/12_seed_frontier/seed_provinces.csv."""

    province_id: str = Field(min_length=1)
    local_name: str = Field(min_length=1)
    common_name: str = ""
    old_imperial_name: str = ""
    religious_name: str = ""
    enemy_name: str = ""
    region_id: str = Field(min_length=1)
    controller: str = Field(min_length=1)
    terrain: str = ""
    primary_resource: str = ""
    road_level: int = Field(ge=0)
    port_level: int = Field(ge=0)
    fort_level: int = Field(ge=0)
    mana_site_level: int = Field(ge=0)
    strategic_value: int = Field(ge=0)


class SeedRelationCsvSchema(LoreCsvSchema):
    """Schema for lore_csv/12_seed_frontier/seed_relations.csv."""

    relation_id: str = Field(min_length=1)
    faction_a: str = Field(min_length=1)
    faction_b: str = Field(min_length=1)
    score: int
    main_tension: str = ""
    war_risk: int = Field(ge=0, le=100)


class SeedCharacterCsvSchema(LoreCsvSchema):
    """Schema for lore_csv/12_seed_frontier/seed_characters.csv."""

    character_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    species_id: str = Field(min_length=1)
    culture_id: str = Field(min_length=1)
    faction_id: str = Field(min_length=1)
    role: str = ""
    age: int = Field(ge=0)
    core_pressure: str = ""


class SeedClaimCsvSchema(LoreCsvSchema):
    """Schema for lore_csv/12_seed_frontier/seed_claims.csv."""

    claim_id: str = Field(min_length=1)
    claimant: str = Field(min_length=1)
    target: str = Field(min_length=1)
    claim_type: str = Field(min_length=1)
    source: str = ""
    strength: int = Field(ge=0)
    decay_rate: int = 0
    myth_status: str = ""
    recognized_by: str = ""


class SeedMageCsvSchema(LoreCsvSchema):
    """Schema for lore_csv/12_seed_frontier/seed_mages.csv."""

    mage_id: str = Field(min_length=1)
    character_id: str = Field(min_length=1)
    species_id: str = Field(min_length=1)
    capacity: int = Field(ge=0)
    control: int = Field(ge=0)
    recovery: int = Field(ge=0)
    strain_tolerance: int = Field(ge=0)
    specialization: str = ""
    legal_status: str = ""
    patron_faction: str = ""
    risk_score: int = Field(ge=0)

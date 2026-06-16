"""
Pydantic schemas for config validation.

Defines strongly-typed configuration structures with validation.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime


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
    current_turn: int = Field(default=1, ge=1)
    current_month: int = Field(default=1, ge=1, le=12)
    current_year: int = Field(default=1, ge=1)
    
    class Config:
        """Pydantic config."""
        schema_extra = {
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
    
    class Config:
        """Pydantic config."""
        schema_extra = {
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
    
    class Config:
        """Pydantic config."""
        schema_extra = {
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
    
    class Config:
        """Pydantic config."""
        schema_extra = {
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


class FactionConfigSchema(BaseModel):
    """Schema for faction configuration."""
    
    name: str
    faction_type: str
    government_type: str
    power_level: int = Field(ge=0, le=100)
    wealth: int = Field(ge=0, le=100)
    stability: int = Field(ge=0, le=100)


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

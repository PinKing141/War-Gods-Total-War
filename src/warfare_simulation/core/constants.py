"""
Constants and enums for the campaign engine.

This module centralizes all constants, enums, and magic values to:
- Prevent hardcoded strings throughout the codebase
- Provide IDE autocomplete for valid values
- Make it easy to add new types/categories
"""

from enum import Enum


# ============================================================================
# UNIT TYPES
# ============================================================================

class UnitType(Enum):
    """Military unit classifications."""
    HEAVY_SPEARMEN = "Heavy Spearmen"
    LIGHT_SPEARMEN = "Light Spearmen"
    RANGED = "Ranged"
    HEAVY_INFANTRY = "Heavy Infantry"
    MEDIUM_CAVALRY = "Medium Cavalry"
    LIGHT_CAVALRY = "Light Cavalry"
    ARCHERS = "Archers"
    CROSSBOWS = "Crossbows"
    SIEGE = "Siege"


# ============================================================================
# ARMOR TYPES
# ============================================================================

class ArmorType(Enum):
    """Unit armor classifications."""
    PLATE = "Plate"
    PLATE_MAIL = "Plate/Mail"
    MAIL = "Mail"
    BRIGANDINE = "Brigandine"
    GAMBESON = "Gambeson"
    LEATHER = "Leather"
    UNARMORED = "Unarmored"


# ============================================================================
# PROJECT TYPES
# ============================================================================

class ProjectType(Enum):
    """Construction and development project types."""
    FORTIFICATION = "Fortification"
    INFRASTRUCTURE = "Infrastructure"
    CONVOY = "Convoy"
    RESEARCH = "Research"
    TRADE_ROUTE = "Trade Route"
    SETTLEMENT = "Settlement"


# ============================================================================
# FACTION STATUSES
# ============================================================================

class FactionStatus(Enum):
    """Diplomatic relationship statuses."""
    ALLY = "Ally"
    RIVAL = "Rival"
    NEUTRAL = "Neutral"
    VASSAL = "Vassal"
    ENEMY = "Enemy"
    TRADE_PARTNER = "Trade Partner"


# ============================================================================
# EVENT CATEGORIES
# ============================================================================

class EventCategory(Enum):
    """Types of events that occur during the campaign."""
    SYSTEM = "System"
    DIPLOMACY = "Diplomacy"
    MILITARY = "Military"
    ECONOMY = "Economy"
    LOGISTICS = "Logistics"
    NATURAL = "Natural"
    INTRIGUE = "Intrigue"


# ============================================================================
# UNIT STATUS
# ============================================================================

class UnitStatus(Enum):
    """Operational status of military units."""
    ACTIVE = "Active"
    GARRISON = "Garrison"
    RECOVERING = "Recovering"
    DISBANDED = "Disbanded"
    DEPLETED = "Depleted"
    MOVING = "Moving"


# ============================================================================
# LOYALTY LEVELS
# ============================================================================

class LoyaltyLevel(Enum):
    """Loyalty rating classifications."""
    HOSTILE = "Hostile"  # < 20%
    DISLOYAL = "Disloyal"  # 20-40%
    NEUTRAL = "Neutral"  # 40-60%
    LOYAL = "Loyal"  # 60-80%
    DEVOTED = "Devoted"  # > 80%


# ============================================================================
# MORALE LEVELS
# ============================================================================

class MoraleLevel(Enum):
    """Morale rating classifications."""
    BROKEN = "Broken"  # < 20%
    LOW = "Low"  # 20-40%
    NEUTRAL = "Neutral"  # 40-60%
    GOOD = "Good"  # 60-80%
    EXCELLENT = "Excellent"  # > 80%


# ============================================================================
# COMMANDER ROLES
# ============================================================================

class CommanderRole(Enum):
    """Positions that commanders can hold."""
    SOVEREIGN = "Sovereign"
    GENERAL = "General"
    CAPTAIN = "Captain"
    LIEUTENANT = "Lieutenant"
    STEWARD = "Steward"
    SPYMASTER = "Spymaster"
    OVERSEER = "Overseer"
    AMBASSADOR = "Ambassador"


# ============================================================================
# RESOURCE TYPES
# ============================================================================

class ResourceType(Enum):
    """Types of resources in the campaign."""
    SILVER = "Silver"
    FOOD = "Food"
    IRON = "Iron"
    TIMBER = "Timber"
    STONE = "Stone"
    WOOL = "Wool"
    HORSES = "Horses"


# ============================================================================
# CONSTANTS
# ============================================================================

# Default values for new entities
DEFAULT_MORALE = 75
DEFAULT_LOYALTY = 75
DEFAULT_FATIGUE = 0

# Turn constants
TURN_DURATION_MONTHS = 1
MONTHS_PER_YEAR = 12

# Economic constants
DEFAULT_MONTHLY_INCOME = 0
DEFAULT_MONTHLY_EXPENSES = 0

# Military constants
MIN_UNIT_SIZE = 1
MAX_UNIT_SIZE = 1000
DEFAULT_RECRUITMENT_TIME = 3  # turns

# Database constants
DEFAULT_DB_PATH = "war_sim.db"
DB_SCHEMA_VERSION = 1

# Validation constants
MIN_POPULATION = 1000
MAX_LOYALTY = 100
MIN_LOYALTY = 0
MAX_MORALE = 100
MIN_MORALE = 0

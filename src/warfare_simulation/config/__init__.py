"""
Configuration module.

Handles campaign configuration loading and validation.
"""

from .config import ConfigManager
from .schema import (
    KingdomConfigSchema,
    ProvincesConfigSchema,
    UnitsConfigSchema,
    CommandersConfigSchema,
    DiplomacyConfigSchema,
    ResourcesConfigSchema,
)

__all__ = [
    "ConfigManager",
    "KingdomConfigSchema",
    "ProvincesConfigSchema",
    "UnitsConfigSchema",
    "CommandersConfigSchema",
    "DiplomacyConfigSchema",
    "ResourcesConfigSchema",
]

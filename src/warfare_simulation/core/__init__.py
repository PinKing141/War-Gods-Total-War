"""
Core module: Shared abstractions, constants, exceptions, and utilities.

This module provides the foundation for all other modules:
- base.py: Abstract base classes (GameEntity, GameSystem, SheetGenerator)
- constants.py: Enums and constants (UnitType, FactionStatus, ProjectType, etc.)
- exceptions.py: Custom exception classes
- logger.py: Centralized logging configuration
- validation.py: Cross-domain validation service
"""

from .base import GameEntity, GameSystem, SheetGenerator, IValidationRule
from .constants import UnitType, ProjectType, FactionStatus, EventCategory
from .exceptions import (
    InvalidCampaignStateError,
    ResourceError,
    ValidationError,
    DatabaseError,
)
from .logger import get_logger
from .validation import ValidationService

__all__ = [
    "GameEntity",
    "GameSystem",
    "SheetGenerator",
    "IValidationRule",
    "UnitType",
    "ProjectType",
    "FactionStatus",
    "EventCategory",
    "InvalidCampaignStateError",
    "ResourceError",
    "ValidationError",
    "DatabaseError",
    "get_logger",
    "ValidationService",
]

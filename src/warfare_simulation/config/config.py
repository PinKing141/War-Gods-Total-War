"""
Configuration manager.

Loads and validates campaign configuration from JSON files.
"""

import json
from pathlib import Path
from typing import Optional

from warfare_simulation.core.logger import get_logger
from warfare_simulation.core.exceptions import ConfigurationError
from .schema import (
    InitialKingdomConfigSchema,
    ProvincesConfigSchema,
    UnitsConfigSchema,
    CommandersConfigSchema,
    DiplomacyConfigSchema,
    ResourcesConfigSchema,
)


logger = get_logger(__name__)


class ConfigManager:
    """Loads and validates campaign configuration from JSON files."""
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize ConfigManager.
        
        Args:
            config_dir: Path to config/data directory. Defaults to src/warfare_simulation/config/data
        """
        if config_dir is None:
            # Default to config/data directory relative to this file
            config_dir = str(Path(__file__).parent / "data")
        
        self.config_dir = Path(config_dir)
        
        if not self.config_dir.exists():
            raise ConfigurationError(f"Config directory not found: {self.config_dir}")
        
        logger.info(f"ConfigManager initialized with config_dir: {self.config_dir}")
    
    def _load_json(self, filename: str) -> dict:
        """
        Load JSON file from config directory.
        
        Args:
            filename: Name of JSON file (e.g., "initial_kingdom.json")
        
        Returns:
            Parsed JSON dictionary
        
        Raises:
            ConfigurationError: If file not found or invalid JSON
        """
        filepath = self.config_dir / filename
        
        if not filepath.exists():
            raise ConfigurationError(f"Config file not found: {filepath}")
        
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
            logger.debug(f"Loaded config: {filename}")
            return data
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in {filename}: {e}")
        except Exception as e:
            raise ConfigurationError(f"Error loading {filename}: {e}")
    
    def load_kingdom_config(self) -> InitialKingdomConfigSchema:
        """
        Load and validate initial_kingdom.json.
        
        Returns:
            Validated kingdom configuration
        
        Raises:
            ConfigurationError: If validation fails
        """
        try:
            data = self._load_json("initial_kingdom.json")
            config = InitialKingdomConfigSchema(**data)
            logger.info(f"Kingdom config loaded: {config.kingdom.name}")
            return config
        except Exception as e:
            raise ConfigurationError(f"Failed to load kingdom config: {e}")
    
    def load_provinces_config(self) -> ProvincesConfigSchema:
        """
        Load and validate provinces.json.
        
        Returns:
            Validated provinces configuration
        
        Raises:
            ConfigurationError: If validation fails
        """
        try:
            data = self._load_json("provinces.json")
            config = ProvincesConfigSchema(**data)
            logger.info(f"Provinces config loaded: {len(config.provinces)} provinces")
            return config
        except Exception as e:
            raise ConfigurationError(f"Failed to load provinces config: {e}")
    
    def load_units_config(self) -> UnitsConfigSchema:
        """
        Load and validate units.json.
        
        Returns:
            Validated units configuration
        
        Raises:
            ConfigurationError: If validation fails
        """
        try:
            data = self._load_json("units.json")
            config = UnitsConfigSchema(**data)
            logger.info(f"Units config loaded: {len(config.units)} units")
            return config
        except Exception as e:
            raise ConfigurationError(f"Failed to load units config: {e}")
    
    def load_commanders_config(self) -> CommandersConfigSchema:
        """
        Load and validate commanders.json.
        
        Returns:
            Validated commanders configuration
        
        Raises:
            ConfigurationError: If validation fails
        """
        try:
            data = self._load_json("commanders.json")
            config = CommandersConfigSchema(**data)
            logger.info(f"Commanders config loaded: {len(config.commanders)} commanders")
            return config
        except Exception as e:
            raise ConfigurationError(f"Failed to load commanders config: {e}")
    
    def load_diplomacy_config(self) -> DiplomacyConfigSchema:
        """
        Load and validate diplomacy.json.
        
        Returns:
            Validated diplomacy configuration
        
        Raises:
            ConfigurationError: If validation fails
        """
        try:
            data = self._load_json("diplomacy.json")
            config = DiplomacyConfigSchema(**data)
            logger.info(
                f"Diplomacy config loaded: {len(config.factions)} factions, "
                f"{len(config.relations)} relations"
            )
            return config
        except Exception as e:
            raise ConfigurationError(f"Failed to load diplomacy config: {e}")
    
    def load_resources_config(self) -> ResourcesConfigSchema:
        """
        Load and validate resources.json.
        
        Returns:
            Validated resources configuration
        
        Raises:
            ConfigurationError: If validation fails
        """
        try:
            data = self._load_json("resources.json")
            config = ResourcesConfigSchema(**data)
            logger.info(f"Resources config loaded: {len(config.resources)} resources")
            return config
        except Exception as e:
            raise ConfigurationError(f"Failed to load resources config: {e}")
    
    def load_all_configs(self) -> dict:
        """
        Load all configuration files.
        
        Returns:
            Dictionary with all loaded configs
        
        Raises:
            ConfigurationError: If any config fails to load
        """
        logger.info("Loading all configurations...")
        
        return {
            "kingdom": self.load_kingdom_config(),
            "provinces": self.load_provinces_config(),
            "units": self.load_units_config(),
            "commanders": self.load_commanders_config(),
            "diplomacy": self.load_diplomacy_config(),
            "resources": self.load_resources_config(),
        }

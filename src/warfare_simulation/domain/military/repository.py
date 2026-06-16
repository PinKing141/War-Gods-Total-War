"""
Military domain repository.

Data access for units, commanders, and garrisons.
"""

from typing import Optional, List
from warfare_simulation.persistence.repository import Repository
from warfare_simulation.core.exceptions import RepositoryError
from .models import Unit, Commander, Garrison


class UnitRepository(Repository[Unit]):
    """Repository for Unit entities."""
    
    def __init__(self, db_manager=None):
        """Initialize Unit repository."""
        super().__init__(db_manager)
        self._units: dict = {}
        self._next_id = 1
    
    def create(self, entity: Unit) -> Unit:
        """Create a new unit."""
        if not entity.name:
            raise RepositoryError("Unit must have a name")
        
        entity.id = self._next_id
        entity.mark_updated()
        self._units[self._next_id] = entity
        self._next_id += 1
        return entity
    
    def get(self, entity_id: int) -> Optional[Unit]:
        """Fetch unit by ID."""
        return self._units.get(entity_id)
    
    def get_by_kingdom(self, kingdom_id: int) -> List[Unit]:
        """Fetch all units of a kingdom."""
        return [u for u in self._units.values() if u.kingdom_id == kingdom_id]
    
    def get_by_location(self, location_id: int) -> List[Unit]:
        """Fetch all units at a location."""
        return [u for u in self._units.values() if u.location_id == location_id]
    
    def update(self, entity: Unit) -> Unit:
        """Update existing unit."""
        if entity.id not in self._units:
            raise RepositoryError(f"Unit with ID {entity.id} not found")
        
        entity.mark_updated()
        self._units[entity.id] = entity
        return entity
    
    def delete(self, entity_id: int) -> bool:
        """Delete unit by ID."""
        if entity_id in self._units:
            del self._units[entity_id]
            return True
        return False
    
    def list_all(self) -> List[Unit]:
        """Fetch all units."""
        return list(self._units.values())
    
    def hydrate(self, entity: Unit) -> Unit:
        """Load a unit with a pre-assigned ID from SQLite."""
        return self._hydrate_entity(entity, self._units)


class CommanderRepository(Repository[Commander]):
    """Repository for Commander entities."""
    
    def __init__(self, db_manager=None):
        """Initialize Commander repository."""
        super().__init__(db_manager)
        self._commanders: dict = {}
        self._next_id = 1
    
    def create(self, entity: Commander) -> Commander:
        """Create a new commander."""
        if not entity.name:
            raise RepositoryError("Commander must have a name")
        
        entity.id = self._next_id
        entity.mark_updated()
        self._commanders[self._next_id] = entity
        self._next_id += 1
        return entity
    
    def get(self, entity_id: int) -> Optional[Commander]:
        """Fetch commander by ID."""
        return self._commanders.get(entity_id)
    
    def get_by_kingdom(self, kingdom_id: int) -> List[Commander]:
        """Fetch all commanders of a kingdom."""
        return [c for c in self._commanders.values() if c.kingdom_id == kingdom_id]
    
    def get_by_name(self, name: str) -> Optional[Commander]:
        """Fetch commander by name."""
        for commander in self._commanders.values():
            if commander.name == name:
                return commander
        return None
    
    def update(self, entity: Commander) -> Commander:
        """Update existing commander."""
        if entity.id not in self._commanders:
            raise RepositoryError(f"Commander with ID {entity.id} not found")
        
        entity.mark_updated()
        self._commanders[entity.id] = entity
        return entity
    
    def delete(self, entity_id: int) -> bool:
        """Delete commander by ID."""
        if entity_id in self._commanders:
            del self._commanders[entity_id]
            return True
        return False
    
    def list_all(self) -> List[Commander]:
        """Fetch all commanders."""
        return list(self._commanders.values())
    
    def hydrate(self, entity: Commander) -> Commander:
        """Load a commander with a pre-assigned ID from SQLite."""
        return self._hydrate_entity(entity, self._commanders)


class GarrisonRepository(Repository[Garrison]):
    """Repository for Garrison entities."""
    
    def __init__(self, db_manager=None):
        """Initialize Garrison repository."""
        super().__init__(db_manager)
        self._garrisons: dict = {}
        self._next_id = 1
    
    def create(self, entity: Garrison) -> Garrison:
        """Create a new garrison."""
        entity.id = self._next_id
        entity.mark_updated()
        self._garrisons[self._next_id] = entity
        self._next_id += 1
        return entity
    
    def get(self, entity_id: int) -> Optional[Garrison]:
        """Fetch garrison by ID."""
        return self._garrisons.get(entity_id)
    
    def get_by_location(self, location_id: int) -> Optional[Garrison]:
        """Fetch garrison at a location."""
        for garrison in self._garrisons.values():
            if garrison.location_id == location_id:
                return garrison
        return None
    
    def update(self, entity: Garrison) -> Garrison:
        """Update existing garrison."""
        if entity.id not in self._garrisons:
            raise RepositoryError(f"Garrison with ID {entity.id} not found")
        
        entity.mark_updated()
        self._garrisons[entity.id] = entity
        return entity
    
    def delete(self, entity_id: int) -> bool:
        """Delete garrison by ID."""
        if entity_id in self._garrisons:
            del self._garrisons[entity_id]
            return True
        return False
    
    def list_all(self) -> List[Garrison]:
        """Fetch all garrisons."""
        return list(self._garrisons.values())

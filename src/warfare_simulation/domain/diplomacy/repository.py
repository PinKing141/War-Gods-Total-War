"""
Diplomacy domain repository.

Data access for factions, relations, spies, and missions.
"""

from typing import Optional, List
from warfare_simulation.persistence.repository import Repository
from warfare_simulation.core.exceptions import RepositoryError
from .models import Faction, Relation, Spy, Mission


class FactionRepository(Repository[Faction]):
    """Repository for Faction entities."""
    
    def __init__(self, db_manager=None):
        """Initialize Faction repository."""
        super().__init__(db_manager)
        self._factions: dict = {}
        self._next_id = 1
    
    def create(self, entity: Faction) -> Faction:
        """Create a new faction."""
        if not entity.name:
            raise RepositoryError("Faction must have a name")
        
        entity.id = self._next_id
        entity.mark_updated()
        self._factions[self._next_id] = entity
        self._next_id += 1
        return entity
    
    def get(self, entity_id: int) -> Optional[Faction]:
        """Fetch faction by ID."""
        return self._factions.get(entity_id)
    
    def get_by_name(self, name: str) -> Optional[Faction]:
        """Fetch faction by name."""
        for faction in self._factions.values():
            if faction.name == name:
                return faction
        return None
    
    def update(self, entity: Faction) -> Faction:
        """Update existing faction."""
        if entity.id not in self._factions:
            raise RepositoryError(f"Faction with ID {entity.id} not found")
        
        entity.mark_updated()
        self._factions[entity.id] = entity
        return entity
    
    def delete(self, entity_id: int) -> bool:
        """Delete faction by ID."""
        if entity_id in self._factions:
            del self._factions[entity_id]
            return True
        return False
    
    def list_all(self) -> List[Faction]:
        """Fetch all factions."""
        return list(self._factions.values())
    
    def hydrate(self, entity: Faction) -> Faction:
        """Load a faction with a pre-assigned ID from SQLite."""
        return self._hydrate_entity(entity, self._factions)


class RelationRepository(Repository[Relation]):
    """Repository for Relation entities."""
    
    def __init__(self, db_manager=None):
        """Initialize Relation repository."""
        super().__init__(db_manager)
        self._relations: dict = {}
        self._next_id = 1
    
    def create(self, entity: Relation) -> Relation:
        """Create a new relation."""
        entity.id = self._next_id
        entity.mark_updated()
        self._relations[self._next_id] = entity
        self._next_id += 1
        return entity
    
    def get(self, entity_id: int) -> Optional[Relation]:
        """Fetch relation by ID."""
        return self._relations.get(entity_id)
    
    def get_between(self, faction_a_id: int, faction_b_id: int) -> Optional[Relation]:
        """Fetch relation between two factions."""
        for relation in self._relations.values():
            if (
                (relation.faction_a_id == faction_a_id and relation.faction_b_id == faction_b_id) or
                (relation.faction_a_id == faction_b_id and relation.faction_b_id == faction_a_id)
            ):
                return relation
        return None
    
    def update(self, entity: Relation) -> Relation:
        """Update existing relation."""
        if entity.id not in self._relations:
            raise RepositoryError(f"Relation with ID {entity.id} not found")
        
        entity.mark_updated()
        self._relations[entity.id] = entity
        return entity
    
    def delete(self, entity_id: int) -> bool:
        """Delete relation by ID."""
        if entity_id in self._relations:
            del self._relations[entity_id]
            return True
        return False
    
    def list_all(self) -> List[Relation]:
        """Fetch all relations."""
        return list(self._relations.values())
    
    def hydrate(self, entity: Relation) -> Relation:
        """Load a relation with a pre-assigned ID from SQLite."""
        return self._hydrate_entity(entity, self._relations)


class SpyRepository(Repository[Spy]):
    """Repository for Spy entities."""
    
    def __init__(self, db_manager=None):
        """Initialize Spy repository."""
        super().__init__(db_manager)
        self._spies: dict = {}
        self._next_id = 1
    
    def create(self, entity: Spy) -> Spy:
        """Create a new spy."""
        entity.id = self._next_id
        entity.mark_updated()
        self._spies[self._next_id] = entity
        self._next_id += 1
        return entity
    
    def get(self, entity_id: int) -> Optional[Spy]:
        """Fetch spy by ID."""
        return self._spies.get(entity_id)
    
    def get_by_kingdom(self, kingdom_id: int) -> List[Spy]:
        """Fetch all spies of a kingdom."""
        return [s for s in self._spies.values() if s.kingdom_id == kingdom_id]
    
    def update(self, entity: Spy) -> Spy:
        """Update existing spy."""
        if entity.id not in self._spies:
            raise RepositoryError(f"Spy with ID {entity.id} not found")
        
        entity.mark_updated()
        self._spies[entity.id] = entity
        return entity
    
    def delete(self, entity_id: int) -> bool:
        """Delete spy by ID."""
        if entity_id in self._spies:
            del self._spies[entity_id]
            return True
        return False
    
    def list_all(self) -> List[Spy]:
        """Fetch all spies."""
        return list(self._spies.values())


class MissionRepository(Repository[Mission]):
    """Repository for Mission entities."""
    
    def __init__(self, db_manager=None):
        """Initialize Mission repository."""
        super().__init__(db_manager)
        self._missions: dict = {}
        self._next_id = 1
    
    def create(self, entity: Mission) -> Mission:
        """Create a new mission."""
        entity.id = self._next_id
        entity.mark_updated()
        self._missions[self._next_id] = entity
        self._next_id += 1
        return entity
    
    def get(self, entity_id: int) -> Optional[Mission]:
        """Fetch mission by ID."""
        return self._missions.get(entity_id)
    
    def get_active(self) -> List[Mission]:
        """Fetch all active missions."""
        return [m for m in self._missions.values() if m.status == "Active"]
    
    def update(self, entity: Mission) -> Mission:
        """Update existing mission."""
        if entity.id not in self._missions:
            raise RepositoryError(f"Mission with ID {entity.id} not found")
        
        entity.mark_updated()
        self._missions[entity.id] = entity
        return entity
    
    def delete(self, entity_id: int) -> bool:
        """Delete mission by ID."""
        if entity_id in self._missions:
            del self._missions[entity_id]
            return True
        return False
    
    def list_all(self) -> List[Mission]:
        """Fetch all missions."""
        return list(self._missions.values())

"""
Kingdom domain repository.

Provides data access for Kingdom entities.
"""

from typing import Optional, List
from warfare_simulation.persistence.repository import Repository
from warfare_simulation.core.exceptions import RepositoryError
from .models import Kingdom, Treasury


class KingdomRepository(Repository[Kingdom]):
    """
    Repository for Kingdom entities.
    
    Uses in-memory storage; hydrate from SQLite via CampaignBootstrap.load_repositories().
    """
    
    def __init__(self, db_manager=None):
        """Initialize Kingdom repository."""
        super().__init__(db_manager)
        self._kingdoms: dict = {}
        self._next_id = 1
    
    def create(self, entity: Kingdom) -> Kingdom:
        """Create a new kingdom."""
        if not entity.name:
            raise RepositoryError("Kingdom must have a name")
        
        entity.id = self._next_id
        entity.mark_updated()
        self._kingdoms[self._next_id] = entity
        self._next_id += 1
        
        return entity
    
    def get(self, entity_id: int) -> Optional[Kingdom]:
        """Fetch kingdom by ID."""
        return self._kingdoms.get(entity_id)
    
    def get_by_name(self, name: str) -> Optional[Kingdom]:
        """Fetch kingdom by name."""
        for kingdom in self._kingdoms.values():
            if kingdom.name == name:
                return kingdom
        return None
    
    def update(self, entity: Kingdom) -> Kingdom:
        """Update existing kingdom."""
        if entity.id not in self._kingdoms:
            raise RepositoryError(f"Kingdom with ID {entity.id} not found")
        
        entity.mark_updated()
        self._kingdoms[entity.id] = entity
        return entity
    
    def delete(self, entity_id: int) -> bool:
        """Delete kingdom by ID."""
        if entity_id in self._kingdoms:
            del self._kingdoms[entity_id]
            return True
        return False
    
    def list_all(self) -> List[Kingdom]:
        """Fetch all kingdoms."""
        return list(self._kingdoms.values())
    
    def hydrate(self, entity: Kingdom) -> Kingdom:
        """Load a kingdom with a pre-assigned ID from SQLite."""
        return self._hydrate_entity(entity, self._kingdoms)
    
    def get_current_kingdom(self) -> Optional[Kingdom]:
        """Get the active kingdom (first one, typically)."""
        if self._kingdoms:
            return next(iter(self._kingdoms.values()))
        return None


class TreasuryRepository(Repository[Treasury]):
    """Repository for Treasury records."""
    
    def __init__(self, db_manager=None):
        """Initialize Treasury repository."""
        super().__init__(db_manager)
        self._treasuries: dict = {}
        self._next_id = 1
    
    def create(self, entity: Treasury) -> Treasury:
        """Create a new treasury record."""
        entity.id = self._next_id
        entity.mark_updated()
        self._treasuries[self._next_id] = entity
        self._next_id += 1
        return entity
    
    def get(self, entity_id: int) -> Optional[Treasury]:
        """Fetch treasury by ID."""
        return self._treasuries.get(entity_id)
    
    def get_by_kingdom(self, kingdom_id: int) -> Optional[Treasury]:
        """Fetch treasury for a specific kingdom."""
        for treasury in self._treasuries.values():
            if treasury.kingdom_id == kingdom_id:
                return treasury
        return None
    
    def update(self, entity: Treasury) -> Treasury:
        """Update existing treasury record."""
        if entity.id not in self._treasuries:
            raise RepositoryError(f"Treasury with ID {entity.id} not found")
        
        entity.mark_updated()
        self._treasuries[entity.id] = entity
        return entity
    
    def delete(self, entity_id: int) -> bool:
        """Delete treasury by ID."""
        if entity_id in self._treasuries:
            del self._treasuries[entity_id]
            return True
        return False
    
    def list_all(self) -> List[Treasury]:
        """Fetch all treasury records."""
        return list(self._treasuries.values())

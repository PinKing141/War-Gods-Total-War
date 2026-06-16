"""
Geography domain repository.

Data access for provinces, borders, and locations.
"""

from typing import Optional, List
from warfare_simulation.persistence.repository import Repository
from warfare_simulation.core.exceptions import RepositoryError
from .models import Province, Border, Location


class ProvinceRepository(Repository[Province]):
    """Repository for Province entities."""
    
    def __init__(self, db_manager=None):
        """Initialize Province repository."""
        super().__init__(db_manager)
        self._provinces: dict = {}
        self._next_id = 1
    
    def create(self, entity: Province) -> Province:
        """Create a new province."""
        if not entity.name:
            raise RepositoryError("Province must have a name")
        
        entity.id = self._next_id
        entity.mark_updated()
        self._provinces[self._next_id] = entity
        self._next_id += 1
        return entity
    
    def get(self, entity_id: int) -> Optional[Province]:
        """Fetch province by ID."""
        return self._provinces.get(entity_id)
    
    def get_by_name(self, name: str) -> Optional[Province]:
        """Fetch province by name."""
        for province in self._provinces.values():
            if province.name == name:
                return province
        return None
    
    def get_by_kingdom(self, kingdom_id: int) -> List[Province]:
        """Fetch all provinces of a kingdom."""
        return [p for p in self._provinces.values() if p.kingdom_id == kingdom_id]
    
    def update(self, entity: Province) -> Province:
        """Update existing province."""
        if entity.id not in self._provinces:
            raise RepositoryError(f"Province with ID {entity.id} not found")
        
        entity.mark_updated()
        self._provinces[entity.id] = entity
        return entity
    
    def delete(self, entity_id: int) -> bool:
        """Delete province by ID."""
        if entity_id in self._provinces:
            del self._provinces[entity_id]
            return True
        return False
    
    def list_all(self) -> List[Province]:
        """Fetch all provinces."""
        return list(self._provinces.values())
    
    def hydrate(self, entity: Province) -> Province:
        """Load a province with a pre-assigned ID from SQLite."""
        return self._hydrate_entity(entity, self._provinces)


class BorderRepository(Repository[Border]):
    """Repository for Border entities."""
    
    def __init__(self, db_manager=None):
        """Initialize Border repository."""
        super().__init__(db_manager)
        self._borders: dict = {}
        self._next_id = 1
    
    def create(self, entity: Border) -> Border:
        """Create a new border."""
        entity.id = self._next_id
        entity.mark_updated()
        self._borders[self._next_id] = entity
        self._next_id += 1
        return entity
    
    def get(self, entity_id: int) -> Optional[Border]:
        """Fetch border by ID."""
        return self._borders.get(entity_id)
    
    def get_between_provinces(
        self, province_a_id: int, province_b_id: int
    ) -> Optional[Border]:
        """Fetch border between two provinces."""
        for border in self._borders.values():
            if (
                (border.province_a_id == province_a_id and border.province_b_id == province_b_id) or
                (border.province_a_id == province_b_id and border.province_b_id == province_a_id)
            ):
                return border
        return None
    
    def update(self, entity: Border) -> Border:
        """Update existing border."""
        if entity.id not in self._borders:
            raise RepositoryError(f"Border with ID {entity.id} not found")
        
        entity.mark_updated()
        self._borders[entity.id] = entity
        return entity
    
    def delete(self, entity_id: int) -> bool:
        """Delete border by ID."""
        if entity_id in self._borders:
            del self._borders[entity_id]
            return True
        return False
    
    def list_all(self) -> List[Border]:
        """Fetch all borders."""
        return list(self._borders.values())


class LocationRepository(Repository[Location]):
    """Repository for Location entities."""
    
    def __init__(self, db_manager=None):
        """Initialize Location repository."""
        super().__init__(db_manager)
        self._locations: dict = {}
        self._next_id = 1
    
    def create(self, entity: Location) -> Location:
        """Create a new location."""
        entity.id = self._next_id
        entity.mark_updated()
        self._locations[self._next_id] = entity
        self._next_id += 1
        return entity
    
    def get(self, entity_id: int) -> Optional[Location]:
        """Fetch location by ID."""
        return self._locations.get(entity_id)
    
    def get_by_province(self, province_id: int) -> List[Location]:
        """Fetch all locations in a province."""
        return [l for l in self._locations.values() if l.province_id == province_id]
    
    def update(self, entity: Location) -> Location:
        """Update existing location."""
        if entity.id not in self._locations:
            raise RepositoryError(f"Location with ID {entity.id} not found")
        
        entity.mark_updated()
        self._locations[entity.id] = entity
        return entity
    
    def delete(self, entity_id: int) -> bool:
        """Delete location by ID."""
        if entity_id in self._locations:
            del self._locations[entity_id]
            return True
        return False
    
    def list_all(self) -> List[Location]:
        """Fetch all locations."""
        return list(self._locations.values())

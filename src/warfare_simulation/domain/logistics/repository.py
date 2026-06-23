"""
Logistics domain repository.

Data access for resources, projects, and supply routes.
"""

from typing import Optional, List
from warfare_simulation.persistence.repository import Repository
from warfare_simulation.core.exceptions import RepositoryError
from warfare_simulation.core.constants import ResourceType
from .models import Resource, Project, SupplyRoute, ArmyMovement


class ResourceRepository(Repository[Resource]):
    """Repository for Resource entities."""
    
    def __init__(self, db_manager=None):
        """Initialize Resource repository."""
        super().__init__(db_manager)
        self._resources: dict = {}
        self._next_id = 1
    
    def create(self, entity: Resource) -> Resource:
        """Create a new resource."""
        entity.id = self._next_id
        entity.mark_updated()
        self._resources[self._next_id] = entity
        self._next_id += 1
        return entity
    
    def get(self, entity_id: int) -> Optional[Resource]:
        """Fetch resource by ID."""
        return self._resources.get(entity_id)
    
    def get_by_kingdom_and_type(
        self, kingdom_id: int, resource_type: ResourceType
    ) -> Optional[Resource]:
        """Fetch resource of specific type for kingdom."""
        for resource in self._resources.values():
            if resource.kingdom_id == kingdom_id and resource.resource_type == resource_type:
                return resource
        return None
    
    def get_by_kingdom(self, kingdom_id: int) -> List[Resource]:
        """Fetch all resources of a kingdom."""
        return [r for r in self._resources.values() if r.kingdom_id == kingdom_id]
    
    def update(self, entity: Resource) -> Resource:
        """Update existing resource."""
        if entity.id not in self._resources:
            raise RepositoryError(f"Resource with ID {entity.id} not found")
        
        entity.mark_updated()
        self._resources[entity.id] = entity
        self._persist_update(entity)
        return entity
    
    def delete(self, entity_id: int) -> bool:
        """Delete resource by ID."""
        if entity_id in self._resources:
            del self._resources[entity_id]
            return True
        return False
    
    def list_all(self) -> List[Resource]:
        """Fetch all resources."""
        return list(self._resources.values())
    
    def hydrate(self, entity: Resource) -> Resource:
        """Load a resource with a pre-assigned ID from SQLite."""
        return self._hydrate_entity(entity, self._resources)

    def _persist_update(self, entity: Resource) -> None:
        """Persist mutable resource turn state to SQLite when a DB is attached."""
        if self.db_manager is None or not self.db_manager.conn:
            return

        self.db_manager.execute(
            """
            UPDATE resource
            SET resource_type = ?, stored = ?, monthly_production = ?,
                monthly_consumption = ?, max_storage = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                entity.resource_type.name,
                entity.stored,
                entity.monthly_production,
                entity.monthly_consumption,
                entity.max_storage,
                entity.id,
            ),
        )
        self.db_manager.commit()


class ProjectRepository(Repository[Project]):
    """Repository for Project entities."""
    
    def __init__(self, db_manager=None):
        """Initialize Project repository."""
        super().__init__(db_manager)
        self._projects: dict = {}
        self._next_id = 1
    
    def create(self, entity: Project) -> Project:
        """Create a new project."""
        if not entity.name:
            raise RepositoryError("Project must have a name")
        
        entity.id = self._next_id
        entity.mark_updated()
        self._projects[self._next_id] = entity
        self._next_id += 1
        return entity
    
    def get(self, entity_id: int) -> Optional[Project]:
        """Fetch project by ID."""
        return self._projects.get(entity_id)
    
    def get_by_kingdom(self, kingdom_id: int) -> List[Project]:
        """Fetch all projects of a kingdom."""
        return [p for p in self._projects.values() if p.kingdom_id == kingdom_id]
    
    def get_active(self) -> List[Project]:
        """Fetch all active projects."""
        return [p for p in self._projects.values() if not p.is_complete()]
    
    def update(self, entity: Project) -> Project:
        """Update existing project."""
        if entity.id not in self._projects:
            raise RepositoryError(f"Project with ID {entity.id} not found")
        
        entity.mark_updated()
        self._projects[entity.id] = entity
        return entity
    
    def delete(self, entity_id: int) -> bool:
        """Delete project by ID."""
        if entity_id in self._projects:
            del self._projects[entity_id]
            return True
        return False
    
    def list_all(self) -> List[Project]:
        """Fetch all projects."""
        return list(self._projects.values())


class SupplyRouteRepository(Repository[SupplyRoute]):
    """Repository for SupplyRoute entities."""
    
    def __init__(self, db_manager=None):
        """Initialize SupplyRoute repository."""
        super().__init__(db_manager)
        self._routes: dict = {}
        self._next_id = 1
    
    def create(self, entity: SupplyRoute) -> SupplyRoute:
        """Create a new supply route."""
        if not entity.name:
            raise RepositoryError("Route must have a name")
        
        entity.id = self._next_id
        entity.mark_updated()
        self._routes[self._next_id] = entity
        self._next_id += 1
        return entity
    
    def get(self, entity_id: int) -> Optional[SupplyRoute]:
        """Fetch route by ID."""
        return self._routes.get(entity_id)
    
    def get_by_kingdom(self, kingdom_id: int) -> List[SupplyRoute]:
        """Fetch all routes of a kingdom."""
        return [r for r in self._routes.values() if r.kingdom_id == kingdom_id]
    
    def get_active(self) -> List[SupplyRoute]:
        """Fetch all active routes."""
        return [r for r in self._routes.values() if r.is_active]
    
    def update(self, entity: SupplyRoute) -> SupplyRoute:
        """Update existing route."""
        if entity.id not in self._routes:
            raise RepositoryError(f"Route with ID {entity.id} not found")
        
        entity.mark_updated()
        self._routes[entity.id] = entity
        return entity
    
    def delete(self, entity_id: int) -> bool:
        """Delete route by ID."""
        if entity_id in self._routes:
            del self._routes[entity_id]
            return True
        return False
    
    def list_all(self) -> List[SupplyRoute]:
        """Fetch all routes."""
        return list(self._routes.values())

class ArmyMovementRepository(Repository[ArmyMovement]):
    """In-memory repository for active army movement plans."""

    def __init__(self, db_manager=None):
        """Initialize army movement repository."""
        super().__init__(db_manager)
        self._movements: dict = {}
        self._next_id = 1

    def create(self, entity: ArmyMovement) -> ArmyMovement:
        """Create a new movement plan."""
        if not entity.army_name:
            raise RepositoryError("Army movement must have an army name")
        if len(entity.route) < 2:
            raise RepositoryError(
                "Army movement route must include at least origin and destination"
            )
        entity.id = self._next_id
        entity.mark_updated()
        self._movements[self._next_id] = entity
        self._next_id += 1
        return entity

    def get(self, entity_id: int) -> Optional[ArmyMovement]:
        """Fetch movement by ID."""
        return self._movements.get(entity_id)

    def update(self, entity: ArmyMovement) -> ArmyMovement:
        """Update an existing movement plan."""
        if entity.id not in self._movements:
            raise RepositoryError(f"Army movement with ID {entity.id} not found")
        entity.mark_updated()
        self._movements[entity.id] = entity
        return entity

    def delete(self, entity_id: int) -> bool:
        """Delete movement by ID."""
        if entity_id in self._movements:
            del self._movements[entity_id]
            return True
        return False

    def list_all(self) -> List[ArmyMovement]:
        """Fetch all movement plans."""
        return list(self._movements.values())

    def get_active(self) -> List[ArmyMovement]:
        """Fetch movement plans that are still marching."""
        return [m for m in self._movements.values() if m.status == "marching"]

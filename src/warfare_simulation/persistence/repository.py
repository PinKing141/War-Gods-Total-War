"""
Generic Repository base class for data access.

All domain repositories inherit from this class to provide consistent CRUD operations
and query patterns. This decouples business logic from data access implementation.

The Repository pattern provides:
- Abstraction layer between domain and persistence
- Easy testing (mock repositories)
- Easy switching databases (just inherit and override methods)
- Consistent interface across all domains
"""

from abc import ABC, abstractmethod
from typing import Dict, Generic, List, Optional, TypeVar, Any
from datetime import datetime

T = TypeVar('T')  # Generic type for any entity


class Repository(ABC, Generic[T]):
    """
    Abstract base repository class for all domain repositories.
    
    All repositories should inherit from this class and implement:
    - create(): Insert a new entity
    - get(): Fetch entity by ID
    - update(): Update existing entity
    - delete(): Remove entity
    - list_all(): Fetch all entities
    
    Domain repositories can add custom query methods as needed.
    """
    
    def __init__(self, db_manager=None):
        """
        Initialize repository.
        
        Args:
            db_manager: DatabaseManager instance (optional for initial setup)
        """
        self.db_manager = db_manager
        self._cache: Dict[int, T] = {}  # Simple in-memory cache
    
    # ========================================================================
    # CORE CRUD OPERATIONS
    # ========================================================================
    
    @abstractmethod
    def create(self, entity: T) -> T:
        """
        Create (insert) a new entity in the database.
        
        Args:
            entity: Entity to create
        
        Returns:
            Entity with assigned ID
        
        Raises:
            RepositoryError: If entity already exists or insert fails
        """
        pass
    
    @abstractmethod
    def get(self, entity_id: int) -> Optional[T]:
        """
        Fetch an entity by ID.
        
        Args:
            entity_id: ID of entity to fetch
        
        Returns:
            Entity if found, None otherwise
        
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    def update(self, entity: T) -> T:
        """
        Update an existing entity in the database.
        
        Args:
            entity: Entity with updated values (must have ID)
        
        Returns:
            Updated entity
        
        Raises:
            RepositoryError: If entity not found or update fails
        """
        pass
    
    @abstractmethod
    def delete(self, entity_id: int) -> bool:
        """
        Delete an entity from the database.
        
        Args:
            entity_id: ID of entity to delete
        
        Returns:
            True if deleted, False if not found
        
        Raises:
            RepositoryError: If delete fails
        """
        pass
    
    @abstractmethod
    def list_all(self) -> List[T]:
        """
        Fetch all entities of this type from the database.
        
        Returns:
            List of all entities (empty list if none found)
        
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    # ========================================================================
    # CACHE MANAGEMENT
    # ========================================================================
    
    def get_cached(self, entity_id: int) -> Optional[T]:
        """
        Fetch entity from in-memory cache (for performance).
        
        Args:
            entity_id: ID of entity to fetch
        
        Returns:
            Cached entity if available, None otherwise
        """
        return self._cache.get(entity_id)
    
    def cache_put(self, entity_id: int, entity: T) -> None:
        """
        Store entity in in-memory cache.
        
        Args:
            entity_id: ID to cache under
            entity: Entity to cache
        """
        self._cache[entity_id] = entity
    
    def cache_clear(self) -> None:
        """Clear entire in-memory cache."""
        self._cache.clear()
    
    def cache_remove(self, entity_id: int) -> None:
        """Remove specific entity from cache."""
        self._cache.pop(entity_id, None)
    
    # ========================================================================
    # BATCH OPERATIONS
    # ========================================================================
    
    def create_many(self, entities: List[T]) -> List[T]:
        """
        Create multiple entities in a transaction.
        
        Args:
            entities: List of entities to create
        
        Returns:
            List of created entities with assigned IDs
        
        Raises:
            RepositoryError: If any insert fails (transaction rolls back)
        """
        results = []
        for entity in entities:
            results.append(self.create(entity))
        return results
    
    def update_many(self, entities: List[T]) -> List[T]:
        """
        Update multiple entities in a transaction.
        
        Args:
            entities: List of entities to update
        
        Returns:
            List of updated entities
        
        Raises:
            RepositoryError: If any update fails (transaction rolls back)
        """
        results = []
        for entity in entities:
            results.append(self.update(entity))
        return results
    
    def delete_many(self, entity_ids: List[int]) -> int:
        """
        Delete multiple entities in a transaction.
        
        Args:
            entity_ids: List of IDs to delete
        
        Returns:
            Number of entities deleted
        
        Raises:
            RepositoryError: If any delete fails (transaction rolls back)
        """
        count = 0
        for entity_id in entity_ids:
            if self.delete(entity_id):
                count += 1
        return count
    
    # ========================================================================
    # QUERY UTILITIES
    # ========================================================================
    
    def exists(self, entity_id: int) -> bool:
        """
        Check if an entity exists.
        
        Args:
            entity_id: ID to check
        
        Returns:
            True if entity exists, False otherwise
        """
        return self.get(entity_id) is not None
    
    def count(self) -> int:
        """
        Count total entities of this type.
        
        Returns:
            Total number of entities
        """
        return len(self.list_all())
    
    def is_empty(self) -> bool:
        """Check if repository has any entities."""
        return self.count() == 0
    
    def _hydrate_entity(self, entity: T, storage: Dict[int, T], next_id_attr: str = "_next_id") -> T:
        """
        Load an entity with a pre-assigned ID (e.g. from SQLite).
        
        Subclasses call this from hydrate() to preserve database IDs in memory.
        """
        storage[entity.id] = entity
        current_next = getattr(self, next_id_attr)
        if entity.id >= current_next:
            setattr(self, next_id_attr, entity.id + 1)
        return entity


class InMemoryRepository(Repository[T]):
    """
    Simple in-memory repository implementation for testing.
    
    Stores entities in a dictionary. Useful for unit tests and
    prototyping before database implementation.
    """
    
    def __init__(self):
        """Initialize in-memory repository."""
        super().__init__()
        self._storage: Dict[int, T] = {}
        self._next_id = 1
    
    def create(self, entity: T) -> T:
        """Create entity with auto-incremented ID."""
        entity.id = self._next_id
        entity.created_at = datetime.now()
        entity.updated_at = datetime.now()
        self._storage[self._next_id] = entity
        self._next_id += 1
        return entity
    
    def get(self, entity_id: int) -> Optional[T]:
        """Fetch entity by ID."""
        return self._storage.get(entity_id)
    
    def update(self, entity: T) -> T:
        """Update existing entity."""
        if entity.id not in self._storage:
            raise KeyError(f"Entity with ID {entity.id} not found")
        entity.updated_at = datetime.now()
        self._storage[entity.id] = entity
        return entity
    
    def delete(self, entity_id: int) -> bool:
        """Delete entity by ID."""
        if entity_id in self._storage:
            del self._storage[entity_id]
            return True
        return False
    
    def list_all(self) -> List[T]:
        """Fetch all entities."""
        return list(self._storage.values())

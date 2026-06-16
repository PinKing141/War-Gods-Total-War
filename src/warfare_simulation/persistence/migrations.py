"""
Database migration framework.

Manages versioned schema migrations for database updates.
"""

from typing import List, Callable
from warfare_simulation.core.logger import get_logger
from warfare_simulation.core.exceptions import DatabaseError
from .database import DatabaseManager


logger = get_logger(__name__)


class Migration:
    """Represents a single database migration."""
    
    def __init__(self, version: int, name: str, up: Callable, down: Callable):
        """
        Initialize migration.
        
        Args:
            version: Migration version number (e.g., 1, 2, 3)
            name: Human-readable migration name
            up: Function to apply migration (takes DatabaseManager)
            down: Function to revert migration (takes DatabaseManager)
        """
        self.version = version
        self.name = name
        self.up = up
        self.down = down
    
    def apply(self, db: DatabaseManager) -> None:
        """Apply migration."""
        try:
            self.up(db)
            logger.info(f"Migration {self.version}: {self.name} applied")
        except Exception as e:
            logger.error(f"Migration {self.version} failed: {e}")
            raise
    
    def revert(self, db: DatabaseManager) -> None:
        """Revert migration."""
        try:
            self.down(db)
            logger.info(f"Migration {self.version}: {self.name} reverted")
        except Exception as e:
            logger.error(f"Migration {self.version} revert failed: {e}")
            raise


class MigrationManager:
    """Manages database migrations."""
    
    def __init__(self, db: DatabaseManager):
        """
        Initialize migration manager.
        
        Args:
            db: Database manager instance
        """
        self.db = db
        self.migrations: List[Migration] = []
    
    def register(self, migration: Migration) -> None:
        """
        Register a migration.
        
        Args:
            migration: Migration to register
        """
        self.migrations.append(migration)
        self.migrations.sort(key=lambda m: m.version)
    
    def get_current_version(self) -> int:
        """
        Get current database schema version.
        
        Returns:
            Current version number (0 if no migrations applied)
        """
        try:
            # Check if migration table exists
            if not self.db.table_exists("migration"):
                return 0
            
            cursor = self.db.execute(
                "SELECT MAX(version) FROM migration"
            )
            result = cursor.fetchone()
            return result[0] if result[0] is not None else 0
        except Exception as e:
            logger.warning(f"Could not determine current version: {e}")
            return 0
    
    def get_applied_migrations(self) -> List[int]:
        """
        Get list of applied migration versions.
        
        Returns:
            List of version numbers
        """
        try:
            if not self.db.table_exists("migration"):
                return []
            
            cursor = self.db.execute(
                "SELECT version FROM migration ORDER BY version"
            )
            return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.warning(f"Could not get applied migrations: {e}")
            return []
    
    def migrate_up(self) -> None:
        """Apply all pending migrations."""
        current_version = self.get_current_version()
        applied_versions = set(self.get_applied_migrations())
        
        pending = [m for m in self.migrations if m.version > current_version]
        
        if not pending:
            logger.info("Database is up to date")
            return
        
        logger.info(f"Applying {len(pending)} pending migrations...")
        
        for migration in pending:
            try:
                migration.apply(self.db)
                
                # Record migration in database
                self.db.execute(
                    "INSERT INTO migration (version, name) VALUES (?, ?)",
                    (migration.version, migration.name)
                )
                self.db.commit()
                
            except Exception as e:
                self.db.rollback()
                raise DatabaseError(f"Migration failed: {e}")
        
        logger.info("All pending migrations applied successfully")
    
    def migrate_down(self, target_version: int = 0) -> None:
        """
        Revert migrations down to target version.
        
        Args:
            target_version: Version to revert to (default 0 = no migrations)
        """
        applied_versions = self.get_applied_migrations()
        to_revert = [v for v in reversed(applied_versions) if v > target_version]
        
        if not to_revert:
            logger.info("No migrations to revert")
            return
        
        logger.info(f"Reverting {len(to_revert)} migrations...")
        
        for version in to_revert:
            migration = next((m for m in self.migrations if m.version == version), None)
            if not migration:
                raise DatabaseError(f"Migration {version} not found")
            
            try:
                migration.revert(self.db)
                
                # Remove from migration table
                self.db.execute(
                    "DELETE FROM migration WHERE version = ?",
                    (version,)
                )
                self.db.commit()
                
            except Exception as e:
                self.db.rollback()
                raise DatabaseError(f"Migration revert failed: {e}")
        
        logger.info("All migrations reverted successfully")

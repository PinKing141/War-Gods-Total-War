"""
Database manager and SQLite integration.

Handles database initialization, schema management, and migrations.
"""

import sqlite3
from pathlib import Path
from typing import Optional

from warfare_simulation.core.logger import get_logger
from warfare_simulation.core.exceptions import DatabaseError


logger = get_logger(__name__)


class DatabaseManager:
    """Manages SQLite database connection and schema."""
    
    def __init__(self, db_path: str = "war_sim.db"):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        logger.info(f"DatabaseManager initialized with db_path: {db_path}")
    
    def connect(self) -> sqlite3.Connection:
        """
        Establish database connection.
        
        Returns:
            SQLite connection object
        
        Raises:
            DatabaseError: If connection fails
        """
        try:
            self.conn = sqlite3.connect(self.db_path)
            # Enable foreign keys
            self.conn.execute("PRAGMA foreign_keys = ON")
            logger.info(f"Database connected: {self.db_path}")
            return self.conn
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to connect to database: {e}")
    
    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
    
    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """
        Execute SQL query.
        
        Args:
            query: SQL query string
            params: Query parameters
        
        Returns:
            Cursor with query results
        
        Raises:
            DatabaseError: If query fails
        """
        if not self.conn:
            raise DatabaseError("Database not connected")
        
        try:
            return self.conn.execute(query, params)
        except sqlite3.Error as e:
            raise DatabaseError(f"Query failed: {e}")
    
    def commit(self) -> None:
        """Commit transaction."""
        if self.conn:
            self.conn.commit()
    
    def rollback(self) -> None:
        """Rollback transaction."""
        if self.conn:
            self.conn.rollback()

    def _ensure_column(self, table_name: str, column_name: str, definition: str) -> None:
        """Add a missing column to an existing table."""
        cursor = self.execute(f"PRAGMA table_info({table_name})")
        existing_columns = {row[1] for row in cursor.fetchall()}
        if column_name not in existing_columns:
            self.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")
    
    def initialize_schema(self) -> None:
        """
        Create database schema (tables).
        
        Raises:
            DatabaseError: If schema creation fails
        """
        try:
            self.execute("""
                CREATE TABLE IF NOT EXISTS kingdom (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    ruler_name TEXT NOT NULL,
                    population INTEGER NOT NULL,
                    treasury_silver INTEGER NOT NULL,
                    monthly_income INTEGER NOT NULL,
                    monthly_expenses INTEGER NOT NULL,
                    morale INTEGER DEFAULT 75,
                    loyalty INTEGER DEFAULT 75,
                    grain_stores INTEGER DEFAULT 0,
                    current_day INTEGER DEFAULT 1,
                    current_turn INTEGER DEFAULT 1,
                    current_month INTEGER DEFAULT 1,
                    current_year INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            self._ensure_column("kingdom", "current_day", "INTEGER DEFAULT 1")
            
            self.execute("""
                CREATE TABLE IF NOT EXISTS province (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kingdom_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    population INTEGER NOT NULL,
                    fort_level INTEGER DEFAULT 0,
                    food_stored INTEGER DEFAULT 0,
                    monthly_tax INTEGER DEFAULT 0,
                    loyalty INTEGER DEFAULT 75,
                    garrison_size INTEGER DEFAULT 0,
                    garrison_capacity INTEGER NOT NULL,
                    governor_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(kingdom_id) REFERENCES kingdom(id),
                    UNIQUE(kingdom_id, name)
                )
            """)
            
            self.execute("""
                CREATE TABLE IF NOT EXISTS unit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kingdom_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    unit_type TEXT NOT NULL,
                    soldiers INTEGER NOT NULL,
                    veterans INTEGER DEFAULT 0,
                    morale INTEGER DEFAULT 75,
                    fatigue INTEGER DEFAULT 0,
                    armor TEXT NOT NULL,
                    location_id INTEGER NOT NULL,
                    commander_id INTEGER,
                    status TEXT DEFAULT 'ACTIVE',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(kingdom_id) REFERENCES kingdom(id)
                )
            """)
            
            self.execute("""
                CREATE TABLE IF NOT EXISTS commander (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kingdom_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    role TEXT NOT NULL,
                    leadership INTEGER DEFAULT 50,
                    tactics INTEGER DEFAULT 50,
                    logistics INTEGER DEFAULT 50,
                    loyalty INTEGER DEFAULT 75,
                    status TEXT DEFAULT 'Active',
                    traits TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(kingdom_id) REFERENCES kingdom(id)
                )
            """)
            
            self.execute("""
                CREATE TABLE IF NOT EXISTS faction (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    faction_type TEXT NOT NULL,
                    government_type TEXT,
                    power_level INTEGER DEFAULT 50,
                    wealth INTEGER DEFAULT 50,
                    stability INTEGER DEFAULT 50,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.execute("""
                CREATE TABLE IF NOT EXISTS relation (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    faction_a_id INTEGER NOT NULL,
                    faction_b_id INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    opinion INTEGER DEFAULT 0,
                    trust INTEGER DEFAULT 0,
                    trade_agreement BOOLEAN DEFAULT 0,
                    military_alliance BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(faction_a_id) REFERENCES faction(id),
                    FOREIGN KEY(faction_b_id) REFERENCES faction(id)
                )
            """)
            
            self.execute("""
                CREATE TABLE IF NOT EXISTS resource (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kingdom_id INTEGER NOT NULL,
                    resource_type TEXT NOT NULL,
                    stored INTEGER NOT NULL,
                    monthly_production INTEGER DEFAULT 0,
                    monthly_consumption INTEGER DEFAULT 0,
                    max_storage INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(kingdom_id) REFERENCES kingdom(id),
                    UNIQUE(kingdom_id, resource_type)
                )
            """)
            
            self.execute("""
                CREATE TABLE IF NOT EXISTS event (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    turn INTEGER NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT NOT NULL,
                    impact TEXT,
                    affected_entities TEXT,
                    day INTEGER DEFAULT 1,
                    month INTEGER DEFAULT 1,
                    year INTEGER DEFAULT 1,
                    actor TEXT DEFAULT 'system',
                    target TEXT DEFAULT '',
                    source_system TEXT DEFAULT 'System',
                    cause_chain TEXT,
                    effect_summary TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self._ensure_column("event", "day", "INTEGER DEFAULT 1")
            self._ensure_column("event", "month", "INTEGER DEFAULT 1")
            self._ensure_column("event", "year", "INTEGER DEFAULT 1")
            self._ensure_column("event", "actor", "TEXT DEFAULT 'system'")
            self._ensure_column("event", "target", "TEXT DEFAULT ''")
            self._ensure_column("event", "source_system", "TEXT DEFAULT 'System'")
            self._ensure_column("event", "cause_chain", "TEXT")
            self._ensure_column("event", "effect_summary", "TEXT DEFAULT ''")

            self.execute("""
                CREATE TABLE IF NOT EXISTS turn_summary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    turn INTEGER NOT NULL,
                    month INTEGER NOT NULL,
                    year INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    narrative TEXT NOT NULL,
                    event_count INTEGER NOT NULL,
                    audit_count INTEGER NOT NULL,
                    highlights TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            self.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    turn INTEGER NOT NULL,
                    month INTEGER NOT NULL,
                    year INTEGER NOT NULL,
                    actor TEXT NOT NULL,
                    target TEXT NOT NULL,
                    system TEXT NOT NULL,
                    action TEXT NOT NULL,
                    previous_value TEXT,
                    new_value TEXT,
                    reason TEXT,
                    source_event_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(source_event_id) REFERENCES event(id)
                )
            """)
            


            self.execute("""
                CREATE TABLE IF NOT EXISTS observer_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    turn INTEGER NOT NULL,
                    day INTEGER NOT NULL,
                    month INTEGER NOT NULL,
                    year INTEGER NOT NULL,
                    stream TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    target TEXT NOT NULL,
                    source_system TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    details TEXT,
                    source_event_id INTEGER,
                    source_audit_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(source_event_id) REFERENCES event(id),
                    FOREIGN KEY(source_audit_id) REFERENCES audit_log(id)
                )
            """)

            self.execute("""
                CREATE TABLE IF NOT EXISTS scheduled_event (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT UNIQUE NOT NULL,
                    due_day INTEGER NOT NULL,
                    due_month INTEGER NOT NULL,
                    due_year INTEGER NOT NULL,
                    event_type TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    target TEXT NOT NULL,
                    payload TEXT DEFAULT '{}',
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            self.execute("""
                CREATE TABLE IF NOT EXISTS migration (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version INTEGER NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.commit()
            logger.info("Database schema initialized successfully")
            
        except sqlite3.Error as e:
            self.rollback()
            raise DatabaseError(f"Failed to initialize schema: {e}")
    
    def table_exists(self, table_name: str) -> bool:
        """
        Check if table exists.
        
        Args:
            table_name: Name of table to check
        
        Returns:
            True if table exists, False otherwise
        """
        try:
            cursor = self.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,)
            )
            return cursor.fetchone() is not None
        except sqlite3.Error:
            return False

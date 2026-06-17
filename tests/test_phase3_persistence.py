"""
Test Phase 3 - Data & Persistence.

Verifies configuration loading and database initialization.
"""

import sys
import os
from pathlib import Path
import tempfile
import shutil

# Add src to path
workspace_root = Path(__file__).resolve().parents[1]
src_path = workspace_root / "src"
sys.path.insert(0, str(src_path))

from warfare_simulation.config import ConfigManager
from warfare_simulation.persistence import DatabaseManager, MigrationManager, Migration
from warfare_simulation.persistence.campaign_bootstrap import CampaignBootstrap
from warfare_simulation.core.logger import get_logger


logger = get_logger(__name__)


def test_config_loading():
    """Test configuration loading and validation."""
    print("\n=== Testing Config Loading ===")
    
    # Get default config directory
    config_dir = workspace_root / "src" / "warfare_simulation" / "config" / "data"
    
    config_mgr = ConfigManager(str(config_dir))
    
    # Load all configs
    print("Loading kingdom config...")
    kingdom_config = config_mgr.load_kingdom_config()
    assert kingdom_config.kingdom.name == "The Dominion of Auster"
    assert kingdom_config.kingdom.population == 450000
    print(f"[OK] Kingdom loaded: {kingdom_config.kingdom.name}")
    
    print("Loading provinces config...")
    provinces_config = config_mgr.load_provinces_config()
    assert len(provinces_config.provinces) == 4
    assert provinces_config.provinces[0].name == "Highreach (Capital)"
    print(f"[OK] Provinces loaded: {len(provinces_config.provinces)} provinces")
    
    print("Loading units config...")
    units_config = config_mgr.load_units_config()
    assert len(units_config.units) == 3
    assert units_config.units[0].soldiers == 500
    print(f"[OK] Units loaded: {len(units_config.units)} units")
    
    print("Loading commanders config...")
    commanders_config = config_mgr.load_commanders_config()
    assert len(commanders_config.commanders) == 3
    assert commanders_config.commanders[0].name == "General Marcus Thorn"
    print(f"[OK] Commanders loaded: {len(commanders_config.commanders)} commanders")
    
    print("Loading diplomacy config...")
    diplomacy_config = config_mgr.load_diplomacy_config()
    assert len(diplomacy_config.factions) == 3
    assert len(diplomacy_config.relations) == 3
    print(f"[OK] Diplomacy loaded: {len(diplomacy_config.factions)} factions, {len(diplomacy_config.relations)} relations")
    
    print("Loading resources config...")
    resources_config = config_mgr.load_resources_config()
    assert len(resources_config.resources) == 4
    assert resources_config.resources[0].resource_type == "FOOD"
    print(f"[OK] Resources loaded: {len(resources_config.resources)} resources")
    
    print("Loading all configs at once...")
    all_configs = config_mgr.load_all_configs()
    assert len(all_configs) == 6
    print(f"[OK] All configs loaded successfully")


def test_database_initialization():
    """Test database initialization and schema creation."""
    print("\n=== Testing Database Initialization ===")
    
    # Create temporary database for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        
        print(f"Creating database at {db_path}...")
        db = DatabaseManager(db_path)
        
        # Connect
        print("Connecting to database...")
        conn = db.connect()
        assert conn is not None
        print("[OK] Database connected")
        
        # Initialize schema
        print("Initializing schema...")
        db.initialize_schema()
        print("[OK] Schema initialized")
        
        # Verify tables exist
        print("Verifying tables...")
        assert db.table_exists("kingdom"), "kingdom table not found"
        assert db.table_exists("province"), "province table not found"
        assert db.table_exists("unit"), "unit table not found"
        assert db.table_exists("commander"), "commander table not found"
        assert db.table_exists("faction"), "faction table not found"
        assert db.table_exists("relation"), "relation table not found"
        assert db.table_exists("resource"), "resource table not found"
        assert db.table_exists("event"), "event table not found"
        assert db.table_exists("migration"), "migration table not found"
        print("[OK] All tables created successfully")
        
        # Test insert
        print("Testing insert...")
        db.execute(
            "INSERT INTO kingdom (name, ruler_name, population, treasury_silver, monthly_income, monthly_expenses) VALUES (?, ?, ?, ?, ?, ?)",
            ("Test Kingdom", "Test Ruler", 100000, 10000, 1000, 500)
        )
        db.commit()
        
        # Test query
        cursor = db.execute("SELECT * FROM kingdom WHERE name = ?", ("Test Kingdom",))
        row = cursor.fetchone()
        assert row is not None
        assert row[1] == "Test Kingdom"  # name column
        print("[OK] Insert and query working")
        
        # Close
        db.close()
        print("[OK] Database closed successfully")


def test_campaign_seeding():
    """Test JSON config seeds SQLite and hydrates repositories."""
    print("\n=== Testing Campaign Seeding ===")

    config_dir = workspace_root / "src" / "warfare_simulation" / "config" / "data"
    config_mgr = ConfigManager(str(config_dir))

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "seed_test.db")
        db = DatabaseManager(db_path)
        db.connect()
        db.initialize_schema()

        kingdom_id = CampaignBootstrap.seed_from_config(config_mgr, db)
        assert kingdom_id == 1

        cursor = db.execute("SELECT COUNT(*) FROM kingdom")
        assert cursor.fetchone()[0] == 1

        cursor = db.execute("SELECT COUNT(*) FROM province")
        assert cursor.fetchone()[0] == 4

        cursor = db.execute("SELECT COUNT(*) FROM unit")
        assert cursor.fetchone()[0] == 3

        cursor = db.execute("SELECT COUNT(*) FROM commander")
        assert cursor.fetchone()[0] == 3

        cursor = db.execute("SELECT COUNT(*) FROM faction")
        assert cursor.fetchone()[0] == 3

        cursor = db.execute("SELECT COUNT(*) FROM relation")
        assert cursor.fetchone()[0] == 3

        cursor = db.execute("SELECT COUNT(*) FROM resource")
        assert cursor.fetchone()[0] == 4

        print("[OK] SQLite seeded with expected row counts")

        kingdom_id_2 = CampaignBootstrap.seed_from_config(config_mgr, db)
        assert kingdom_id_2 == kingdom_id
        cursor = db.execute("SELECT COUNT(*) FROM kingdom")
        assert cursor.fetchone()[0] == 1
        print("[OK] Seeding is idempotent")

        repos = CampaignBootstrap.load_repositories(db)
        kingdom = repos.kingdom.get(kingdom_id)
        assert kingdom.name == "The Dominion of Auster"
        assert len(repos.province.list_all()) == 4
        assert len(repos.unit.list_all()) == 3
        assert len(repos.commander.list_all()) == 3
        assert len(repos.faction.list_all()) == 3
        assert len(repos.relation.list_all()) == 3
        assert len(repos.resource.list_all()) == 4
        print("[OK] Repositories hydrated from SQLite")

        db.close()


def test_campaign_force_reseed_remaps_relation_ids_after_deleted_factions():
    """Force reseeding should not assume config faction IDs match SQLite row IDs."""
    print("\n=== Testing Campaign Force Reseed Relation ID Mapping ===")

    config_dir = workspace_root / "src" / "warfare_simulation" / "config" / "data"
    config_mgr = ConfigManager(str(config_dir))

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "force_seed_test.db")
        db = DatabaseManager(db_path)
        db.connect()
        db.initialize_schema()

        CampaignBootstrap.seed_from_config(config_mgr, db)
        CampaignBootstrap.seed_from_config(config_mgr, db, force=True)

        faction_ids = {
            row[0] for row in db.execute("SELECT id FROM faction").fetchall()
        }
        relation_faction_ids = {
            faction_id
            for row in db.execute(
                "SELECT faction_a_id, faction_b_id FROM relation"
            ).fetchall()
            for faction_id in row
        }

        assert len(faction_ids) == 3
        assert len(relation_faction_ids) == 3
        assert relation_faction_ids == faction_ids
        print("[OK] Force reseed relations reference the newly inserted factions")

        db.close()


def test_migrations():
    """Test migration system."""
    print("\n=== Testing Migrations ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_migrations.db")
        
        db = DatabaseManager(db_path)
        db.connect()
        db.initialize_schema()
        
        mgr = MigrationManager(db)
        
        # Define test migrations
        def migration_1_up(db):
            db.execute("""
                ALTER TABLE kingdom ADD COLUMN test_field TEXT DEFAULT 'test'
            """)
            db.commit()
        
        def migration_1_down(db):
            # SQLite doesn't support DROP COLUMN easily, so we'll just log
            pass
        
        migration_1 = Migration(1, "Add test field", migration_1_up, migration_1_down)
        mgr.register(migration_1)
        
        # Check initial version
        print("Checking initial version...")
        version = mgr.get_current_version()
        assert version == 0, f"Expected version 0, got {version}"
        print(f"[OK] Initial version: {version}")
        
        # Apply migrations
        print("Applying migrations...")
        mgr.migrate_up()
        print("[OK] Migrations applied")
        
        # Check new version
        print("Checking new version...")
        version = mgr.get_current_version()
        assert version == 1, f"Expected version 1, got {version}"
        print(f"[OK] New version: {version}")
        
        # Check applied migrations
        print("Checking applied migrations...")
        applied = mgr.get_applied_migrations()
        assert 1 in applied
        print(f"[OK] Applied migrations: {applied}")
        
        db.close()


def run_all_tests():
    """Run all Phase 3 tests."""
    print("=" * 70)
    print("PHASE 3 - DATA & PERSISTENCE TEST SUITE")
    print("=" * 70)
    
    try:
        test_config_loading()
        test_database_initialization()
        test_campaign_seeding()
        test_campaign_force_reseed_remaps_relation_ids_after_deleted_factions()
        test_migrations()
        
        print("\n" + "=" * 70)
        print("[OK] ALL PHASE 3 TESTS PASSED!")
        print("=" * 70)
        return True
        
    except Exception as e:
        print("\n" + "=" * 70)
        print(f"[FAIL] TEST FAILED: {e}")
        print("=" * 70)
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

"""
Test Phase 2 domain implementations.

Verifies all 6 domains import successfully and work together.
"""

import sys
from pathlib import Path

# Add src to path so we can import warfare_simulation
workspace_root = Path(__file__).parent
src_path = workspace_root / "src"
sys.path.insert(0, str(src_path))

from warfare_simulation.core.constants import (
    UnitType, ArmorType, CommanderRole, FactionStatus, 
    EventCategory, ResourceType, ProjectType
)
from warfare_simulation.core.exceptions import ValidationError
from warfare_simulation.core.validation import ValidationService


def test_kingdom_domain():
    """Test Kingdom domain imports and basic usage."""
    print("Testing Kingdom domain...")
    from warfare_simulation.domain.kingdom.models import Kingdom, Treasury
    from warfare_simulation.domain.kingdom.repository import KingdomRepository, TreasuryRepository
    from warfare_simulation.domain.kingdom.service import KingdomService
    
    # Create repositories
    kingdom_repo = KingdomRepository()
    treasury_repo = TreasuryRepository()
    validator = ValidationService()
    
    # Create service
    service = KingdomService(kingdom_repo, validator)
    service.initialize()
    
    # Create kingdom
    kingdom = service.create_kingdom(
        name="Westeros",
        ruler_name="Jon Snow",
        initial_population=50000,
        initial_treasury=10000,
        monthly_income=1000,
        monthly_expenses=500,
    )
    
    assert kingdom.id == 1
    assert kingdom.name == "Westeros"
    assert kingdom.morale == 85
    print(f"[OK] Kingdom domain works: created '{kingdom.name}'")


def test_geography_domain():
    """Test Geography domain imports and basic usage."""
    print("Testing Geography domain...")
    from warfare_simulation.domain.geography.models import Province, Border, Location
    from warfare_simulation.domain.geography.repository import (
        ProvinceRepository, BorderRepository, LocationRepository
    )
    from warfare_simulation.domain.geography.service import GeographyService
    
    # Create repositories
    province_repo = ProvinceRepository()
    border_repo = BorderRepository()
    location_repo = LocationRepository()
    validator = ValidationService()
    
    # Create service
    service = GeographyService(province_repo, border_repo, location_repo, validator)
    service.initialize()
    
    # Create province
    province = service.create_province(
        kingdom_id=1,
        name="The North",
        population=10000,
        monthly_tax=500,
        loyalty=80,
    )
    
    assert province.id == 1
    assert province.name == "The North"
    print(f"[OK] Geography domain works: created '{province.name}'")


def test_military_domain():
    """Test Military domain imports and basic usage."""
    print("Testing Military domain...")
    from warfare_simulation.domain.military.models import Unit, Commander, Garrison
    from warfare_simulation.domain.military.repository import (
        UnitRepository, CommanderRepository, GarrisonRepository
    )
    from warfare_simulation.domain.military.service import MilitaryService
    
    # Create repositories
    unit_repo = UnitRepository()
    commander_repo = CommanderRepository()
    garrison_repo = GarrisonRepository()
    validator = ValidationService()
    
    # Create service
    service = MilitaryService(unit_repo, commander_repo, garrison_repo, validator)
    service.initialize()
    
    # Create commander
    commander = service.create_commander(
        kingdom_id=1,
        name="Tyrion Lannister",
        role=CommanderRole.GENERAL,
        leadership=75,
        tactics=85,
        logistics=80,
    )
    
    assert commander.id == 1
    assert commander.name == "Tyrion Lannister"
    
    # Create unit
    unit = service.create_unit(
        kingdom_id=1,
        name="Lannister Vanguard",
        unit_type=UnitType.HEAVY_SPEARMEN,
        soldiers=500,
        armor=ArmorType.PLATE_MAIL,
        location_id=1,
    )
    
    assert unit.id == 1
    assert unit.soldiers == 500
    print(f"[OK] Military domain works: created commander '{commander.name}' and unit '{unit.name}'")


def test_diplomacy_domain():
    """Test Diplomacy domain imports and basic usage."""
    print("Testing Diplomacy domain...")
    from warfare_simulation.domain.diplomacy.models import Faction, Relation, Spy, Mission
    from warfare_simulation.domain.diplomacy.repository import (
        FactionRepository, RelationRepository, SpyRepository, MissionRepository
    )
    from warfare_simulation.domain.diplomacy.service import DiplomacyService
    
    # Create repositories
    faction_repo = FactionRepository()
    relation_repo = RelationRepository()
    spy_repo = SpyRepository()
    mission_repo = MissionRepository()
    validator = ValidationService()
    
    # Create service
    service = DiplomacyService(faction_repo, relation_repo, spy_repo, mission_repo, validator)
    service.initialize()
    
    # Create factions
    faction_a = service.create_faction(
        name="Targaryen Dynasty",
        faction_type="nation",
        power_level=80,
        wealth=70,
    )
    
    faction_b = service.create_faction(
        name="Stark House",
        faction_type="nation",
        power_level=75,
        wealth=65,
    )
    
    assert faction_a.id == 1
    assert faction_b.id == 2
    
    # Establish relation
    relation = service.establish_relation(
        faction_a_id=1,
        faction_b_id=2,
        initial_opinion=10,
    )
    
    assert relation.opinion == 10
    print(f"[OK] Diplomacy domain works: created factions '{faction_a.name}' and '{faction_b.name}'")


def test_logistics_domain():
    """Test Logistics domain imports and basic usage."""
    print("Testing Logistics domain...")
    from warfare_simulation.domain.logistics.models import Resource, Project, SupplyRoute
    from warfare_simulation.domain.logistics.repository import (
        ResourceRepository, ProjectRepository, SupplyRouteRepository
    )
    from warfare_simulation.domain.logistics.service import LogisticsService
    
    # Create repositories
    resource_repo = ResourceRepository()
    project_repo = ProjectRepository()
    route_repo = SupplyRouteRepository()
    validator = ValidationService()
    
    # Create service
    service = LogisticsService(resource_repo, project_repo, route_repo, validator)
    service.initialize()
    
    # Create resource
    resource = service.create_resource(
        kingdom_id=1,
        resource_type=ResourceType.FOOD,
        initial_stored=5000,
        monthly_production=500,
    )
    
    assert resource.id == 1
    assert resource.stored == 5000
    
    # Create project
    project = service.create_project(
        kingdom_id=1,
        name="Winterfell Fortification",
        project_type=ProjectType.FORTIFICATION,
        cost_silver=5000,
        duration=5,
    )
    
    assert project.id == 1
    assert project.name == "Winterfell Fortification"
    print(f"[OK] Logistics domain works: created resource and project '{project.name}'")


def test_events_domain():
    """Test Events domain imports and basic usage."""
    print("Testing Events domain...")
    from warfare_simulation.domain.events.models import Event
    from warfare_simulation.domain.events.repository import EventRepository
    from warfare_simulation.domain.events.service import EventService
    
    # Create repository
    event_repo = EventRepository()
    
    # Create service
    service = EventService(event_repo)
    service.initialize()
    
    # Log event
    event = service.log_kingdom_event(
        turn=1,
        description="Kingdom established",
        impact="Kingdom Westeros now active",
        kingdom_id=1,
    )
    
    assert event.id == 1
    # Check category by string value since enum comparison can be tricky
    assert str(event.category.value) == "Economy", f"Expected Economy but got {event.category.value}"
    assert event.description == "Kingdom established"
    
    # Get summary
    summary = service.get_turn_summary(1)
    assert "Kingdom established" in summary
    
    print(f"[OK] Events domain works: logged event '{event.description}'")


def run_all_tests():
    """Run all domain tests."""
    print("=" * 60)
    print("PHASE 2 DOMAIN TEST SUITE")
    print("=" * 60)
    print()
    
    try:
        test_kingdom_domain()
        test_geography_domain()
        test_military_domain()
        test_diplomacy_domain()
        test_logistics_domain()
        test_events_domain()
        
        print()
        print("=" * 60)
        print("[OK] ALL TESTS PASSED - Phase 2 domains complete!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print()
        print("=" * 60)
        print(f"[FAIL] TEST FAILED: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)


def test_living_chronicle_phase4_army_movement_constraints():
    """Logistics Phase 4 should model route progress, supply shortage, and contact."""
    from warfare_simulation.domain.logistics.repository import (
        ArmyMovementRepository,
        ProjectRepository,
        ResourceRepository,
        SupplyRouteRepository,
    )
    from warfare_simulation.domain.logistics.service import LogisticsService

    service = LogisticsService(
        ResourceRepository(),
        ProjectRepository(),
        SupplyRouteRepository(),
        ValidationService(),
        movement_repo=ArmyMovementRepository(),
    )

    movement = service.create_army_movement(
        army_name="Veyl Relief Column",
        kingdom_id=1,
        unit_ids=[1, 2],
        route=[10, 11, 12],
        supply_days=1,
        base_daily_progress=50,
    )

    first_day = service.advance_army_movement_day(
        movement.id,
        weather_modifier=0.8,
        road_modifier=0.5,
        enemy_present=True,
    )
    assert first_day["status"] == "marching"
    assert first_day["progress_gained"] == 20
    assert first_day["shortage_level"] == "supplied"
    assert first_day["contact_detected"] is True

    for _ in range(6):
        final_day = service.advance_army_movement_day(
            movement.id,
            weather_modifier=0.6,
            road_modifier=0.5,
        )

    stored = service.movement_repo.get(movement.id)
    assert stored is not None
    assert final_day["status"] == "turned_back"
    assert stored.shortage_level == "starving"
    assert stored.attrition_taken > 0

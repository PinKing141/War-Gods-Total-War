"""Tests for activating the CSV seed frontier into runtime tables."""

from pathlib import Path

from warfare_simulation.app import WarfareSimulationApp
from warfare_simulation.config.config import ConfigManager
from warfare_simulation.config.csv_loader import CsvLoreLoader
from warfare_simulation.persistence.campaign_bootstrap import CampaignBootstrap
from warfare_simulation.persistence.database import DatabaseManager
from warfare_simulation.persistence.lore_bootstrap import LoreBootstrap
from warfare_simulation.persistence.seed_frontier_activation import SeedFrontierActivation


ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "src" / "warfare_simulation" / "config" / "data"


def _runtime_counts(db: DatabaseManager) -> dict[str, int]:
    return {
        table: db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in ("faction", "province", "relation", "commander")
    }


def test_seed_frontier_activation_creates_runtime_rows_idempotently(tmp_path):
    """Seed frontier rows become active runtime rows without duplicate activations."""
    loader = CsvLoreLoader()
    expected_seed_counts = {
        "faction": len(loader.load_seed_factions()),
        "province": len(loader.load_seed_provinces()),
        "relation": len(loader.load_seed_relations()),
        "commander": len(loader.load_seed_characters()),
    }

    db = DatabaseManager(str(tmp_path / "seed_frontier.db"))
    db.connect()
    LoreBootstrap.seed_lore(db)
    CampaignBootstrap.seed_from_config(ConfigManager(str(CONFIG_DIR)), db)
    before = _runtime_counts(db)

    result = SeedFrontierActivation.activate(db)
    after_first = _runtime_counts(db)
    result_2 = SeedFrontierActivation.activate(db)
    after_second = _runtime_counts(db)

    assert result == result_2
    assert result.factions == expected_seed_counts["faction"]
    assert result.provinces == expected_seed_counts["province"]
    assert result.relations == expected_seed_counts["relation"]
    assert result.commanders == expected_seed_counts["commander"]
    assert after_second == after_first

    for table, seed_count in expected_seed_counts.items():
        assert after_first[table] == before[table] + seed_count

    rov = db.execute(
        """
        SELECT id, dominant_culture, religion_id, personality_traits
        FROM faction
        WHERE seed_faction_id = ?
        """,
        ("FAC_ROV_HALEN",),
    ).fetchone()
    assert rov is not None
    assert rov[1] == "CULT_ROVANT"
    assert rov[2] == "REL_MEASURE_ROADS"
    assert "road_control_priority:95" in rov[3]
    assert "lawful_claim_weight:20" in rov[3]

    halem = db.execute(
        """
        SELECT controller_faction_id, road_level, port_level, mana_site_level, strategic_value
        FROM province
        WHERE seed_province_id = ?
        """,
        ("PROV_ROV_HALEM",),
    ).fetchone()
    assert halem == (rov[0], 5, 2, 1, 95)

    relation = db.execute(
        """
        SELECT status, opinion, main_tension, war_risk
        FROM relation
        WHERE seed_relation_id = ?
        """,
        ("SREL_002",),
    ).fetchone()
    assert relation == ("ENEMY", -60, "service_yoke_claims_and_road_control", 70)

    claim_link = db.execute(
        """
        SELECT active_claimant_faction_id, active_target_province_id
        FROM claim
        WHERE claim_id = ?
        """,
        ("CLAIM_ROV_OPEN_GATE",),
    ).fetchone()
    assert claim_link[0] == rov[0]
    assert claim_link[1] is not None

    mage_link = db.execute(
        """
        SELECT active_character_commander_id, active_patron_faction_id
        FROM mage
        WHERE mage_id = ?
        """,
        ("MAGE_001",),
    ).fetchone()
    assert mage_link[0] is not None
    assert mage_link[1] is not None

    repos = CampaignBootstrap.load_repositories(db)
    assert repos.faction.get_by_name("Crown of Rov Halem") is not None
    assert repos.province.get_by_name("Halem Bridge") is not None

    db.close()


def test_app_can_optionally_start_with_active_seed_frontier(tmp_path):
    """The app keeps legacy startup by default but can activate the frontier seed."""
    app = WarfareSimulationApp(
        config_path=CONFIG_DIR,
        db_path=tmp_path / "app_seed_frontier.db",
        activate_seed_frontier=True,
    )

    assert app.repos.faction.get_by_name("Crown of Rov Halem") is not None
    assert app.repos.province.get_by_name("Halem Bridge") is not None


def test_active_seed_claims_influence_monthly_faction_intent(tmp_path):
    """Activated claims should make the monthly AI choose a lore-backed claim intent."""
    app = WarfareSimulationApp(
        config_path=CONFIG_DIR,
        db_path=tmp_path / "claim_intent.db",
        activate_seed_frontier=True,
    )
    rov = app.repos.faction.get_by_name("Crown of Rov Halem")

    app.campaign.advance_turn()

    claim_log = next(
        log
        for log in app.repos.observer_log.get_by_stream("diplomacy")
        if log.actor == f"faction:{rov.id}" and log.source_system == "FactionIntent"
    )
    claim_event = next(
        event
        for event in app.repos.event.list_all()
        if event.actor == f"faction:{rov.id}" and event.source_system == "FactionIntent"
    )

    assert claim_log.details["intent_type"] == "press_claim"
    assert claim_log.details["claim_signal"]["claim_id"] == "CLAIM_ROV_OPEN_GATE"
    assert claim_log.details["claim_signal"]["target_name"] == "Open Gate Freehold"
    assert "Sarovan service-yoke record" in claim_log.details["description"]
    assert any(part.startswith("claim_pressure:CLAIM_ROV_OPEN_GATE") for part in claim_event.cause_chain)


def test_first_historical_loop_mutates_state_and_formats_reason(tmp_path):
    """Pressure -> intent -> validation -> action should change state and explain why."""
    app = WarfareSimulationApp(
        config_path=CONFIG_DIR,
        db_path=tmp_path / "historical_loop.db",
        activate_seed_frontier=True,
    )
    db = app.db_mgr
    rov = app.repos.faction.get_by_name("Crown of Rov Halem")
    open_gate = app.repos.province.get_by_name("Open Gate Freehold")
    before_relation = db.execute(
        """
        SELECT opinion, trust, war_risk
        FROM relation
        WHERE seed_relation_id = ?
        """,
        ("SREL_002",),
    ).fetchone()
    before_loyalty = open_gate.loyalty

    app.campaign.advance_turn()

    after_relation = db.execute(
        """
        SELECT opinion, trust, war_risk
        FROM relation
        WHERE seed_relation_id = ?
        """,
        ("SREL_002",),
    ).fetchone()
    refreshed_open_gate = app.repos.province.get(open_gate.id)
    historical_logs = [
        log
        for log in app.repos.observer_log.get_by_stream("diplomacy")
        if log.source_system == "HistoricalLoop"
    ]
    rov_log = next(log for log in historical_logs if log.actor == f"faction:{rov.id}")
    rov_event = next(
        event
        for event in app.repos.event.list_all()
        if event.actor == f"faction:{rov.id}" and event.source_system == "HistoricalLoop"
    )
    historical_audits = app.repos.audit_log.get_by_system("HistoricalLoop")

    assert after_relation[0] < before_relation[0]
    assert after_relation[1] < before_relation[1]
    assert after_relation[2] > before_relation[2]
    assert refreshed_open_gate.loyalty < before_loyalty
    assert rov_log.details["validation"]["accepted"] is True
    assert rov_log.details["intent"]["intent_type"] == "press_service_yoke_claim"
    assert "Sarovan service-yoke record" in rov_log.summary
    assert "Service Colony Nineteen" in rov_log.summary
    assert "action:press_service_yoke_claim" in rov_event.cause_chain
    assert historical_audits
    assert historical_audits[0].new_value["action"]["accepted"] is True

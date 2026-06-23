"""Thin runnable application for initializing and exporting a campaign."""

from pathlib import Path

from warfare_simulation.config.config import ConfigManager
from warfare_simulation.orchestration import CampaignOrchestrator, GameState
from warfare_simulation.persistence.campaign_bootstrap import CampaignBootstrap
from warfare_simulation.persistence.database import DatabaseManager


class WarfareSimulationApp:
    """Load JSON config, seed SQLite runtime state, and export a workbook."""

    def __init__(self, config_path: str | Path | None = None, db_path: str | Path = "war_sim.db"):
        self.config_mgr = ConfigManager(str(config_path) if config_path is not None else None)
        self.db_mgr = DatabaseManager(str(db_path))
        self.repos = CampaignBootstrap.initialize(self.config_mgr, self.db_mgr)
        self.game_state = GameState()
        self.campaign = CampaignOrchestrator(
            {
                "kingdom": self.repos.kingdom,
                "geography": self.repos.province,
                "province": self.repos.province,
                "military": self.repos,
                "unit": self.repos.unit,
                "commander": self.repos.commander,
                "diplomacy": self.repos,
                "faction": self.repos.faction,
                "relation": self.repos.relation,
                "logistics": self.repos.resource,
                "resource": self.repos.resource,
                "event": self.repos.event,
                "audit_log": self.repos.audit_log,
                "observer_log": self.repos.observer_log,
                "turn_summary": self.repos.turn_summary,
                "scheduled_event": self.repos.scheduled_event,
            },
            game_state=self.game_state,
        )

    def export_campaign(self, filename: str | Path = "Auster_Campaign_Engine.xlsx") -> Path:
        """Generate the campaign spreadsheet."""
        return self.campaign.export_campaign(filename)

    def run(self, filename: str | Path = "Auster_Campaign_Engine.xlsx") -> Path:
        """Initialize the campaign and export the spreadsheet."""
        print("Campaign engine initialized.")
        output_path = self.export_campaign(filename)
        print(f"Spreadsheet exported to {output_path}.")
        return output_path

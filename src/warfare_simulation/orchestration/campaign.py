"""Campaign-level orchestration for export and turn advancement."""

from pathlib import Path
from typing import Any, Mapping

from warfare_simulation.export.workbook_factory import WorkbookFactory
from warfare_simulation.orchestration.game_state import GameState


class CampaignOrchestrator:
    """Coordinates high-level campaign actions across domain repositories."""

    def __init__(self, repos: Mapping[str, Any], game_state: GameState | None = None):
        self.repos = dict(repos)
        self.game_state = game_state or GameState()

    def export_campaign(self, filename: str | Path) -> Path:
        """Generate the current campaign state as an Excel workbook."""
        output_path = Path(filename)
        factory = WorkbookFactory(self.repos)
        workbook = factory.create_workbook()
        workbook.save(output_path)
        return output_path

    def advance_turn(self) -> GameState:
        """Advance the campaign by one monthly turn.

        Phase 7 starts with deterministic economy/logistics progression: the active
        kingdom collects net income and every tracked resource applies monthly net
        production. The global ``GameState`` is then synchronized to the kingdom's
        campaign clock so exports and future systems share one turn counter.
        """
        kingdom_repo = self.repos.get("kingdom")
        if kingdom_repo is None:
            self.game_state.advance_turn()
            return self.game_state

        kingdoms = kingdom_repo.list_all()
        for kingdom in kingdoms:
            kingdom.advance_turn()
            kingdom_repo.update(kingdom)

        resource_repo = self.repos.get("resource") or self.repos.get("logistics")
        if resource_repo is not None:
            for resource in resource_repo.list_all():
                resource.advance_turn()
                resource_repo.update(resource)

        if kingdoms:
            self.game_state.sync_from_kingdom(kingdoms[0])
        else:
            self.game_state.advance_turn()

        return self.game_state

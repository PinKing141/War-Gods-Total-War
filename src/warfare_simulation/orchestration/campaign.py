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
        self._sync_game_state_from_repos()

    def _sync_game_state_from_repos(self) -> None:
        """Initialize the shared game clock from persisted kingdom state when available."""
        kingdom_repo = self.repos.get("kingdom")
        if kingdom_repo is None or not hasattr(kingdom_repo, "get_current_kingdom"):
            return

        kingdom = kingdom_repo.get_current_kingdom()
        if kingdom is not None:
            self.game_state.sync_from_kingdom(kingdom)

    def export_campaign(self, filename: str | Path) -> Path:
        """Generate the current campaign state as an Excel workbook."""
        output_path = Path(filename)
        factory = WorkbookFactory(self.repos)
        workbook = factory.create_workbook()
        workbook.save(output_path)
        return output_path

    def advance_day(self) -> GameState:
        """Advance the simulation by one in-world day.

        The currently-implemented economy and logistics logic remains monthly, so
        only month rollovers trigger the existing domain progression slice.
        """
        month_rolled = self.game_state.advance_day()

        kingdom_repo = self.repos.get("kingdom")
        kingdoms = []
        if kingdom_repo is not None and hasattr(kingdom_repo, "list_all"):
            kingdoms = kingdom_repo.list_all()
            for kingdom in kingdoms:
                kingdom.current_day = self.game_state.current_day
                if month_rolled:
                    kingdom.advance_turn()
                    kingdom.current_day = self.game_state.current_day
                else:
                    kingdom.current_turn = self.game_state.current_turn
                    kingdom.current_month = self.game_state.current_month
                    kingdom.current_year = self.game_state.current_year
                    kingdom.mark_updated()
                kingdom_repo.update(kingdom)

        if month_rolled:
            resource_repo = self.repos.get("resource") or self.repos.get("logistics")
            if resource_repo is not None:
                for resource in resource_repo.list_all():
                    resource.advance_turn()
                    resource_repo.update(resource)

        if kingdoms:
            self.game_state.sync_from_kingdom(kingdoms[0])

        return self.game_state

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
            kingdom.current_day = 1
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

"""Campaign-level orchestration for export and turn advancement."""

from pathlib import Path
from typing import Any, Mapping

from warfare_simulation.core.constants import EventCategory
from warfare_simulation.domain.events.models import AuditLog, Event
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

        event_repo = self.repos.get("event")
        audit_repo = self.repos.get("audit_log")

        kingdoms = kingdom_repo.list_all()
        for kingdom in kingdoms:
            previous_treasury = kingdom.treasury_silver
            kingdom.advance_turn()
            kingdom_repo.update(kingdom)
            if audit_repo is not None:
                audit_repo.create(
                    AuditLog(
                        turn=kingdom.current_turn,
                        month=kingdom.current_month,
                        year=kingdom.current_year,
                        actor=f"kingdom:{kingdom.id}",
                        target=f"kingdom:{kingdom.id}.treasury_silver",
                        system="Economy",
                        action="collect_monthly_net_income",
                        previous_value=previous_treasury,
                        new_value=kingdom.treasury_silver,
                        reason="Monthly income minus expenses during turn advancement.",
                    )
                )
            if event_repo is not None:
                event_repo.create(
                    Event(
                        turn=kingdom.current_turn,
                        category=EventCategory.ECONOMY,
                        description=f"{kingdom.name} collected monthly net income.",
                        impact=(
                            f"Treasury changed from {previous_treasury} "
                            f"to {kingdom.treasury_silver} silver."
                        ),
                        affected_entities=[kingdom.id],
                    )
                )

        resource_repo = self.repos.get("resource") or self.repos.get("logistics")
        if resource_repo is not None:
            for resource in resource_repo.list_all():
                previous_stored = resource.stored
                resource.advance_turn()
                resource_repo.update(resource)
                if audit_repo is not None:
                    audit_repo.create(
                        AuditLog(
                            turn=self.game_state.current_turn + 1,
                            month=(self.game_state.current_month % 12) + 1,
                            year=self.game_state.current_year + (1 if self.game_state.current_month == 12 else 0),
                            actor=f"kingdom:{resource.kingdom_id}",
                            target=f"resource:{resource.id}.stored",
                            system="Logistics",
                            action="apply_monthly_net_production",
                            previous_value=previous_stored,
                            new_value=resource.stored,
                            reason="Monthly production minus consumption during turn advancement.",
                        )
                    )

        if kingdoms:
            self.game_state.sync_from_kingdom(kingdoms[0])
        else:
            self.game_state.advance_turn()

        return self.game_state

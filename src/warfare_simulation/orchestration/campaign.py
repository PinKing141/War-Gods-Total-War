"""Campaign-level orchestration for export and turn advancement."""

from pathlib import Path
from typing import Any, Mapping

from warfare_simulation.core.constants import EventCategory
from warfare_simulation.domain.events.models import AuditLog, Event, TurnSummary
from warfare_simulation.export.workbook_factory import WorkbookFactory
from warfare_simulation.orchestration.game_state import GameState
from warfare_simulation.orchestration.pulses import PulseContext, PulseScheduler, PulseType


class CampaignOrchestrator:
    """Coordinates high-level campaign actions across domain repositories."""

    def __init__(self, repos: Mapping[str, Any], game_state: GameState | None = None):
        self.repos = dict(repos)
        self.game_state = game_state or GameState()
        self._sync_game_state_from_repos()
        self.pulse_scheduler = PulseScheduler()
        self._register_default_pulse_hooks()

    def _sync_game_state_from_repos(self) -> None:
        """Initialize the shared game clock from persisted kingdom state when available."""
        kingdom_repo = self.repos.get("kingdom")
        if kingdom_repo is None or not hasattr(kingdom_repo, "get_current_kingdom"):
            return

        kingdom = kingdom_repo.get_current_kingdom()
        if kingdom is not None:
            self.game_state.sync_from_kingdom(kingdom)

    def _register_default_pulse_hooks(self) -> None:
        """Register deterministic pulse hooks for currently implemented domains."""
        self.pulse_scheduler.register(
            PulseType.DAILY, "kingdom_clock_sync", self._sync_kingdom_clock_daily
        )
        self.pulse_scheduler.register(
            PulseType.WEEKLY, "route_and_risk_placeholder", self._record_weekly_boundary
        )
        self.pulse_scheduler.register(
            PulseType.MONTHLY, "kingdom_economy", self._resolve_monthly_kingdoms
        )
        self.pulse_scheduler.register(
            PulseType.MONTHLY, "logistics_resources", self._resolve_monthly_resources
        )
        self.pulse_scheduler.register(
            PulseType.MONTHLY, "observer_summary", self._resolve_monthly_summary
        )
        self.pulse_scheduler.register(
            PulseType.SEASONAL, "seasonal_placeholder", self._record_seasonal_boundary
        )
        self.pulse_scheduler.register(
            PulseType.YEARLY, "yearly_placeholder", self._record_yearly_boundary
        )

    def export_campaign(self, filename: str | Path) -> Path:
        """Generate the current campaign state as an Excel workbook."""
        output_path = Path(filename)
        factory = WorkbookFactory(self.repos)
        workbook = factory.create_workbook()
        workbook.save(output_path)
        return output_path

    def advance_day(self) -> GameState:
        """Advance the simulation by one in-world day and run due pulse hooks."""
        before = GameState.from_dict(self.game_state.to_dict())
        month_rolled = self.game_state.advance_day()
        context = PulseContext.from_transition(before, self.game_state, month_rolled)
        self.pulse_scheduler.run(context)
        return self.game_state

    def _sync_kingdom_clock_daily(self, context: PulseContext) -> None:
        """Persist ordinary day changes without running monthly systems."""
        if context.month_rolled:
            return

        kingdom_repo = self.repos.get("kingdom")
        if kingdom_repo is None or not hasattr(kingdom_repo, "list_all"):
            return

        kingdoms = kingdom_repo.list_all()
        for kingdom in kingdoms:
            kingdom.current_day = context.current_day
            kingdom.current_turn = context.current_turn
            kingdom.current_month = context.current_month
            kingdom.current_year = context.current_year
            kingdom.mark_updated()
            kingdom_repo.update(kingdom)

    def _resolve_monthly_kingdoms(self, context: PulseContext) -> None:
        """Run monthly kingdom economy at a month boundary."""
        kingdom_repo = self.repos.get("kingdom")
        if kingdom_repo is None or not hasattr(kingdom_repo, "list_all"):
            return

        event_repo = self.repos.get("event")
        audit_repo = self.repos.get("audit_log")
        kingdoms = kingdom_repo.list_all()
        for kingdom in kingdoms:
            previous_treasury = kingdom.treasury_silver
            kingdom.advance_turn()
            kingdom.current_day = context.current_day
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
                        reason="Monthly income minus expenses during scheduled monthly pulse.",
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

        if kingdoms:
            self.game_state.sync_from_kingdom(kingdoms[0])

    def _resolve_monthly_resources(self, context: PulseContext) -> None:
        """Run monthly resource production at a month boundary."""
        resource_repo = self.repos.get("resource") or self.repos.get("logistics")
        if resource_repo is None:
            return

        audit_repo = self.repos.get("audit_log")
        for resource in resource_repo.list_all():
            previous_stored = resource.stored
            resource.advance_turn()
            resource_repo.update(resource)
            if audit_repo is not None:
                audit_repo.create(
                    AuditLog(
                        turn=context.current_turn,
                        month=context.current_month,
                        year=context.current_year,
                        actor=f"kingdom:{resource.kingdom_id}",
                        target=f"resource:{resource.id}.stored",
                        system="Logistics",
                        action="apply_monthly_net_production",
                        previous_value=previous_stored,
                        new_value=resource.stored,
                        reason="Monthly production minus consumption during scheduled monthly pulse.",
                    )
                )

    def _resolve_monthly_summary(self, context: PulseContext) -> None:
        """Write observer summary after monthly domain hooks finish."""
        self._write_turn_summary()

    def _record_weekly_boundary(self, context: PulseContext) -> None:
        """Reserved hook for Phase 9 weekly route/risk recalculation."""
        return None

    def _record_seasonal_boundary(self, context: PulseContext) -> None:
        """Reserved hook for Phase 9 seasonal weather and harvest systems."""
        return None

    def _record_yearly_boundary(self, context: PulseContext) -> None:
        """Reserved hook for Phase 9 yearly demographic and succession systems."""
        return None

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
            kingdom.current_day = 1
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
                            year=self.game_state.current_year
                            + (1 if self.game_state.current_month == 12 else 0),
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

        self._write_turn_summary()
        return self.game_state

    def _write_turn_summary(self) -> TurnSummary | None:
        """Create an auditable high-level summary for the completed turn."""
        summary_repo = self.repos.get("turn_summary")
        if summary_repo is None:
            return None

        event_repo = self.repos.get("event")
        audit_repo = self.repos.get("audit_log")
        events = (
            event_repo.get_by_turn(self.game_state.current_turn) if event_repo is not None else []
        )
        audits = (
            audit_repo.get_by_turn(self.game_state.current_turn) if audit_repo is not None else []
        )
        highlights = [event.description for event in events[:3]]
        if not highlights:
            highlights = ["No major campaign events were recorded."]

        economy_audits = [audit for audit in audits if audit.system == "Economy"]
        logistics_audits = [audit for audit in audits if audit.system == "Logistics"]
        narrative_parts = [
            f"Turn {self.game_state.current_turn} closed in month {self.game_state.current_month}, year {self.game_state.current_year}.",
            f"Recorded {len(events)} event(s) and {len(audits)} auditable state change(s).",
        ]
        if economy_audits:
            narrative_parts.append(f"Economy resolved {len(economy_audits)} treasury update(s).")
        if logistics_audits:
            narrative_parts.append(
                f"Logistics resolved {len(logistics_audits)} resource update(s)."
            )

        return summary_repo.create(
            TurnSummary(
                turn=self.game_state.current_turn,
                month=self.game_state.current_month,
                year=self.game_state.current_year,
                title=f"Turn {self.game_state.current_turn} Summary",
                narrative=" ".join(narrative_parts),
                event_count=len(events),
                audit_count=len(audits),
                highlights=highlights,
            )
        )

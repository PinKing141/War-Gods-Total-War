"""Campaign-level orchestration for export and turn advancement."""

from pathlib import Path
from typing import Any, Mapping

from warfare_simulation.core.constants import EventCategory
from warfare_simulation.domain.events.models import AuditLog, Event, TurnSummary
from warfare_simulation.export.workbook_factory import WorkbookFactory
from warfare_simulation.orchestration.game_state import GameState
from warfare_simulation.orchestration.pulse_scheduler import PulseReport, PulseScheduler


class CampaignOrchestrator:
    """Coordinates high-level campaign actions across domain repositories."""

    def __init__(self, repos: Mapping[str, Any], game_state: GameState | None = None):
        self.repos = dict(repos)
        self.game_state = game_state or GameState()
        self.pulse_scheduler = PulseScheduler()
        self.last_pulse_report: PulseReport | None = None
        self._register_pulse_hooks()
        self._sync_game_state_from_repos()

    def _register_pulse_hooks(self) -> None:
        """Register implemented domain work with the pulse scheduler."""
        self.pulse_scheduler.register("daily", self._sync_daily_calendar_to_kingdoms)
        self.pulse_scheduler.register("monthly", self._resolve_monthly_economy_and_logistics)

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
        """Advance the simulation by one in-world day through scheduled pulses.

        Daily, weekly, monthly, seasonal, and yearly pulse boundaries are resolved
        by ``PulseScheduler``. The currently implemented economy and logistics
        mutations remain monthly, so they execute only when the scheduler reports
        the monthly pulse for the newly-entered date.
        """
        previous_date = self.game_state.sim_date
        self.game_state.advance_day()
        self.last_pulse_report = self.pulse_scheduler.run_due_pulses(
            previous_date,
            self.game_state.sim_date,
        )
        return self.game_state

    def _sync_daily_calendar_to_kingdoms(self, _date: Any) -> None:
        """Persist the daily clock to kingdom aggregates without monthly effects."""
        kingdom_repo = self.repos.get("kingdom")
        if kingdom_repo is None or not hasattr(kingdom_repo, "list_all"):
            return

        kingdoms = kingdom_repo.list_all()
        for kingdom in kingdoms:
            kingdom.current_day = self.game_state.current_day
            kingdom.current_turn = self.game_state.current_turn
            kingdom.current_month = self.game_state.current_month
            kingdom.current_year = self.game_state.current_year
            kingdom.mark_updated()
            kingdom_repo.update(kingdom)

    def _resolve_monthly_economy_and_logistics(self, _date: Any) -> None:
        """Resolve currently implemented monthly economy and logistics systems."""
        kingdom_repo = self.repos.get("kingdom")
        event_repo = self.repos.get("event")
        audit_repo = self.repos.get("audit_log")

        kingdoms = []
        if kingdom_repo is not None and hasattr(kingdom_repo, "list_all"):
            kingdoms = kingdom_repo.list_all()
            for kingdom in kingdoms:
                previous_treasury = kingdom.treasury_silver
                kingdom.treasury_silver += kingdom.monthly_income - kingdom.monthly_expenses
                kingdom.current_day = self.game_state.current_day
                kingdom.current_turn = self.game_state.current_turn
                kingdom.current_month = self.game_state.current_month
                kingdom.current_year = self.game_state.current_year
                kingdom.mark_updated()
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
                            action="daily_scheduler_monthly_net_income",
                            previous_value=previous_treasury,
                            new_value=kingdom.treasury_silver,
                            reason="Monthly economy pulse reached by daily scheduler.",
                        )
                    )
                if event_repo is not None:
                    event_repo.create(
                        Event(
                            turn=kingdom.current_turn,
                            category=EventCategory.ECONOMY,
                            description=f"{kingdom.name} resolved the monthly economy pulse.",
                            impact=(
                                f"Treasury changed from {previous_treasury} "
                                f"to {kingdom.treasury_silver} silver."
                            ),
                            affected_entities=[kingdom.id],
                            day=kingdom.current_day,
                            month=kingdom.current_month,
                            year=kingdom.current_year,
                            actor=f"kingdom:{kingdom.id}",
                            target=f"kingdom:{kingdom.id}.treasury_silver",
                            source_system="Economy",
                            cause_chain=[
                                "daily_scheduler",
                                "monthly_pulse",
                                "collect_monthly_net_income",
                                f"income:{kingdom.monthly_income}",
                                f"expenses:{kingdom.monthly_expenses}",
                            ],
                            effect_summary=(
                                f"Treasury changed from {previous_treasury} "
                                f"to {kingdom.treasury_silver} silver."
                            ),
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
                            turn=self.game_state.current_turn,
                            month=self.game_state.current_month,
                            year=self.game_state.current_year,
                            actor=f"kingdom:{resource.kingdom_id}",
                            target=f"resource:{resource.id}.stored",
                            system="Logistics",
                            action="daily_scheduler_monthly_net_production",
                            previous_value=previous_stored,
                            new_value=resource.stored,
                            reason="Monthly logistics pulse reached by daily scheduler.",
                        )
                    )
                if event_repo is not None:
                    event_repo.create(
                        Event(
                            turn=self.game_state.current_turn,
                            category=EventCategory.LOGISTICS,
                            description=f"Resource {resource.id} resolved monthly net production.",
                            impact=f"Stored amount changed from {previous_stored} to {resource.stored}.",
                            affected_entities=[resource.id],
                            day=self.game_state.current_day,
                            month=self.game_state.current_month,
                            year=self.game_state.current_year,
                            actor=f"kingdom:{resource.kingdom_id}",
                            target=f"resource:{resource.id}.stored",
                            source_system="Logistics",
                            cause_chain=[
                                "daily_scheduler",
                                "monthly_pulse",
                                "apply_monthly_net_production",
                                f"production:{resource.monthly_production}",
                                f"consumption:{resource.monthly_consumption}",
                            ],
                            effect_summary=f"Stored amount changed from {previous_stored} to {resource.stored}.",
                        )
                    )

        if kingdoms:
            self.game_state.sync_from_kingdom(kingdoms[0])

        self._write_turn_summary()

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
                        day=kingdom.current_day,
                        month=kingdom.current_month,
                        year=kingdom.current_year,
                        actor=f"kingdom:{kingdom.id}",
                        target=f"kingdom:{kingdom.id}.treasury_silver",
                        source_system="Economy",
                        cause_chain=[
                            "monthly_pulse",
                            "collect_monthly_net_income",
                            f"income:{kingdom.monthly_income}",
                            f"expenses:{kingdom.monthly_expenses}",
                        ],
                        effect_summary=(
                            f"Treasury changed from {previous_treasury} "
                            f"to {kingdom.treasury_silver} silver."
                        ),
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

        self._write_turn_summary()
        return self.game_state

    def _write_turn_summary(self) -> TurnSummary | None:
        """Create an auditable high-level summary for the completed turn."""
        summary_repo = self.repos.get("turn_summary")
        if summary_repo is None:
            return None

        event_repo = self.repos.get("event")
        audit_repo = self.repos.get("audit_log")
        events = event_repo.get_by_turn(self.game_state.current_turn) if event_repo is not None else []
        audits = audit_repo.get_by_turn(self.game_state.current_turn) if audit_repo is not None else []
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
            narrative_parts.append(f"Logistics resolved {len(logistics_audits)} resource update(s).")

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

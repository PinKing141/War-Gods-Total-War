"""Campaign-level orchestration for export and turn advancement."""

from pathlib import Path
from typing import Any, Mapping

from warfare_simulation.core.constants import EventCategory
from warfare_simulation.domain.events.models import AuditLog, Event, ObserverLog, TurnSummary
from warfare_simulation.domain.diplomacy.intent import FactionIntentEngine
from warfare_simulation.domain.events.summary import ObserverSummaryGenerator
from warfare_simulation.export.workbook_factory import WorkbookFactory
from warfare_simulation.orchestration.game_state import GameState
from warfare_simulation.orchestration.pulse_scheduler import PulseReport, PulseScheduler


class CampaignOrchestrator:
    """Coordinates high-level campaign actions across domain repositories."""

    def __init__(self, repos: Mapping[str, Any], game_state: GameState | None = None):
        self.repos = dict(repos)
        self.game_state = game_state or GameState()
        self.pulse_scheduler = PulseScheduler()
        self.summary_generator = ObserverSummaryGenerator()
        self.faction_intent_engine = FactionIntentEngine()
        self.last_pulse_report: PulseReport | None = None
        self._register_pulse_hooks()
        self._sync_game_state_from_repos()
        self._restore_scheduled_events_from_repos()

    def _register_pulse_hooks(self) -> None:
        """Register implemented domain work with the pulse scheduler."""
        self.pulse_scheduler.register("daily", self._sync_daily_calendar_to_kingdoms)
        self.pulse_scheduler.register("monthly", self._resolve_monthly_economy_and_logistics)
        self.pulse_scheduler.register("monthly", self._resolve_monthly_faction_intents)
        self.pulse_scheduler.register("monthly", self._write_monthly_turn_summary)

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
        self._persist_scheduled_events_to_repos()
        return self.game_state

    def schedule_event(self, event: Any) -> Any:
        """Schedule a day-level event and persist the queue snapshot when available."""
        scheduled = self.pulse_scheduler.schedule_event(event)
        self._persist_scheduled_events_to_repos()
        return scheduled

    def _restore_scheduled_events_from_repos(self) -> None:
        """Hydrate the in-memory scheduler queue from SQLite on campaign reload."""
        scheduled_event_repo = self.repos.get("scheduled_event")
        if scheduled_event_repo is None or not hasattr(scheduled_event_repo, "list_all"):
            return
        self.pulse_scheduler.restore_checkpoint(
            {"scheduled_events": [event.to_dict() for event in scheduled_event_repo.list_all()]}
        )

    def _persist_scheduled_events_to_repos(self) -> None:
        """Persist pending and completed scheduled events for long-running reloads."""
        scheduled_event_repo = self.repos.get("scheduled_event")
        if scheduled_event_repo is None or not hasattr(scheduled_event_repo, "replace_all"):
            return
        scheduled_event_repo.replace_all(self.pulse_scheduler.scheduled_events)

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
                self._write_observer_log(
                    stream="economics",
                    turn=kingdom.current_turn,
                    day=kingdom.current_day,
                    month=kingdom.current_month,
                    year=kingdom.current_year,
                    actor=f"kingdom:{kingdom.id}",
                    target=f"kingdom:{kingdom.id}.treasury_silver",
                    source_system="Economy",
                    summary=f"{kingdom.name} treasury changed from {previous_treasury} to {kingdom.treasury_silver} silver.",
                    details={
                        "previous_treasury": previous_treasury,
                        "new_treasury": kingdom.treasury_silver,
                        "monthly_income": kingdom.monthly_income,
                        "monthly_expenses": kingdom.monthly_expenses,
                    },
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
                self._write_observer_log(
                    stream="logistics",
                    turn=self.game_state.current_turn,
                    day=self.game_state.current_day,
                    month=self.game_state.current_month,
                    year=self.game_state.current_year,
                    actor=f"kingdom:{resource.kingdom_id}",
                    target=f"resource:{resource.id}.stored",
                    source_system="Logistics",
                    summary=f"Resource {resource.id} stockpile changed from {previous_stored} to {resource.stored}.",
                    details={
                        "previous_stored": previous_stored,
                        "new_stored": resource.stored,
                        "monthly_production": resource.monthly_production,
                        "monthly_consumption": resource.monthly_consumption,
                    },
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

    def _resolve_monthly_faction_intents(self, _date: Any) -> None:
        """Evaluate autonomous faction pressure and record monthly strategic intents."""
        faction_repo = self.repos.get("faction")
        relation_repo = self.repos.get("relation")
        if faction_repo is None or not hasattr(faction_repo, "list_all"):
            return

        factions = faction_repo.list_all()
        relations = relation_repo.list_all() if relation_repo is not None and hasattr(relation_repo, "list_all") else []
        intents = self.faction_intent_engine.generate_intents(factions, relations)
        event_repo = self.repos.get("event")
        audit_repo = self.repos.get("audit_log")

        for intent in intents:
            actor = f"faction:{intent.faction_id}"
            target = f"faction:{intent.faction_id}.strategic_intent"
            summary = (
                f"{intent.faction_name} chose {intent.intent_type}: {intent.description}."
                if intent.valid
                else f"{intent.faction_name} failed to choose {intent.intent_type}: {intent.failure_reason}"
            )
            details = {
                "intent_type": intent.intent_type,
                "description": intent.description,
                "valid": intent.valid,
                "failure_reason": intent.failure_reason,
                "pressure": intent.pressure.as_dict(),
            }
            if audit_repo is not None:
                audit_repo.create(
                    AuditLog(
                        turn=self.game_state.current_turn,
                        month=self.game_state.current_month,
                        year=self.game_state.current_year,
                        actor=actor,
                        target=target,
                        system="FactionIntent",
                        action="choose_monthly_strategic_intent" if intent.valid else "reject_monthly_strategic_intent",
                        previous_value=None,
                        new_value=details,
                        reason="Monthly autonomous faction pressure evaluation.",
                    )
                )
            self._write_observer_log(
                stream="diplomacy",
                turn=self.game_state.current_turn,
                day=self.game_state.current_day,
                month=self.game_state.current_month,
                year=self.game_state.current_year,
                actor=actor,
                target=target,
                source_system="FactionIntent",
                summary=summary,
                details=details,
            )
            if event_repo is not None:
                event_repo.create(
                    Event(
                        turn=self.game_state.current_turn,
                        category=EventCategory.DIPLOMACY,
                        description=summary,
                        impact=(
                            "Faction posture recorded for observers; no direct state mutation in Phase 1A."
                            if intent.valid
                            else "Invalid faction posture was logged without mutating state."
                        ),
                        affected_entities=[intent.faction_id],
                        day=self.game_state.current_day,
                        month=self.game_state.current_month,
                        year=self.game_state.current_year,
                        actor=actor,
                        target=target,
                        source_system="FactionIntent",
                        cause_chain=intent.cause_chain,
                        effect_summary=(
                            f"Strategic intent recorded: {intent.intent_type}."
                            if intent.valid
                            else f"Strategic intent rejected: {intent.failure_reason}"
                        ),
                    )
                )

    def _write_monthly_turn_summary(self, _date: Any) -> None:
        """Persist the monthly observer summary after all monthly hooks run."""
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
            self._write_observer_log(
                stream="economics",
                turn=kingdom.current_turn,
                day=kingdom.current_day,
                month=kingdom.current_month,
                year=kingdom.current_year,
                actor=f"kingdom:{kingdom.id}",
                target=f"kingdom:{kingdom.id}.treasury_silver",
                source_system="Economy",
                summary=f"{kingdom.name} treasury changed from {previous_treasury} to {kingdom.treasury_silver} silver.",
                details={
                    "previous_treasury": previous_treasury,
                    "new_treasury": kingdom.treasury_silver,
                    "monthly_income": kingdom.monthly_income,
                    "monthly_expenses": kingdom.monthly_expenses,
                },
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
                self._write_observer_log(
                    stream="logistics",
                    turn=self.game_state.current_turn + 1,
                    day=1,
                    month=(self.game_state.current_month % 12) + 1,
                    year=self.game_state.current_year + (1 if self.game_state.current_month == 12 else 0),
                    actor=f"kingdom:{resource.kingdom_id}",
                    target=f"resource:{resource.id}.stored",
                    source_system="Logistics",
                    summary=f"Resource {resource.id} stockpile changed from {previous_stored} to {resource.stored}.",
                    details={
                        "previous_stored": previous_stored,
                        "new_stored": resource.stored,
                        "monthly_production": resource.monthly_production,
                        "monthly_consumption": resource.monthly_consumption,
                    },
                )

        if kingdoms:
            self.game_state.sync_from_kingdom(kingdoms[0])
        else:
            self.game_state.advance_turn()

        self._resolve_monthly_faction_intents(None)
        self._write_turn_summary()
        return self.game_state

    def _write_observer_log(
        self,
        *,
        stream: str,
        turn: int,
        day: int,
        month: int,
        year: int,
        actor: str,
        target: str,
        source_system: str,
        summary: str,
        details: dict[str, Any],
        source_event_id: int | None = None,
        source_audit_id: int | None = None,
    ) -> ObserverLog | None:
        """Write a domain-specific observer log if the repository is available."""
        observer_repo = self.repos.get("observer_log")
        if observer_repo is None:
            return None
        return observer_repo.create(
            ObserverLog(
                turn=turn,
                day=day,
                month=month,
                year=year,
                stream=stream,
                actor=actor,
                target=target,
                source_system=source_system,
                summary=summary,
                details=details,
                source_event_id=source_event_id,
                source_audit_id=source_audit_id,
            )
        )

    def _write_turn_summary(self) -> TurnSummary | None:
        """Create an auditable high-level summary for the completed turn."""
        summary_repo = self.repos.get("turn_summary")
        if summary_repo is None:
            return None

        event_repo = self.repos.get("event")
        audit_repo = self.repos.get("audit_log")
        observer_repo = self.repos.get("observer_log")
        events = event_repo.get_by_turn(self.game_state.current_turn) if event_repo is not None else []
        audits = audit_repo.get_by_turn(self.game_state.current_turn) if audit_repo is not None else []
        observer_logs = observer_repo.get_by_turn(self.game_state.current_turn) if observer_repo is not None else []

        summary = self.summary_generator.generate_monthly(
            month=self.game_state.current_month,
            year=self.game_state.current_year,
            turn=self.game_state.current_turn,
            events=events,
            audits=audits,
            observer_logs=observer_logs,
        )
        return summary_repo.create(self.summary_generator.to_turn_summary(summary))

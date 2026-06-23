"""Thin facade between the simulation engine and the UI layer.

The UI reads only from this service — never from domain objects directly.
That boundary keeps presentation code ignorant of persistence, repositories,
and turn-mutation logic, enabling the engine and UI to evolve independently.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from warfare_simulation.app import WarfareSimulationApp
from warfare_simulation.domain.events.summary import ObserverSummaryGenerator

# ---------------------------------------------------------------------------
# Read models — plain dataclasses, no domain objects exposed to UI
# ---------------------------------------------------------------------------


@dataclass
class KingdomSummary:
    name: str
    ruler: str
    treasury: int
    monthly_income: int
    monthly_expenses: int
    net_income: int
    morale: int
    loyalty: int
    grain_stores: int
    current_day: int
    current_turn: int
    current_month: int
    current_year: int


@dataclass
class SimulationStatus:
    current_day: int
    current_month: int
    current_year: int
    current_turn: int
    formatted_date: str
    simulation_speed: str
    is_paused: bool


@dataclass
class ProvinceRow:
    name: str
    population: int
    fort_level: int
    food_stored: int
    monthly_tax: int
    loyalty: int
    garrison: int
    governor: str


@dataclass
class ResourceRow:
    resource_type: str
    stored: int
    monthly_production: int
    monthly_consumption: int
    net_change: int
    max_storage: int


@dataclass
class ObserverSummaryRow:
    period: str
    title: str
    date_range: str
    turn: int
    narrative: str
    event_count: int
    audit_count: int
    observer_log_count: int
    highlights: str


@dataclass
class ArmyRow:
    name: str
    unit_type: str
    soldiers: int
    veterans: int
    strength: int
    morale: int
    fatigue: int
    armor: str
    status: str
    location: str
    commander: str


@dataclass
class TimelineRow:
    date: str
    turn: int
    kind: str
    system: str
    title: str
    details: str


@dataclass
class EventRow:
    date: str
    turn: int
    category: str
    actor: str
    target: str
    source_system: str
    description: str
    cause: str
    impact: str


@dataclass
class FactionRow:
    name: str
    faction_type: str
    power_level: int
    wealth: int
    stability: int


@dataclass
class RelationRow:
    faction_a: str
    faction_b: str
    status: str
    opinion: int
    trust: int
    trade_agreement: bool
    military_alliance: bool


# ---------------------------------------------------------------------------
# Service class
# ---------------------------------------------------------------------------


class CampaignService:
    """Provides read models and commands for the UI layer.

    The UI calls *get_* methods to read state, and *advance_turn* / *export*
    to trigger engine mutations.  No Qt imports, no domain objects leak out.
    """

    def __init__(self, engine: WarfareSimulationApp) -> None:
        self._engine = engine
        self._summary_generator = ObserverSummaryGenerator()

    # ------------------------------------------------------------------
    # Read models
    # ------------------------------------------------------------------

    def get_kingdom_summary(self) -> Optional[KingdomSummary]:
        k = self._engine.repos.kingdom.get_current_kingdom()
        if k is None:
            return None
        state = self._engine.game_state
        return KingdomSummary(
            name=k.name,
            ruler=k.ruler_name,
            treasury=k.treasury_silver,
            monthly_income=k.monthly_income,
            monthly_expenses=k.monthly_expenses,
            net_income=k.monthly_income - k.monthly_expenses,
            morale=k.morale,
            loyalty=k.loyalty,
            grain_stores=k.grain_stores,
            current_day=state.current_day,
            current_turn=state.current_turn,
            current_month=state.current_month,
            current_year=state.current_year,
        )

    def get_simulation_status(self) -> SimulationStatus:
        state = self._engine.game_state
        return SimulationStatus(
            current_day=state.current_day,
            current_month=state.current_month,
            current_year=state.current_year,
            current_turn=state.current_turn,
            formatted_date=state.formatted_date(),
            simulation_speed=state.simulation_speed,
            is_paused=state.is_paused(),
        )

    def get_provinces(self) -> List[ProvinceRow]:
        return [
            ProvinceRow(
                name=p.name,
                population=p.population,
                fort_level=p.fort_level,
                food_stored=p.food_stored,
                monthly_tax=p.monthly_tax,
                loyalty=p.loyalty,
                garrison=p.garrison_size,
                governor=p.governor_name,
            )
            for p in self._engine.repos.province.list_all()
        ]

    def get_resources(self) -> List[ResourceRow]:
        return [
            ResourceRow(
                resource_type=getattr(r.resource_type, "value", str(r.resource_type)),
                stored=r.stored,
                monthly_production=r.monthly_production,
                monthly_consumption=r.monthly_consumption,
                net_change=r.monthly_production - r.monthly_consumption,
                max_storage=r.max_storage,
            )
            for r in self._engine.repos.resource.list_all()
        ]

    def get_armies(self) -> List[ArmyRow]:
        """Return army units with resolved commander and province names for the observer UI."""
        commanders = {c.id: c.name for c in self._engine.repos.commander.list_all()}
        provinces = {p.id: p.name for p in self._engine.repos.province.list_all()}
        return [
            ArmyRow(
                name=u.name,
                unit_type=getattr(u.unit_type, "value", str(u.unit_type)),
                soldiers=u.soldiers,
                veterans=u.veterans,
                strength=u.get_total_strength(),
                morale=u.morale,
                fatigue=u.fatigue,
                armor=getattr(u.armor, "value", str(u.armor)),
                status=getattr(u.status, "value", str(u.status)),
                location=provinces.get(u.location_id, str(u.location_id)),
                commander=(
                    commanders.get(u.commander_id, "Unassigned") if u.commander_id else "Unassigned"
                ),
            )
            for u in self._engine.repos.unit.list_all()
        ]

    def get_timeline(self, limit: int | None = 200) -> List[TimelineRow]:
        """Return an observer-facing timeline of summaries, events, and observer logs."""
        rows: list[TimelineRow] = []
        for summary in self._engine.repos.turn_summary.list_all():
            rows.append(
                TimelineRow(
                    date=f"01/{summary.month:02d}/{summary.year:04d}",
                    turn=summary.turn,
                    kind="summary",
                    system="Chronicle",
                    title=summary.title,
                    details=summary.narrative or " | ".join(summary.highlights),
                )
            )
        for event in self._engine.repos.event.list_all():
            rows.append(
                TimelineRow(
                    date=f"{event.day:02d}/{event.month:02d}/{event.year:04d}",
                    turn=event.turn,
                    kind="event",
                    system=event.source_system,
                    title=getattr(event.category, "value", str(event.category)),
                    details=event.description,
                )
            )
        for log in self._engine.repos.observer_log.list_all():
            rows.append(
                TimelineRow(
                    date=f"{log.day:02d}/{log.month:02d}/{log.year:04d}",
                    turn=log.turn,
                    kind="observer",
                    system=log.stream,
                    title=log.source_system,
                    details=log.summary,
                )
            )
        rows.sort(key=lambda r: (r.turn, r.date, r.kind, r.system, r.title), reverse=True)
        return rows if limit is None else rows[:limit]

    def get_events(self, limit: int | None = 200) -> List[EventRow]:
        events = sorted(
            self._engine.repos.event.list_all(),
            key=lambda e: (e.turn, e.id if e.id else 0),
            reverse=True,
        )
        if limit is not None:
            events = events[:limit]
        return [
            EventRow(
                date=f"{e.day:02d}/{e.month:02d}/{e.year:04d}",
                turn=e.turn,
                category=getattr(e.category, "value", str(e.category)),
                actor=e.actor,
                target=e.target or "world",
                source_system=e.source_system,
                description=e.description,
                cause=" → ".join(e.cause_chain) if e.cause_chain else "unspecified",
                impact=e.effect_summary or e.impact,
            )
            for e in events
        ]

    def get_observer_summaries(self) -> List[ObserverSummaryRow]:
        """Return generated daily, weekly, monthly, and yearly summaries for observer views."""
        state = self._engine.game_state
        events = self._engine.repos.event.list_all()
        audits = self._engine.repos.audit_log.list_all()
        observer_logs = self._engine.repos.observer_log.list_all()
        log_years = [item.year for item in [*events, *audits, *observer_logs]]
        chronicle_year = max(log_years, default=state.current_year)
        summaries = [
            self._summary_generator.generate_daily(
                day=state.current_day,
                month=state.current_month,
                year=state.current_year,
                turn=state.current_turn,
                events=events,
                audits=audits,
                observer_logs=observer_logs,
            ),
            self._summary_generator.generate_weekly(
                start_day=max(1, state.current_day - 6),
                start_month=state.current_month,
                start_year=state.current_year,
                end_day=state.current_day,
                end_month=state.current_month,
                end_year=state.current_year,
                turn=state.current_turn,
                events=events,
                audits=audits,
                observer_logs=observer_logs,
            ),
            self._summary_generator.generate_monthly(
                month=state.current_month,
                year=state.current_year,
                turn=state.current_turn,
                events=events,
                audits=audits,
                observer_logs=observer_logs,
            ),
            self._summary_generator.generate_yearly(
                year=chronicle_year,
                turn=state.current_turn,
                events=events,
                audits=audits,
                observer_logs=observer_logs,
            ),
        ]
        return [
            ObserverSummaryRow(
                period=summary.period,
                title=summary.title,
                date_range=summary.date_range,
                turn=summary.turn,
                narrative=summary.narrative,
                event_count=summary.event_count,
                audit_count=summary.audit_count,
                observer_log_count=summary.observer_log_count,
                highlights=" | ".join(summary.highlights),
            )
            for summary in summaries
        ]

    def get_factions(self) -> List[FactionRow]:
        return [
            FactionRow(
                name=f.name,
                faction_type=f.faction_type,
                power_level=f.power_level,
                wealth=f.wealth,
                stability=f.stability,
            )
            for f in self._engine.repos.faction.list_all()
        ]

    def get_relations(self) -> List[RelationRow]:
        factions = {f.id: f.name for f in self._engine.repos.faction.list_all()}
        return [
            RelationRow(
                faction_a=factions.get(r.faction_a_id, str(r.faction_a_id)),
                faction_b=factions.get(r.faction_b_id, str(r.faction_b_id)),
                status=getattr(r.status, "value", str(r.status)),
                opinion=r.opinion,
                trust=r.trust,
                trade_agreement=r.trade_agreement,
                military_alliance=r.military_alliance,
            )
            for r in self._engine.repos.relation.list_all()
        ]

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    def advance_day(self) -> None:
        """Advance the campaign by one in-world day."""
        self._engine.campaign.advance_day()

    def advance_turn(self) -> None:
        """Advance the campaign by one monthly turn."""
        self._engine.campaign.advance_turn()

    def set_simulation_speed(self, speed: str) -> None:
        """Update the live simulation speed state."""
        self._engine.game_state.set_speed(speed)

    def get_speed_interval_ms(self) -> int | None:
        """Return the timer interval for the current speed label."""
        mapping = {
            "paused": None,
            "1x": 1000,
            "2x": 500,
            "5x": 200,
            "fast": 50,
        }
        return mapping[self._engine.game_state.simulation_speed]

    def export_workbook(self, path: Path) -> Path:
        """Export the current campaign state as an Excel workbook."""
        return self._engine.export_campaign(path)

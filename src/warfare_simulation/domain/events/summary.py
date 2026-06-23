"""Observer-facing summary generation for campaign logs.

The generator turns low-level event, audit, and observer-log rows into compact
read models for daily, weekly, and monthly chronicle surfaces. It does not
mutate state; persistence remains the responsibility of the orchestrator when a
monthly summary should be stored as a ``TurnSummary``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Literal

from warfare_simulation.domain.events.models import AuditLog, Event, ObserverLog, TurnSummary

SummaryPeriod = Literal["daily", "weekly", "monthly"]


@dataclass(frozen=True)
class ObserverSummary:
    """Read model for an observer-facing chronicle summary."""

    period: SummaryPeriod
    title: str
    narrative: str
    start_day: int
    start_month: int
    start_year: int
    end_day: int
    end_month: int
    end_year: int
    turn: int
    event_count: int
    audit_count: int
    observer_log_count: int
    highlights: list[str] = field(default_factory=list)

    @property
    def date_range(self) -> str:
        """Return a compact observer-facing date range."""
        start = f"{self.start_day:02d}/{self.start_month:02d}/{self.start_year:04d}"
        end = f"{self.end_day:02d}/{self.end_month:02d}/{self.end_year:04d}"
        return start if start == end else f"{start}–{end}"


class ObserverSummaryGenerator:
    """Build daily, weekly, and monthly summaries from campaign log streams."""

    def generate_daily(
        self,
        *,
        day: int,
        month: int,
        year: int,
        turn: int,
        events: Iterable[Event] = (),
        audits: Iterable[AuditLog] = (),
        observer_logs: Iterable[ObserverLog] = (),
    ) -> ObserverSummary:
        """Generate a single-day observer summary."""
        event_list = [event for event in events if (event.day, event.month, event.year) == (day, month, year)]
        audit_list = [audit for audit in audits if (audit.month, audit.year) == (month, year)]
        log_list = [log for log in observer_logs if (log.day, log.month, log.year) == (day, month, year)]
        highlights = self._highlights(event_list, log_list)
        return ObserverSummary(
            period="daily",
            title=f"Daily Summary — {day:02d}/{month:02d}/{year:04d}",
            narrative=self._narrative("day", event_list, audit_list, log_list),
            start_day=day,
            start_month=month,
            start_year=year,
            end_day=day,
            end_month=month,
            end_year=year,
            turn=turn,
            event_count=len(event_list),
            audit_count=len(audit_list),
            observer_log_count=len(log_list),
            highlights=highlights,
        )

    def generate_weekly(
        self,
        *,
        start_day: int,
        start_month: int,
        start_year: int,
        end_day: int,
        end_month: int,
        end_year: int,
        turn: int,
        events: Iterable[Event] = (),
        audits: Iterable[AuditLog] = (),
        observer_logs: Iterable[ObserverLog] = (),
    ) -> ObserverSummary:
        """Generate a seven-day observer summary for a scheduler week window.

        Current campaign months use a fixed 31-day calendar, so the window
        comparison intentionally uses the in-world ``(year, month, day)`` tuple.
        """
        start = (start_year, start_month, start_day)
        end = (end_year, end_month, end_day)
        event_list = [event for event in events if start <= (event.year, event.month, event.day) <= end]
        audit_list = [audit for audit in audits if start[:2] <= (audit.year, audit.month) <= end[:2]]
        log_list = [log for log in observer_logs if start <= (log.year, log.month, log.day) <= end]
        highlights = self._highlights(event_list, log_list, limit=5)
        return ObserverSummary(
            period="weekly",
            title=f"Weekly Summary — {start_day:02d}/{start_month:02d}/{start_year:04d} to {end_day:02d}/{end_month:02d}/{end_year:04d}",
            narrative=self._narrative("week", event_list, audit_list, log_list),
            start_day=start_day,
            start_month=start_month,
            start_year=start_year,
            end_day=end_day,
            end_month=end_month,
            end_year=end_year,
            turn=turn,
            event_count=len(event_list),
            audit_count=len(audit_list),
            observer_log_count=len(log_list),
            highlights=highlights,
        )

    def generate_monthly(
        self,
        *,
        month: int,
        year: int,
        turn: int,
        events: Iterable[Event] = (),
        audits: Iterable[AuditLog] = (),
        observer_logs: Iterable[ObserverLog] = (),
    ) -> ObserverSummary:
        """Generate a monthly observer summary."""
        event_list = [event for event in events if (event.month, event.year) == (month, year)]
        audit_list = [audit for audit in audits if (audit.month, audit.year) == (month, year)]
        log_list = [log for log in observer_logs if (log.month, log.year) == (month, year)]
        highlights = self._highlights(event_list, log_list, limit=5)
        return ObserverSummary(
            period="monthly",
            title=f"Monthly Summary — Month {month}, Year {year}",
            narrative=self._narrative("month", event_list, audit_list, log_list),
            start_day=1,
            start_month=month,
            start_year=year,
            end_day=31,
            end_month=month,
            end_year=year,
            turn=turn,
            event_count=len(event_list),
            audit_count=len(audit_list),
            observer_log_count=len(log_list),
            highlights=highlights,
        )

    def to_turn_summary(self, summary: ObserverSummary) -> TurnSummary:
        """Convert a monthly observer summary to the persisted summary model."""
        return TurnSummary(
            turn=summary.turn,
            month=summary.end_month,
            year=summary.end_year,
            title=f"Turn {summary.turn} Summary",
            narrative=summary.narrative,
            event_count=summary.event_count,
            audit_count=summary.audit_count,
            highlights=summary.highlights,
        )

    def _highlights(self, events: list[Event], observer_logs: list[ObserverLog], limit: int = 3) -> list[str]:
        highlights = [event.description for event in events[:limit]]
        if len(highlights) < limit:
            highlights.extend(log.summary for log in observer_logs[: limit - len(highlights)])
        return highlights or ["No major campaign events were recorded."]

    def _narrative(
        self,
        period_label: str,
        events: list[Event],
        audits: list[AuditLog],
        observer_logs: list[ObserverLog],
    ) -> str:
        streams = sorted({log.stream for log in observer_logs})
        parts = [
            f"This {period_label} recorded {len(events)} event(s), {len(audits)} auditable state change(s), and {len(observer_logs)} observer log entry(ies)."
        ]
        if streams:
            parts.append(f"Active streams: {', '.join(streams)}.")
        economy = sum(1 for audit in audits if audit.system == "Economy")
        logistics = sum(1 for audit in audits if audit.system == "Logistics")
        if economy:
            parts.append(f"Economy resolved {economy} update(s).")
        if logistics:
            parts.append(f"Logistics resolved {logistics} resource update(s).")
        return " ".join(parts)

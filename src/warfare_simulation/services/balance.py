"""Balance and soak-test read models for Living Chronicle content expansion.

Phase 9 is about adding richness safely.  This module gives developers and the
observer UI a deterministic health report before larger scenario/content packs
are added, so long unattended runs can be checked for impossible state without
mutating the campaign.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


@dataclass(frozen=True)
class BalanceWarning:
    """One detected simulation plausibility issue."""

    subject: str
    metric: str
    value: int
    message: str


@dataclass(frozen=True)
class BalanceHealthReport:
    """Observer/developer-facing summary of scenario balance health."""

    years_simulated: int
    faction_count: int
    province_count: int
    event_count: int
    warning_count: int
    warnings: tuple[BalanceWarning, ...] = field(default_factory=tuple)

    @property
    def status(self) -> str:
        """Return a compact traffic-light label for dashboards and tests."""
        if self.warning_count == 0:
            return "plausible"
        if self.warning_count <= 3:
            return "watch"
        return "unstable"

    @property
    def summary(self) -> str:
        """Return a short text suitable for Phase 9 soak-test logs."""
        return (
            f"{self.years_simulated}-year balance check: {self.status}; "
            f"{self.faction_count} faction(s), {self.province_count} province(s), "
            f"{self.event_count} event(s), {self.warning_count} warning(s)."
        )


class BalanceAnalyzer:
    """Detect impossible or suspicious values in long observer simulations."""

    def build_report(
        self,
        *,
        years_simulated: int,
        factions: Iterable[object] = (),
        provinces: Iterable[object] = (),
        events: Iterable[object] = (),
    ) -> BalanceHealthReport:
        """Build a non-mutating plausibility report from current repository rows."""
        faction_list = list(factions)
        province_list = list(provinces)
        event_list = list(events)
        warnings: list[BalanceWarning] = []

        for faction in faction_list:
            warnings.extend(
                self._bounded_score_warnings(
                    subject=getattr(faction, "name", f"faction:{getattr(faction, 'id', '?')}"),
                    values={
                        "power_level": getattr(faction, "power_level", 0),
                        "wealth": getattr(faction, "wealth", 0),
                        "stability": getattr(faction, "stability", 0),
                    },
                )
            )

        for province in province_list:
            name = getattr(province, "name", f"province:{getattr(province, 'id', '?')}")
            warnings.extend(
                self._bounded_score_warnings(
                    subject=name,
                    values={"loyalty": getattr(province, "loyalty", 0)},
                )
            )
            for metric in ("population", "food_stored", "monthly_tax", "garrison_size"):
                value = getattr(province, metric, 0)
                if value < 0:
                    warnings.append(
                        BalanceWarning(
                            subject=name,
                            metric=metric,
                            value=value,
                            message=f"{metric} cannot be negative in a plausible scenario.",
                        )
                    )
            garrison = getattr(province, "garrison_size", 0)
            capacity = getattr(province, "garrison_capacity", 0)
            if capacity >= 0 and garrison > capacity:
                warnings.append(
                    BalanceWarning(
                        subject=name,
                        metric="garrison_size",
                        value=garrison,
                        message="Garrison exceeds the province capacity.",
                    )
                )

        return BalanceHealthReport(
            years_simulated=years_simulated,
            faction_count=len(faction_list),
            province_count=len(province_list),
            event_count=len(event_list),
            warning_count=len(warnings),
            warnings=tuple(warnings),
        )

    def _bounded_score_warnings(
        self, *, subject: str, values: dict[str, int]
    ) -> list[BalanceWarning]:
        warnings: list[BalanceWarning] = []
        for metric, value in values.items():
            if not 0 <= value <= 100:
                warnings.append(
                    BalanceWarning(
                        subject=subject,
                        metric=metric,
                        value=value,
                        message=f"{metric} should remain within 0-100.",
                    )
                )
        return warnings

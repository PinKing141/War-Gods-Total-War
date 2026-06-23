"""Internal politics pressure and collapse checks for autonomous factions."""

from dataclasses import dataclass, field
from typing import Iterable

from warfare_simulation.domain.diplomacy.models import Faction


@dataclass(frozen=True)
class PoliticalCrisis:
    """A resolved internal-politics crisis candidate."""

    faction_id: int
    faction_name: str
    crisis_type: str
    severity: int
    stability_delta: int
    previous_stability: int
    new_stability: int
    description: str
    cause_chain: list[str] = field(default_factory=list)
    pressure: dict[str, int] = field(default_factory=dict)


class InternalPoliticsEngine:
    """Deterministic first slice of Living Chronicle internal politics."""

    def evaluate(self, factions: Iterable[Faction]) -> list[PoliticalCrisis]:
        """Return crises for factions whose internal pressure crosses the audible threshold."""
        crises: list[PoliticalCrisis] = []
        for faction in sorted(factions, key=lambda item: item.id):
            pressure = self._pressure_for(faction)
            severity = sum(pressure.values())
            if severity < 60:
                continue

            if severity >= 95 or faction.stability <= 10:
                crisis_type = "collapse"
                stability_delta = -20
                description = (
                    f"{faction.name} entered collapse as legitimacy, public order, and noble loyalty failed."
                )
            elif severity >= 80:
                crisis_type = "coup"
                stability_delta = -15
                description = f"{faction.name} suffered a coup attempt amid severe court instability."
            else:
                crisis_type = "revolt"
                stability_delta = -10
                description = f"{faction.name} faced a revolt driven by internal political pressure."

            previous = faction.stability
            new_stability = max(0, previous + stability_delta)
            crises.append(
                PoliticalCrisis(
                    faction_id=faction.id,
                    faction_name=faction.name,
                    crisis_type=crisis_type,
                    severity=severity,
                    stability_delta=stability_delta,
                    previous_stability=previous,
                    new_stability=new_stability,
                    description=description,
                    pressure=pressure,
                    cause_chain=[
                        "monthly_pulse",
                        "evaluate_internal_politics",
                        f"legitimacy_pressure:{pressure['legitimacy']}",
                        f"public_order_pressure:{pressure['public_order']}",
                        f"noble_loyalty_pressure:{pressure['noble_loyalty']}",
                        f"tax_burden_pressure:{pressure['tax_burden']}",
                        f"war_exhaustion_pressure:{pressure['war_exhaustion']}",
                        f"crisis:{crisis_type}",
                    ],
                )
            )
        return crises

    def _pressure_for(self, faction: Faction) -> dict[str, int]:
        instability = max(0, 100 - faction.stability)
        debt_pressure = max(0, 40 - faction.wealth)
        weak_army_pressure = max(0, 35 - faction.power_level)
        return {
            "legitimacy": instability // 2,
            "public_order": instability // 3,
            "noble_loyalty": max(0, instability - 45),
            "tax_burden": debt_pressure,
            "war_exhaustion": weak_army_pressure,
        }

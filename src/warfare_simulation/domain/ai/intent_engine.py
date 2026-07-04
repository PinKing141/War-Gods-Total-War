"""Intent selection for the historical AI loop."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from .pressure_engine import HistoricalPressure


@dataclass(frozen=True)
class HistoricalIntent:
    """Concrete intent selected from a faction pressure."""

    faction_id: int
    faction_name: str
    seed_faction_id: str
    intent_type: str
    target_faction_id: int | None
    target_faction_name: str
    target_seed_faction_id: str
    province_id: int | None
    province_name: str
    seed_province_id: str
    claim_id: str
    claim_type: str
    confidence: int
    risk: int
    reason: str
    pressure: HistoricalPressure
    action_scope: str = "diplomacy"
    causes: list[str] = field(default_factory=list)

    @property
    def cause_chain(self) -> list[str]:
        """Return the causal chain up to intent selection."""
        return [
            "monthly_pulse",
            "historical_pressure",
            f"pressure:{self.pressure.top_pressure}:{self.pressure.intensity}",
            f"intent:{self.intent_type}",
        ]

    def as_dict(self) -> dict[str, Any]:
        return {
            "faction_id": self.faction_id,
            "faction_name": self.faction_name,
            "seed_faction_id": self.seed_faction_id,
            "intent_type": self.intent_type,
            "target_faction_id": self.target_faction_id,
            "target_faction_name": self.target_faction_name,
            "target_seed_faction_id": self.target_seed_faction_id,
            "province_id": self.province_id,
            "province_name": self.province_name,
            "seed_province_id": self.seed_province_id,
            "claim_id": self.claim_id,
            "claim_type": self.claim_type,
            "confidence": self.confidence,
            "risk": self.risk,
            "reason": self.reason,
            "action_scope": self.action_scope,
            "causes": list(self.causes),
            "pressure": self.pressure.as_dict(),
        }


class HistoricalIntentEngine:
    """Choose concrete historical-loop intents from pressure."""

    def generate_intents(self, pressures: Iterable[HistoricalPressure]) -> list[HistoricalIntent]:
        intents = [self.choose_intent(pressure) for pressure in pressures]
        return sorted(
            intents,
            key=lambda intent: (intent.confidence, intent.pressure.intensity, intent.faction_id),
            reverse=True,
        )

    def choose_intent(self, pressure: HistoricalPressure) -> HistoricalIntent:
        if pressure.top_pressure == "service_yoke_claim":
            intent_type = "press_service_yoke_claim"
            reason = (
                f"Strong old imperial claim, {pressure.culture_name or pressure.culture_id} "
                f"road-law pressure, and {pressure.target_faction_name} resistance."
            )
        elif pressure.top_pressure == "service_yoke_resistance":
            intent_type = "demand_recognition"
            reason = (
                f"{pressure.faction_name} controls {pressure.province_name} and rejects "
                f"{pressure.target_faction_name}'s service-yoke claim."
            )
        elif pressure.top_pressure == "defend_claimed_land":
            intent_type = "refuse_tax"
            reason = f"{pressure.faction_name} resists an outside claim on {pressure.province_name}."
        else:
            intent_type = "enforce_contract"
            reason = f"{pressure.faction_name} tries to turn {pressure.top_pressure} into leverage."

        confidence = self._clamp(pressure.intensity - pressure.war_risk // 8, 0, 100)
        risk = self._clamp(pressure.war_risk + max(0, pressure.intensity - 75) // 2, 0, 100)
        return HistoricalIntent(
            faction_id=pressure.faction_id,
            faction_name=pressure.faction_name,
            seed_faction_id=pressure.seed_faction_id,
            intent_type=intent_type,
            target_faction_id=pressure.target_faction_id,
            target_faction_name=pressure.target_faction_name,
            target_seed_faction_id=pressure.target_seed_faction_id,
            province_id=pressure.province_id,
            province_name=pressure.province_name,
            seed_province_id=pressure.seed_province_id,
            claim_id=pressure.claim_id,
            claim_type=pressure.claim_type,
            confidence=confidence,
            risk=risk,
            reason=reason,
            pressure=pressure,
            action_scope="diplomacy" if intent_type != "refuse_tax" else "politics",
            causes=list(pressure.causes),
        )

    @staticmethod
    def _clamp(value: int, minimum: int, maximum: int) -> int:
        return max(minimum, min(maximum, value))

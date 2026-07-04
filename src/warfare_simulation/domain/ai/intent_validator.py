"""Validation for historical AI intents."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from warfare_simulation.persistence.database import DatabaseManager

from .intent_engine import HistoricalIntent


@dataclass(frozen=True)
class ValidatedIntent:
    """Validation result for a historical AI intent."""

    intent: HistoricalIntent
    accepted: bool
    reason: str
    risks: list[str] = field(default_factory=list)
    checks: dict[str, Any] = field(default_factory=dict)

    @property
    def cause_chain(self) -> list[str]:
        return [
            *self.intent.cause_chain,
            "validate_intent" if self.accepted else "reject_intent",
        ]

    def as_dict(self) -> dict[str, Any]:
        return {
            "accepted": self.accepted,
            "reason": self.reason,
            "risks": list(self.risks),
            "checks": dict(self.checks),
            "intent": self.intent.as_dict(),
        }


class IntentValidator:
    """Check whether selected historical intents can proceed."""

    def validate(self, db: DatabaseManager, intent: HistoricalIntent) -> ValidatedIntent:
        checks: dict[str, Any] = {
            "faction_exists": self._exists(db, "faction", intent.faction_id),
            "target_exists": (
                intent.target_faction_id is not None
                and self._exists(db, "faction", intent.target_faction_id)
            ),
            "province_exists": (
                intent.province_id is not None
                and self._exists(db, "province", intent.province_id)
            ),
            "claim_exists": bool(self._claim_row(db, intent.claim_id)),
            "relation_exists": intent.pressure.relation_id is not None,
        }
        province = self._province_row(db, intent.province_id)
        checks["food_stored"] = province["food_stored"] if province else 0
        checks["road_level"] = province["road_level"] if province else 0
        checks["religion_war_stance"] = intent.pressure.religion_war_stance

        missing = [
            name
            for name in ("faction_exists", "target_exists", "province_exists", "claim_exists")
            if not checks[name]
        ]
        risks = self._risks(intent, checks)
        if missing:
            return ValidatedIntent(
                intent=intent,
                accepted=False,
                reason=f"Missing required world state: {', '.join(missing)}.",
                risks=risks,
                checks=checks,
            )
        if intent.intent_type == "press_service_yoke_claim" and checks["food_stored"] < 8_000:
            return ValidatedIntent(
                intent=intent,
                accepted=False,
                reason="Winter stores fell below campaign safety for pressing the claim.",
                risks=risks,
                checks=checks,
            )
        if intent.intent_type == "press_service_yoke_claim" and checks["road_level"] <= 0:
            return ValidatedIntent(
                intent=intent,
                accepted=False,
                reason="The target cannot be reached by a usable road or route.",
                risks=risks,
                checks=checks,
            )

        reason = "Claim exists, food is sufficient, and the target is reachable."
        if intent.pressure.old_imperial_name:
            reason += f" Old records name the place as {intent.pressure.old_imperial_name}."
        return ValidatedIntent(
            intent=intent,
            accepted=True,
            reason=reason,
            risks=risks,
            checks=checks,
        )

    def _risks(self, intent: HistoricalIntent, checks: dict[str, Any]) -> list[str]:
        risks: list[str] = []
        if intent.risk >= 60:
            risks.append(f"War risk is high at {intent.risk}")
        if intent.pressure.relation_score < -50:
            risks.append(f"Existing relation is hostile at {intent.pressure.relation_score}")
        if "conditional" in str(checks.get("religion_war_stance", "")):
            risks.append("Religious approval depends on oath/legal framing")
        if intent.pressure.target_faction_name:
            risks.append(f"{intent.pressure.target_faction_name} resistance expected")
        return risks

    @staticmethod
    def _exists(db: DatabaseManager, table: str, row_id: int | None) -> bool:
        if row_id is None:
            return False
        return db.execute(f"SELECT 1 FROM {table} WHERE id = ?", (row_id,)).fetchone() is not None

    @staticmethod
    def _claim_row(db: DatabaseManager, claim_id: str) -> dict[str, Any] | None:
        cursor = db.execute("SELECT * FROM claim WHERE claim_id = ?", (claim_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        columns = [column[0] for column in cursor.description]
        return dict(zip(columns, row))

    @staticmethod
    def _province_row(db: DatabaseManager, province_id: int | None) -> dict[str, Any] | None:
        if province_id is None:
            return None
        cursor = db.execute("SELECT * FROM province WHERE id = ?", (province_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        columns = [column[0] for column in cursor.description]
        return dict(zip(columns, row))

"""State mutation for validated historical AI actions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from warfare_simulation.persistence.database import DatabaseManager

from .intent_validator import ValidatedIntent


@dataclass(frozen=True)
class HistoricalActionResult:
    """Result of resolving a validated historical intent."""

    validated_intent: ValidatedIntent
    action_type: str
    accepted: bool
    state_changes: dict[str, dict[str, Any]] = field(default_factory=dict)
    event_summary: str = ""
    effect_summary: str = ""

    @property
    def cause_chain(self) -> list[str]:
        return [
            *self.validated_intent.cause_chain,
            f"action:{self.action_type}" if self.accepted else "action:logged_rejection",
        ]

    def as_dict(self) -> dict[str, Any]:
        return {
            "action_type": self.action_type,
            "accepted": self.accepted,
            "state_changes": dict(self.state_changes),
            "event_summary": self.event_summary,
            "effect_summary": self.effect_summary,
            "validated_intent": self.validated_intent.as_dict(),
        }


class ActionResolver:
    """Apply accepted historical intents to mutable runtime state."""

    def resolve(self, db: DatabaseManager, validated: ValidatedIntent) -> HistoricalActionResult:
        intent = validated.intent
        if not validated.accepted:
            return HistoricalActionResult(
                validated_intent=validated,
                action_type=intent.intent_type,
                accepted=False,
                event_summary=(
                    f"{intent.faction_name} considered {intent.intent_type} "
                    f"against {intent.target_faction_name}, but stopped: {validated.reason}"
                ),
                effect_summary="No state changed; the rejected intent remains part of the record.",
            )

        if intent.intent_type == "press_service_yoke_claim":
            return self._resolve_press_claim(db, validated)
        if intent.intent_type == "demand_recognition":
            return self._resolve_demand_recognition(db, validated)
        if intent.intent_type == "refuse_tax":
            return self._resolve_refuse_tax(db, validated)
        return self._resolve_diplomacy_pressure(db, validated)

    def _resolve_press_claim(
        self,
        db: DatabaseManager,
        validated: ValidatedIntent,
    ) -> HistoricalActionResult:
        intent = validated.intent
        relation_change = self._shift_relation(
            db,
            intent.pressure.relation_id,
            opinion_delta=-6,
            trust_delta=-4,
            war_risk_delta=6,
        )
        province_change = self._shift_province_loyalty(
            db,
            intent.province_id,
            delta=-3,
        )
        return HistoricalActionResult(
            validated_intent=validated,
            action_type=intent.intent_type,
            accepted=True,
            state_changes={
                "relation": relation_change,
                "province": province_change,
            },
            event_summary=(
                f"{intent.faction_name} renewed {intent.claim_type} over "
                f"{intent.province_name}."
            ),
            effect_summary=(
                "Relations worsened and the claimed province grew less loyal under renewed "
                "legal pressure."
            ),
        )

    def _resolve_demand_recognition(
        self,
        db: DatabaseManager,
        validated: ValidatedIntent,
    ) -> HistoricalActionResult:
        intent = validated.intent
        relation_change = self._shift_relation(
            db,
            intent.pressure.relation_id,
            opinion_delta=-4,
            trust_delta=-2,
            war_risk_delta=3,
        )
        province_change = self._shift_province_loyalty(
            db,
            intent.province_id,
            delta=2,
        )
        return HistoricalActionResult(
            validated_intent=validated,
            action_type=intent.intent_type,
            accepted=True,
            state_changes={
                "relation": relation_change,
                "province": province_change,
            },
            event_summary=(
                f"{intent.faction_name} demanded recognition over {intent.province_name}."
            ),
            effect_summary=(
                "The demand hardened diplomatic lines while improving local loyalty among "
                "supporters."
            ),
        )

    def _resolve_refuse_tax(
        self,
        db: DatabaseManager,
        validated: ValidatedIntent,
    ) -> HistoricalActionResult:
        intent = validated.intent
        relation_change = self._shift_relation(
            db,
            intent.pressure.relation_id,
            opinion_delta=-3,
            trust_delta=-2,
            war_risk_delta=2,
        )
        return HistoricalActionResult(
            validated_intent=validated,
            action_type=intent.intent_type,
            accepted=True,
            state_changes={"relation": relation_change},
            event_summary=f"{intent.faction_name} refused outside tax pressure.",
            effect_summary="Diplomatic trust fell after the refusal.",
        )

    def _resolve_diplomacy_pressure(
        self,
        db: DatabaseManager,
        validated: ValidatedIntent,
    ) -> HistoricalActionResult:
        intent = validated.intent
        relation_change = self._shift_relation(
            db,
            intent.pressure.relation_id,
            opinion_delta=-2,
            trust_delta=-1,
            war_risk_delta=1,
        )
        return HistoricalActionResult(
            validated_intent=validated,
            action_type=intent.intent_type,
            accepted=True,
            state_changes={"relation": relation_change},
            event_summary=f"{intent.faction_name} turned pressure into a diplomatic crisis.",
            effect_summary="The pressure damaged diplomatic trust.",
        )

    def _shift_relation(
        self,
        db: DatabaseManager,
        relation_id: int | None,
        *,
        opinion_delta: int,
        trust_delta: int,
        war_risk_delta: int,
    ) -> dict[str, Any]:
        if relation_id is None:
            return {}
        row = db.execute(
            "SELECT opinion, trust, war_risk, status FROM relation WHERE id = ?",
            (relation_id,),
        ).fetchone()
        if row is None:
            return {}
        previous = {
            "opinion": int(row[0]),
            "trust": int(row[1]),
            "war_risk": int(row[2] or 0),
            "status": row[3],
        }
        new = {
            "opinion": self._clamp(previous["opinion"] + opinion_delta, -100, 100),
            "trust": self._clamp(previous["trust"] + trust_delta, -100, 100),
            "war_risk": self._clamp(previous["war_risk"] + war_risk_delta, 0, 100),
            "status": previous["status"],
        }
        if new["opinion"] <= -50 or new["war_risk"] >= 70:
            new["status"] = "ENEMY"
        elif new["opinion"] <= -20:
            new["status"] = "RIVAL"

        db.execute(
            """
            UPDATE relation
            SET opinion = ?, trust = ?, war_risk = ?, status = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (new["opinion"], new["trust"], new["war_risk"], new["status"], relation_id),
        )
        return {"id": relation_id, "previous": previous, "new": new}

    def _shift_province_loyalty(
        self,
        db: DatabaseManager,
        province_id: int | None,
        *,
        delta: int,
    ) -> dict[str, Any]:
        if province_id is None:
            return {}
        row = db.execute("SELECT loyalty FROM province WHERE id = ?", (province_id,)).fetchone()
        if row is None:
            return {}
        previous = {"loyalty": int(row[0])}
        new = {"loyalty": self._clamp(previous["loyalty"] + delta, 0, 100)}
        db.execute(
            """
            UPDATE province
            SET loyalty = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (new["loyalty"], province_id),
        )
        return {"id": province_id, "previous": previous, "new": new}

    @staticmethod
    def _clamp(value: int, minimum: int, maximum: int) -> int:
        return max(minimum, min(maximum, value))

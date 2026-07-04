"""Format historical-loop reasons into readable chronicle prose."""

from __future__ import annotations

from warfare_simulation.domain.ai.action_resolver import HistoricalActionResult


class ChronicleReasonFormatter:
    """Turn pressure/intent/action records into observer-facing history."""

    def format_action(self, result: HistoricalActionResult) -> str:
        validated = result.validated_intent
        intent = validated.intent
        pressure = intent.pressure

        if not result.accepted:
            return (
                f"{intent.faction_name} considered {intent.intent_type} over "
                f"{intent.province_name}, but abandoned the plan: {validated.reason}"
            )

        if intent.intent_type == "press_service_yoke_claim":
            return self._format_press_service_yoke(result)
        if intent.intent_type == "demand_recognition":
            return self._format_demand_recognition(result)
        if intent.intent_type == "refuse_tax":
            return (
                f"{intent.faction_name} refused outside tax pressure around "
                f"{intent.province_name}; the dispute now follows "
                f"{pressure.claim_source or 'older records'}."
            )
        return (
            f"{intent.faction_name} acted on {pressure.top_pressure} around "
            f"{intent.province_name}: {intent.reason}"
        )

    def _format_press_service_yoke(self, result: HistoricalActionResult) -> str:
        intent = result.validated_intent.intent
        pressure = intent.pressure
        old_name = f", named in old records as {pressure.old_imperial_name}" if pressure.old_imperial_name else ""
        religion = (
            f" {pressure.religion_name} doctrine frames war as {pressure.religion_war_stance}."
            if pressure.religion_name and pressure.religion_war_stance
            else ""
        )
        target_reply = (
            f" {intent.target_faction_name} answered through the old grievance of service-yoke rule."
            if intent.target_faction_name
            else ""
        )
        return (
            f"{intent.faction_name} renewed the {intent.claim_type} over "
            f"{intent.province_name}{old_name}, citing {pressure.claim_source}. "
            f"{pressure.culture_name or pressure.culture_id} records cast the matter as road law "
            f"and inheritance rather than conquest.{target_reply}{religion}"
        )

    def _format_demand_recognition(self, result: HistoricalActionResult) -> str:
        intent = result.validated_intent.intent
        pressure = intent.pressure
        return (
            f"{intent.faction_name} demanded recognition at {intent.province_name}, "
            f"arguing that {pressure.claim_source} cannot bind freeholders forever. "
            f"The dispute with {intent.target_faction_name} now turns on "
            f"{pressure.claim_type} and oath memory."
        )

"""Autonomous faction pressure evaluation and intent selection.

This module is the first thin slice of the Living Chronicle direction: factions
inspect their own state, choose a simple strategic posture, and expose the cause
chain needed for observer logs before any deep diplomatic mechanics are added.
"""

from dataclasses import dataclass
from typing import Iterable

from warfare_simulation.core.constants import FactionStatus
from warfare_simulation.domain.diplomacy.models import Faction, Relation


@dataclass(frozen=True)
class FactionPressure:
    """Readable pressure scores that explain why a faction chose an intent."""

    faction_id: int
    faction_name: str
    stability: int
    economy: int
    military: int
    diplomatic: int

    @property
    def dominant(self) -> str:
        """Return the highest-pressure axis, using stable tie-break ordering."""
        ordered = [
            ("stability", self.stability),
            ("economy", self.economy),
            ("military", self.military),
            ("diplomatic", self.diplomatic),
        ]
        return max(ordered, key=lambda item: item[1])[0]

    def as_dict(self) -> dict[str, int | str]:
        """Serialize the pressure model for observer-log details."""
        return {
            "faction_id": self.faction_id,
            "faction_name": self.faction_name,
            "stability": self.stability,
            "economy": self.economy,
            "military": self.military,
            "diplomatic": self.diplomatic,
            "dominant": self.dominant,
        }


@dataclass(frozen=True)
class FactionIntent:
    """A validated strategic choice produced by an autonomous faction."""

    faction_id: int
    faction_name: str
    intent_type: str
    description: str
    pressure: FactionPressure
    valid: bool = True
    failure_reason: str = ""
    personality_traits: tuple[str, ...] = ()
    weighted_scores: dict[str, int] | None = None

    @property
    def cause_chain(self) -> list[str]:
        """Explain the choice in compact, log-friendly terms."""
        return [
            "monthly_pulse",
            "evaluate_faction_pressure",
            f"dominant_pressure:{self.pressure.dominant}",
            f"intent:{self.intent_type}",
            f"personality:{','.join(self.personality_traits) or 'balanced'}",
            "validate_intent" if self.valid else "reject_intent",
        ]


class FactionIntentEngine:
    """Deterministic personality-weighted pressure-to-intent engine."""

    _AXES = ("stability", "economy", "military", "diplomatic")
    _TRAIT_WEIGHTS = {
        "cautious": {"stability": 15, "diplomatic": 10},
        "mercantile": {"economy": 20, "diplomatic": 5},
        "militant": {"military": 20, "diplomatic": 10},
        "pragmatic": {"economy": 10, "stability": 10},
        "diplomatic": {"diplomatic": 20, "economy": 5},
        "authoritarian": {"stability": 20, "military": 5},
    }

    def normalize_personality_traits(self, faction: Faction) -> tuple[str, ...]:
        """Return stable lowercase personality traits used by the selector."""
        return tuple(
            trait.strip().lower()
            for trait in faction.personality_traits.split(",")
            if trait.strip()
        )

    def score_intent_axes(
        self, pressure: FactionPressure, personality_traits: Iterable[str]
    ) -> dict[str, int]:
        """Apply ruler personality weights to pressure axes deterministically."""
        scores = {axis: int(getattr(pressure, axis)) for axis in self._AXES}
        for trait in personality_traits:
            for axis, bonus in self._TRAIT_WEIGHTS.get(trait, {}).items():
                scores[axis] += bonus
        return scores

    def evaluate_pressure(self, faction: Faction, relations: Iterable[Relation]) -> FactionPressure:
        """Score pressure from current faction stats and known relations."""
        related = [
            relation
            for relation in relations
            if faction.id in {relation.faction_a_id, relation.faction_b_id}
        ]
        worst_opinion_pressure = max((max(0, -relation.opinion) for relation in related), default=0)
        hostile_status_pressure = max(
            (
                35
                for relation in related
                if relation.status in {FactionStatus.ENEMY, FactionStatus.RIVAL}
            ),
            default=0,
        )
        return FactionPressure(
            faction_id=faction.id,
            faction_name=faction.name,
            stability=max(0, 100 - faction.stability),
            economy=max(0, 100 - faction.wealth),
            military=max(0, 100 - faction.power_level),
            diplomatic=max(worst_opinion_pressure, hostile_status_pressure),
        )

    def choose_intent(
        self, pressure: FactionPressure, personality_traits: Iterable[str] = ()
    ) -> FactionIntent:
        """Choose one strategic intent using pressure plus ruler personality weights."""
        intent_map = {
            "stability": (
                "stabilize_realm",
                "contain unrest and reinforce internal legitimacy",
            ),
            "economy": (
                "replenish_treasury",
                "prioritize revenue, trade, and stored wealth",
            ),
            "military": (
                "rebuild_forces",
                "preserve security by rebuilding military capacity",
            ),
            "diplomatic": (
                "watch_rivals",
                "monitor rivals and avoid diplomatic surprise",
            ),
        }
        traits = tuple(personality_traits)
        weighted_scores = self.score_intent_axes(pressure, traits)
        selected_axis = max(
            self._AXES,
            key=lambda axis: (weighted_scores[axis], -self._AXES.index(axis)),
        )
        intent_type, description = intent_map[selected_axis]
        return self.validate_intent(
            FactionIntent(
                faction_id=pressure.faction_id,
                faction_name=pressure.faction_name,
                intent_type=intent_type,
                description=description,
                pressure=pressure,
                personality_traits=traits,
                weighted_scores=weighted_scores,
            )
        )

    def validate_intent(self, intent: FactionIntent) -> FactionIntent:
        """Validate an intent before it is allowed to mutate state.

        Phase 1A only records posture; it intentionally avoids deep state
        mutation. The validation hook exists so future concrete intents can fail
        audibly instead of silently doing nothing.
        """
        if intent.faction_id <= 0:
            return FactionIntent(
                faction_id=intent.faction_id,
                faction_name=intent.faction_name,
                intent_type=intent.intent_type,
                description=intent.description,
                pressure=intent.pressure,
                valid=False,
                personality_traits=intent.personality_traits,
                weighted_scores=intent.weighted_scores,
                failure_reason="Faction intent requires a persisted faction id.",
            )
        return intent

    def generate_intents(
        self,
        factions: Iterable[Faction],
        relations: Iterable[Relation],
    ) -> list[FactionIntent]:
        """Evaluate every faction and return deterministic monthly intents."""
        relation_list = list(relations)
        return [
            self.choose_intent(
                self.evaluate_pressure(faction, relation_list),
                self.normalize_personality_traits(faction),
            )
            for faction in sorted(factions, key=lambda item: item.id)
        ]

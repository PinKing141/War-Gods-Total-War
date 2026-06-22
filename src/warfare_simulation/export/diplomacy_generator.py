"""
Generates the 'Diplomacy & Intel' sheet.
"""

from openpyxl.workbook import Workbook
from typing import Any, Optional

DiplomacyRepository = Any

from .base_generator import SheetGenerator
from .styles import StyleManager


class DiplomacyGenerator(SheetGenerator):
    """Generates the 'Diplomacy & Intel' sheet."""

    def __init__(self, workbook: Workbook, style_manager: StyleManager, diplomacy_repo: Optional[DiplomacyRepository] = None):
        super().__init__("Diplomacy & Intel", workbook, style_manager)
        self.diplomacy_repo = diplomacy_repo

    def generate(self) -> None:
        """Generates the full diplomacy and intel sheet."""
        super().generate()

        headers = ["Faction/Agent", "Type", "Opinion/Risk", "Status", "Notes/Mission"]
        self._format_header(headers)

        relation_repo = getattr(self.diplomacy_repo, "relation", None)
        faction_repo = getattr(self.diplomacy_repo, "faction", self.diplomacy_repo)
        if relation_repo is not None and hasattr(relation_repo, "list_all"):
            relations = relation_repo.list_all()
            if relations:
                factions = {}
                if faction_repo is not None and hasattr(faction_repo, "list_all"):
                    factions = {faction.id: faction for faction in faction_repo.list_all()}

                self._append_data([
                    [
                        self._relation_name(relation, factions),
                        getattr(relation.status, "value", str(relation.status)),
                        f"{relation.opinion:+d} opinion / {relation.trust:+d} trust",
                        self._relation_status(relation),
                        self._relation_notes(relation, factions),
                    ]
                    for relation in relations
                ])
                return

        intel_data = [
            ["Republic of Tyra", "Nation (Ally)", "+89", "Trade Pact Active", "Supplies gold and exotic goods for iron."],
            ["Empire of Volantis", "Nation (Rival)", "-85", "Cold War", "Expansionist empire to the south. Tensions high."],
            ["Raven 1 (Kael's Network)", "Spy", "12% Risk", "Active", "Scouting Volantis border troop movements."],
            ["Raven 2 (Kael's Network)", "Spy", "40% Risk", "Active", "Infiltrating Volantis military command."],
        ]
        self._append_data(intel_data)

    @staticmethod
    def _relation_name(relation, factions: dict) -> str:
        faction_a = factions.get(relation.faction_a_id)
        faction_b = factions.get(relation.faction_b_id)
        name_a = faction_a.name if faction_a is not None else str(relation.faction_a_id)
        name_b = faction_b.name if faction_b is not None else str(relation.faction_b_id)
        return f"{name_a} <-> {name_b}"

    @staticmethod
    def _relation_status(relation) -> str:
        pacts = []
        if relation.trade_agreement:
            pacts.append("Trade Agreement")
        if relation.military_alliance:
            pacts.append("Military Alliance")
        return ", ".join(pacts) if pacts else "No formal pact"

    @staticmethod
    def _relation_notes(relation, factions: dict) -> str:
        faction_a = factions.get(relation.faction_a_id)
        faction_b = factions.get(relation.faction_b_id)
        if faction_a is None or faction_b is None:
            return ""
        return f"{faction_a.government_type} vs {faction_b.government_type}"
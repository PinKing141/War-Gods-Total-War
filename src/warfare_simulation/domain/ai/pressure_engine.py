"""Pressure evaluation for the activated seed-frontier historical loop."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from warfare_simulation.persistence.database import DatabaseManager


@dataclass(frozen=True)
class HistoricalPressure:
    """A faction-level reason to act in the historical loop."""

    faction_id: int
    faction_name: str
    seed_faction_id: str
    top_pressure: str
    intensity: int
    causes: list[str] = field(default_factory=list)
    claim_id: str = ""
    claim_type: str = ""
    claim_source: str = ""
    recognized_by: str = ""
    target_faction_id: int | None = None
    target_faction_name: str = ""
    target_seed_faction_id: str = ""
    province_id: int | None = None
    province_name: str = ""
    seed_province_id: str = ""
    old_imperial_name: str = ""
    relation_id: int | None = None
    relation_score: int = 0
    war_risk: int = 0
    culture_id: str = ""
    culture_name: str = ""
    religion_id: str = ""
    religion_name: str = ""
    religion_war_stance: str = ""
    modifiers: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        """Serialize for logs and validation records."""
        return {
            "faction_id": self.faction_id,
            "faction_name": self.faction_name,
            "seed_faction_id": self.seed_faction_id,
            "top_pressure": self.top_pressure,
            "intensity": self.intensity,
            "causes": list(self.causes),
            "claim_id": self.claim_id,
            "claim_type": self.claim_type,
            "claim_source": self.claim_source,
            "recognized_by": self.recognized_by,
            "target_faction_id": self.target_faction_id,
            "target_faction_name": self.target_faction_name,
            "target_seed_faction_id": self.target_seed_faction_id,
            "province_id": self.province_id,
            "province_name": self.province_name,
            "seed_province_id": self.seed_province_id,
            "old_imperial_name": self.old_imperial_name,
            "relation_id": self.relation_id,
            "relation_score": self.relation_score,
            "war_risk": self.war_risk,
            "culture_id": self.culture_id,
            "culture_name": self.culture_name,
            "religion_id": self.religion_id,
            "religion_name": self.religion_name,
            "religion_war_stance": self.religion_war_stance,
            "modifiers": dict(self.modifiers),
        }


class PressureEngine:
    """Derive actionable faction pressure from active seed-frontier state."""

    def evaluate(self, db: DatabaseManager) -> list[HistoricalPressure]:
        if not db.conn or not db.table_exists("seed_frontier_runtime_map"):
            return []

        claim_rows = self._fetch_dicts(
            db,
            """
            SELECT
                c.claim_id,
                c.claimant,
                c.target,
                c.claim_type,
                c.source,
                c.strength,
                c.myth_status,
                c.recognized_by,
                c.active_claimant_faction_id,
                c.active_target_province_id,
                claimant.name AS claimant_name,
                claimant.seed_faction_id AS claimant_seed_faction_id,
                claimant.dominant_culture AS claimant_culture_id,
                claimant.religion_id AS claimant_religion_id,
                p.name AS province_name,
                p.seed_province_id,
                p.controller_faction_id,
                p.food_stored,
                p.road_level,
                p.strategic_value,
                sp.old_imperial_name,
                controller.name AS controller_name,
                controller.seed_faction_id AS controller_seed_faction_id,
                controller.dominant_culture AS controller_culture_id,
                controller.religion_id AS controller_religion_id
            FROM claim c
            JOIN faction claimant ON claimant.id = c.active_claimant_faction_id
            JOIN province p ON p.id = c.active_target_province_id
            LEFT JOIN seed_province sp ON sp.province_id = p.seed_province_id
            LEFT JOIN faction controller ON controller.id = p.controller_faction_id
            WHERE c.active_claimant_faction_id IS NOT NULL
              AND c.active_target_province_id IS NOT NULL
            ORDER BY c.strength DESC, c.claim_id
            """,
        )

        pressures: list[HistoricalPressure] = []
        for row in claim_rows:
            relation = self._relation_between(
                db,
                row["active_claimant_faction_id"],
                row["controller_faction_id"],
            )
            pressures.append(self._claimant_pressure(db, row, relation))
            if row["controller_faction_id"] and row["controller_faction_id"] != row["active_claimant_faction_id"]:
                pressures.append(self._controller_pressure(db, row, relation))

        return pressures

    def _claimant_pressure(
        self,
        db: DatabaseManager,
        row: dict[str, Any],
        relation: dict[str, Any],
    ) -> HistoricalPressure:
        culture_name = self._culture_name(db, row["claimant_culture_id"])
        religion = self._religion(db, row["claimant_religion_id"])
        modifiers = self._combined_modifiers(
            db,
            row["claimant_culture_id"],
            row["claimant_religion_id"],
        )
        relation_score = int(relation.get("opinion") or 0)
        war_risk = int(relation.get("war_risk") or 0)
        road_priority = self._int_modifier(modifiers, "road_control_priority")
        lawful_claim_weight = max(
            self._int_modifier(modifiers, "legal_claim_weight"),
            self._int_modifier(modifiers, "lawful_claim_weight"),
        )
        intensity = self._clamp(
            int(row["strength"])
            + int(row["strategic_value"]) // 6
            + road_priority // 8
            + lawful_claim_weight // 4
            + max(0, -relation_score) // 5,
            0,
            100,
        )
        top_pressure = (
            "service_yoke_claim"
            if "service" in row["claim_type"] or "service-yoke" in row["source"].lower()
            else "lawful_claim"
        )
        causes = [
            f"{row['claimant_name']} has claim {row['claim_id']} at strength {row['strength']}",
            f"Claim source: {row['source']}",
            f"Target province {row['province_name']} has strategic value {row['strategic_value']}",
        ]
        if road_priority:
            causes.append(f"{culture_name} road control priority {road_priority}")
        if lawful_claim_weight:
            causes.append(f"{religion['name'] or row['claimant_religion_id']} lawful claim weight {lawful_claim_weight}")
        if relation_score < 0:
            causes.append(f"Border relation is hostile at {relation_score}")
        if int(row["food_stored"]) > 10_000:
            causes.append("Food stores are stable enough for pressure")

        return HistoricalPressure(
            faction_id=row["active_claimant_faction_id"],
            faction_name=row["claimant_name"],
            seed_faction_id=row["claimant_seed_faction_id"],
            top_pressure=top_pressure,
            intensity=intensity,
            causes=causes,
            claim_id=row["claim_id"],
            claim_type=row["claim_type"],
            claim_source=row["source"],
            recognized_by=row["recognized_by"] or "",
            target_faction_id=row["controller_faction_id"],
            target_faction_name=row["controller_name"] or "",
            target_seed_faction_id=row["controller_seed_faction_id"] or "",
            province_id=row["active_target_province_id"],
            province_name=row["province_name"],
            seed_province_id=row["seed_province_id"],
            old_imperial_name=row["old_imperial_name"] or "",
            relation_id=relation.get("id"),
            relation_score=relation_score,
            war_risk=war_risk,
            culture_id=row["claimant_culture_id"] or "",
            culture_name=culture_name,
            religion_id=row["claimant_religion_id"] or "",
            religion_name=religion["name"],
            religion_war_stance=religion["war_stance"],
            modifiers=modifiers,
        )

    def _controller_pressure(
        self,
        db: DatabaseManager,
        row: dict[str, Any],
        relation: dict[str, Any],
    ) -> HistoricalPressure:
        culture_name = self._culture_name(db, row["controller_culture_id"])
        religion = self._religion(db, row["controller_religion_id"])
        modifiers = self._combined_modifiers(
            db,
            row["controller_culture_id"],
            row["controller_religion_id"],
        )
        relation_score = int(relation.get("opinion") or 0)
        war_risk = int(relation.get("war_risk") or 0)
        oath_morale = self._int_modifier(modifiers, "morale_oath_war_mod")
        homeland_defense = self._int_modifier(modifiers, "homeland_defense_morale_mod")
        intensity = self._clamp(
            int(row["strength"])
            + max(0, -relation_score) // 4
            + war_risk // 6
            + oath_morale // 3
            + homeland_defense // 4,
            0,
            100,
        )
        top_pressure = (
            "service_yoke_resistance"
            if "service" in row["claim_type"] or "service-yoke" in row["source"].lower()
            else "defend_claimed_land"
        )
        causes = [
            f"{row['controller_name']} controls {row['province_name']}",
            f"{row['claimant_name']} claim {row['claim_id']} threatens local rule",
            f"Claim strength {row['strength']} creates recognition pressure",
        ]
        if oath_morale:
            causes.append(f"{religion['name'] or row['controller_religion_id']} oath-war morale {oath_morale}")
        if relation_score < 0:
            causes.append(f"Existing tension is {relation_score}")

        return HistoricalPressure(
            faction_id=row["controller_faction_id"],
            faction_name=row["controller_name"],
            seed_faction_id=row["controller_seed_faction_id"],
            top_pressure=top_pressure,
            intensity=intensity,
            causes=causes,
            claim_id=row["claim_id"],
            claim_type=row["claim_type"],
            claim_source=row["source"],
            recognized_by=row["recognized_by"] or "",
            target_faction_id=row["active_claimant_faction_id"],
            target_faction_name=row["claimant_name"],
            target_seed_faction_id=row["claimant_seed_faction_id"],
            province_id=row["active_target_province_id"],
            province_name=row["province_name"],
            seed_province_id=row["seed_province_id"],
            old_imperial_name=row["old_imperial_name"] or "",
            relation_id=relation.get("id"),
            relation_score=relation_score,
            war_risk=war_risk,
            culture_id=row["controller_culture_id"] or "",
            culture_name=culture_name,
            religion_id=row["controller_religion_id"] or "",
            religion_name=religion["name"],
            religion_war_stance=religion["war_stance"],
            modifiers=modifiers,
        )

    def _relation_between(
        self,
        db: DatabaseManager,
        faction_a_id: int,
        faction_b_id: int | None,
    ) -> dict[str, Any]:
        if faction_b_id is None:
            return {}
        rows = self._fetch_dicts(
            db,
            """
            SELECT id, opinion, trust, status, main_tension, war_risk
            FROM relation
            WHERE (faction_a_id = ? AND faction_b_id = ?)
               OR (faction_a_id = ? AND faction_b_id = ?)
            ORDER BY id
            LIMIT 1
            """,
            (faction_a_id, faction_b_id, faction_b_id, faction_a_id),
        )
        return rows[0] if rows else {}

    def _culture_name(self, db: DatabaseManager, culture_id: str | None) -> str:
        if not culture_id:
            return ""
        row = db.execute(
            "SELECT common_name FROM culture WHERE culture_id = ?",
            (culture_id,),
        ).fetchone()
        return row[0] if row else culture_id

    def _religion(self, db: DatabaseManager, religion_id: str | None) -> dict[str, str]:
        if not religion_id:
            return {"name": "", "war_stance": ""}
        row = db.execute(
            "SELECT name, war_stance FROM religion WHERE religion_id = ?",
            (religion_id,),
        ).fetchone()
        if row is None:
            return {"name": religion_id, "war_stance": ""}
        return {"name": row[0], "war_stance": row[1] or ""}

    def _combined_modifiers(
        self,
        db: DatabaseManager,
        culture_id: str | None,
        religion_id: str | None,
    ) -> dict[str, Any]:
        modifiers: dict[str, Any] = {}
        for table, id_column, row_id in (
            ("culture_modifier", "culture_id", culture_id),
            ("religion_modifier", "religion_id", religion_id),
        ):
            if not row_id:
                continue
            row = db.execute(
                f"SELECT modifiers_json FROM {table} WHERE {id_column} = ?",
                (row_id,),
            ).fetchone()
            if row is not None:
                modifiers.update(json.loads(row[0] or "{}"))
        return modifiers

    @staticmethod
    def _int_modifier(modifiers: dict[str, Any], key: str) -> int:
        value = modifiers.get(key, 0)
        if value in ("", None):
            return 0
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _fetch_dicts(
        db: DatabaseManager,
        query: str,
        params: tuple[Any, ...] = (),
    ) -> list[dict[str, Any]]:
        cursor = db.execute(query, params)
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    @staticmethod
    def _clamp(value: int, minimum: int, maximum: int) -> int:
        return max(minimum, min(maximum, value))

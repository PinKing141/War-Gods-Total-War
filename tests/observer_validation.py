"""Shared validation helpers for observer data and runtime snapshots."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    location: str
    message: str

    def format(self) -> str:
        return f"[{self.code}] {self.location}: {self.message}"


def format_issues(issues: Iterable[ValidationIssue]) -> str:
    return "\n".join(issue.format() for issue in issues)


def collect_static_validation_issues(
    seed: dict,
    province_rows: list[dict[str, str]],
    adjacency_rows: list[dict[str, str]],
    river_rows: list[dict[str, str]],
    local_faction_ids: set[str] | None = None,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    local_faction_ids = local_faction_ids or set()
    factions = {f["id"] for f in seed["factions"]}
    all_map_factions = factions | local_faction_ids
    seed_provinces = {p["id"] for p in seed["provinces"]}
    cultures = set(seed["cultures"])
    religions = set(seed["religions"])
    species = set(seed["species"])
    characters = {c["id"] for c in seed["characters"]}

    def add(code: str, location: str, message: str) -> None:
        issues.append(ValidationIssue(code, location, message))

    if len(factions) != len(seed["factions"]):
        add("duplicate_faction_id", "seed.factions", "Faction IDs must be unique")
    if len(seed_provinces) != len(seed["provinces"]):
        add("duplicate_province_id", "seed.provinces", "Province IDs must be unique")
    if len(characters) != len(seed["characters"]):
        add("duplicate_character_id", "seed.characters", "Character IDs must be unique")

    for faction in seed["factions"]:
        loc = f"faction:{faction['id']}"
        if faction["culture"] not in cultures:
            add("unknown_culture", loc, faction["culture"])
        if faction["religion"] not in religions:
            add("unknown_religion", loc, faction["religion"])
        if faction["species"] not in species:
            add("unknown_species", loc, faction["species"])

    for province in seed["provinces"]:
        loc = f"province:{province['id']}"
        if province["controller"] not in factions:
            add("unknown_controller", loc, province["controller"])
        if province["terrain"] not in seed["terrains"]:
            add("unknown_terrain", loc, province["terrain"])
        for field in ["value", "fort", "roads"]:
            if province[field] < 0:
                add("negative_province_number", f"{loc}.{field}", str(province[field]))

    defined_map_provinces = {row["province_id"] for row in province_rows}
    if not seed_provinces <= defined_map_provinces:
        missing = ", ".join(sorted(seed_provinces - defined_map_provinces))
        add("seed_province_missing_from_map", "province_definitions.csv", missing)
    for row in province_rows:
        loc = f"province_definitions:{row['province_id']}"
        if row["controller"] not in all_map_factions:
            add("unknown_map_controller", loc, row["controller"])
        for field in ["road_level", "port_level", "fort_level", "strategic_value", "pixel_area"]:
            if int(row[field]) < 0:
                add("negative_map_number", f"{loc}.{field}", row[field])

    for row in adjacency_rows:
        loc = f"adjacency:{row['province_a']}->{row['province_b']}"
        if row["province_a"] not in defined_map_provinces:
            add("unknown_adjacency_province", loc, row["province_a"])
        if row["province_b"] not in defined_map_provinces:
            add("unknown_adjacency_province", loc, row["province_b"])
        if row["province_a"] == row["province_b"]:
            add("self_adjacency", loc, "A province cannot be adjacent to itself")

    for claim in seed["claims"]:
        loc = f"claim:{claim['id']}"
        if claim["claimant"] not in factions:
            add("unknown_claimant", loc, claim["claimant"])
        if claim["target"] not in seed_provinces:
            add("unknown_claim_target", loc, claim["target"])
        if claim["strength"] < 0:
            add("negative_claim_strength", loc, str(claim["strength"]))
        recognized_by = claim.get("recognizedBy")
        if isinstance(recognized_by, list):
            bad = set(recognized_by) - religions
            if bad:
                add("unknown_claim_recognizer", loc, ", ".join(sorted(bad)))
        elif recognized_by and recognized_by not in religions:
            add("unknown_claim_recognizer", loc, recognized_by)

    for mage in seed["mages"]:
        loc = f"mage:{mage['id']}"
        if mage["character"] not in characters:
            add("unknown_mage_character", loc, mage["character"])
        if mage["patron"] not in factions:
            add("unknown_mage_patron", loc, mage["patron"])
        if mage["species"] not in species:
            add("unknown_mage_species", loc, mage["species"])
        for field in ["capacity", "control", "strain", "risk"]:
            if mage[field] < 0:
                add("negative_mage_number", f"{loc}.{field}", str(mage[field]))

    for row in river_rows:
        loc = f"province_river_features:{row['province_id']}"
        if row["province_id"] not in defined_map_provinces:
            add("unknown_river_feature_province", loc, row["province_id"])
        for field in ["river_trade_value", "river_defense_bonus", "river_movement_penalty", "supply_bonus", "farmland_bonus"]:
            if int(row[field]) < 0:
                add("negative_river_feature_number", f"{loc}.{field}", row[field])

    return issues


def collect_runtime_validation_issues(snapshot: dict, seed: dict) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    factions = {f["id"] for f in seed["factions"]}
    provinces = {p["id"] for p in seed["provinces"]}
    cultures = set(seed["cultures"])
    species = set(seed["species"])
    characters = {c["id"] for c in snapshot["characters"]}

    def add(code: str, location: str, message: str) -> None:
        issues.append(ValidationIssue(code, location, message))

    for army in snapshot["armies"]:
        loc = f"army:{army['id']}"
        if army["faction"] not in factions:
            add("unknown_army_faction", loc, army["faction"])
        if army["loc"] not in provinces:
            add("unknown_army_location", loc, army["loc"])
        if army["commanderId"] not in characters:
            add("unknown_army_commander", loc, army["commanderId"])
        for field in ["size", "supply", "maxSupply", "dailySupplyUse"]:
            if army.get(field, 0) < 0:
                add("negative_army_number", f"{loc}.{field}", str(army.get(field)))

    for war in snapshot["wars"]:
        loc = f"war:{war['id']}"
        if war["attacker"] not in factions:
            add("unknown_war_attacker", loc, war["attacker"])
        if war["defender"] not in factions:
            add("unknown_war_defender", loc, war["defender"])
        if war["goal"].get("province") not in provinces:
            add("unknown_war_goal", loc, str(war["goal"]))
        for side_name in ["atkSide", "defSide"]:
            bad = set(war.get(side_name, [])) - factions
            if bad:
                add("unknown_war_side", f"{loc}.{side_name}", ", ".join(sorted(bad)))

    for character in snapshot["characters"]:
        loc = f"character:{character['id']}"
        if character["faction"] not in factions:
            add("unknown_character_faction", loc, character["faction"])
        if character["culture"] not in cultures:
            add("unknown_character_culture", loc, character["culture"])
        if character["species"] not in species:
            add("unknown_character_species", loc, character["species"])

    for province_id, state in snapshot["provinceState"].items():
        loc = f"province_state:{province_id}"
        if province_id not in provinces:
            add("unknown_runtime_province", loc, province_id)
        if state["controller"] not in factions:
            add("unknown_runtime_controller", loc, state["controller"])
        for field in ["pop", "garrison", "devastation"]:
            if state.get(field, 0) < 0:
                add("negative_province_state_number", f"{loc}.{field}", str(state.get(field)))

    for faction_id, state in snapshot["factionState"].items():
        loc = f"faction_state:{faction_id}"
        if faction_id not in factions:
            add("unknown_runtime_faction", loc, faction_id)
        for field in ["treasury", "manpower", "maxManpower", "prestige", "exhaustion"]:
            if state.get(field, 0) < 0:
                add("negative_faction_state_number", f"{loc}.{field}", str(state.get(field)))

    return issues

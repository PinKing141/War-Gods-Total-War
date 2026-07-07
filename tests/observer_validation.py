"""Shared validation helpers for observer data and runtime snapshots."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
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


def _ids_by_row(items: list[dict], id_field: str, source: str) -> tuple[set[str], list[ValidationIssue]]:
    seen: dict[str, int] = {}
    issues: list[ValidationIssue] = []
    for idx, item in enumerate(items, start=2):
        value = item.get(id_field)
        loc = f"{source}:row {idx}.{id_field}"
        if not value:
            issues.append(ValidationIssue("missing_id", loc, "ID is required"))
            continue
        if value in seen:
            issues.append(ValidationIssue(
                "duplicate_id",
                loc,
                f"{value} duplicates row {seen[value]}",
            ))
        else:
            seen[value] = idx
    return set(seen), issues


def collect_static_validation_issues(
    seed: dict,
    province_rows: list[dict[str, str]],
    adjacency_rows: list[dict[str, str]],
    river_rows: list[dict[str, str]],
    local_faction_ids: set[str] | None = None,
    scenario_docs: list[tuple[str, dict]] | None = None,
    root: str | Path | None = None,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    local_faction_ids = local_faction_ids or set()
    scenario_docs = scenario_docs or []
    root_path = Path(root) if root is not None else None
    factions, id_issues = _ids_by_row(seed["factions"], "id", "docs/assets/data.js:seed.factions")
    issues.extend(id_issues)
    all_map_factions = factions | local_faction_ids
    seed_provinces, id_issues = _ids_by_row(seed["provinces"], "id", "docs/assets/data.js:seed.provinces")
    issues.extend(id_issues)
    characters, id_issues = _ids_by_row(seed["characters"], "id", "docs/assets/data.js:seed.characters")
    issues.extend(id_issues)
    claim_ids, id_issues = _ids_by_row(seed.get("claims", []), "id", "docs/assets/data.js:seed.claims")
    issues.extend(id_issues)
    mage_ids, id_issues = _ids_by_row(seed.get("mages", []), "id", "docs/assets/data.js:seed.mages")
    issues.extend(id_issues)
    cultures = set(seed["cultures"])
    religions = set(seed["religions"])
    species = set(seed["species"])
    valid_tiers = {"tier_1", "tier_2", "tier_3", "tier_4"}

    def add(code: str, location: str, message: str) -> None:
        issues.append(ValidationIssue(code, location, message))

    if len(cultures) != len(seed["cultures"]):
        add("duplicate_culture_id", "docs/assets/data.js:seed.cultures", "Culture IDs must be unique")
    if len(religions) != len(seed["religions"]):
        add("duplicate_religion_id", "docs/assets/data.js:seed.religions", "Religion IDs must be unique")
    if len(species) != len(seed["species"]):
        add("duplicate_species_id", "docs/assets/data.js:seed.species", "Species IDs must be unique")

    for idx, faction in enumerate(seed["factions"], start=2):
        loc = f"docs/assets/data.js:seed.factions[row {idx}, id={faction.get('id')}]"
        if faction["culture"] not in cultures:
            add("unknown_culture", f"{loc}.culture", faction["culture"])
        if faction["religion"] not in religions:
            add("unknown_religion", f"{loc}.religion", faction["religion"])
        if faction["species"] not in species:
            add("unknown_species", f"{loc}.species", faction["species"])
        if faction.get("tier") not in valid_tiers:
            add("invalid_faction_tier", f"{loc}.tier", str(faction.get("tier")))
        if faction.get("tierWeight", 0) <= 0:
            add("invalid_faction_tier_weight", f"{loc}.tierWeight", str(faction.get("tierWeight")))

    for idx, province in enumerate(seed["provinces"], start=2):
        loc = f"docs/assets/data.js:seed.provinces[row {idx}, id={province.get('id')}]"
        if province["controller"] not in factions:
            add("unknown_controller", f"{loc}.controller", province["controller"])
        if province["terrain"] not in seed["terrains"]:
            add("unknown_terrain", f"{loc}.terrain", province["terrain"])
        for field in ["value", "fort", "roads"]:
            if province[field] < 0:
                add("negative_province_number", f"{loc}.{field}", str(province[field]))

    defined_map_provinces, id_issues = _ids_by_row(province_rows, "province_id", "docs/assets/provinces/world_province_definitions.csv")
    issues.extend(id_issues)
    if not seed_provinces <= defined_map_provinces:
        missing = ", ".join(sorted(seed_provinces - defined_map_provinces))
        add("seed_province_missing_from_map", "docs/assets/provinces/world_province_definitions.csv", missing)
    rgb_seen: dict[tuple[str, str, str], int] = {}
    for idx, row in enumerate(province_rows, start=2):
        loc = f"docs/assets/provinces/world_province_definitions.csv:row {idx}, province_id={row.get('province_id')}"
        rgb = (row.get("red", ""), row.get("green", ""), row.get("blue", ""))
        if rgb in rgb_seen:
            add("duplicate_province_rgb", loc, f"{rgb} duplicates row {rgb_seen[rgb]}")
        else:
            rgb_seen[rgb] = idx
        if row["controller"] not in all_map_factions:
            add("unknown_map_controller", f"{loc}.controller", row["controller"])
        for field in ["road_level", "port_level", "fort_level", "strategic_value", "pixel_area"]:
            if int(row[field]) < 0:
                add("negative_map_number", f"{loc}.{field}", row[field])

    adjacency_pairs = set()
    for idx, row in enumerate(adjacency_rows, start=2):
        loc = f"docs/assets/provinces/world_province_adjacency.csv:row {idx} {row.get('province_a')}->{row.get('province_b')}"
        pair = (row["province_a"], row["province_b"])
        if pair in adjacency_pairs:
            add("duplicate_adjacency", loc, "Adjacency row is duplicated")
        adjacency_pairs.add(pair)
        if row["province_a"] not in defined_map_provinces:
            add("unknown_adjacency_province", f"{loc}.province_a", row["province_a"])
        if row["province_b"] not in defined_map_provinces:
            add("unknown_adjacency_province", f"{loc}.province_b", row["province_b"])
        if row["province_a"] == row["province_b"]:
            add("self_adjacency", loc, "A province cannot be adjacent to itself")

    for idx, claim in enumerate(seed["claims"], start=2):
        loc = f"docs/assets/data.js:seed.claims[row {idx}, id={claim.get('id')}]"
        if claim["claimant"] not in factions:
            add("unknown_claimant", f"{loc}.claimant", claim["claimant"])
        if claim["target"] not in seed_provinces:
            add("unknown_claim_target", f"{loc}.target", claim["target"])
        if claim["strength"] < 0:
            add("negative_claim_strength", f"{loc}.strength", str(claim["strength"]))
        recognized_by = claim.get("recognizedBy")
        if isinstance(recognized_by, list):
            bad = set(recognized_by) - religions
            if bad:
                add("unknown_claim_recognizer", f"{loc}.recognizedBy", ", ".join(sorted(bad)))
        elif recognized_by and recognized_by not in religions:
            add("unknown_claim_recognizer", f"{loc}.recognizedBy", recognized_by)

    for idx, mage in enumerate(seed["mages"], start=2):
        loc = f"docs/assets/data.js:seed.mages[row {idx}, id={mage.get('id')}]"
        if mage["character"] not in characters:
            add("unknown_mage_character", f"{loc}.character", mage["character"])
        if mage["patron"] not in factions:
            add("unknown_mage_patron", f"{loc}.patron", mage["patron"])
        if mage["species"] not in species:
            add("unknown_mage_species", f"{loc}.species", mage["species"])
        for field in ["capacity", "control", "strain", "risk"]:
            if mage[field] < 0:
                add("negative_mage_number", f"{loc}.{field}", str(mage[field]))

    river_provinces, id_issues = _ids_by_row(river_rows, "province_id", "docs/assets/rivers/province_river_features.csv")
    issues.extend(id_issues)
    for idx, row in enumerate(river_rows, start=2):
        loc = f"docs/assets/rivers/province_river_features.csv:row {idx}, province_id={row.get('province_id')}"
        if row["province_id"] not in defined_map_provinces:
            add("unknown_river_feature_province", f"{loc}.province_id", row["province_id"])
        for field in ["river_trade_value", "river_defense_bonus", "river_movement_penalty", "supply_bonus", "farmland_bonus"]:
            if int(row[field]) < 0:
                add("negative_river_feature_number", f"{loc}.{field}", row[field])

    scenario_ids: dict[str, str] = {}
    for source, scenario in scenario_docs:
        scenario_id = scenario.get("scenario_id")
        loc = f"{source}:scenario_id"
        if not scenario_id:
            add("missing_scenario_id", loc, "scenario_id is required")
        elif scenario_id in scenario_ids:
            add("duplicate_scenario_id", loc, f"{scenario_id} duplicates {scenario_ids[scenario_id]}")
        else:
            scenario_ids[scenario_id] = source
        if scenario.get("start_year", 0) < 0:
            add("negative_scenario_start_year", f"{source}:start_year", str(scenario.get("start_year")))
        for key, rel_path in (scenario.get("data_sources") or {}).items():
            if root_path is not None and not (root_path / rel_path).exists():
                add("missing_scenario_data_source", f"{source}:data_sources.{key}", rel_path)
        for fid in scenario.get("active_factions", []):
            if fid not in factions:
                add("unknown_scenario_faction", f"{source}:active_factions", fid)
        for pid in scenario.get("focus_provinces", []):
            if pid not in seed_provinces:
                add("unknown_scenario_province", f"{source}:focus_provinces", pid)
        for idx, war in enumerate(scenario.get("starting_wars", []), start=1):
            war_loc = f"{source}:starting_wars[{idx}]"
            if war.get("attacker") not in factions:
                add("unknown_scenario_war_attacker", f"{war_loc}.attacker", str(war.get("attacker")))
            if war.get("defender") not in factions:
                add("unknown_scenario_war_defender", f"{war_loc}.defender", str(war.get("defender")))
            if war.get("goal_province") not in seed_provinces:
                add("unknown_scenario_war_goal", f"{war_loc}.goal_province", str(war.get("goal_province")))

    return issues


def collect_runtime_validation_issues(snapshot: dict, seed: dict) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    factions = {f["id"] for f in seed["factions"]}
    provinces = {p["id"] for p in seed["provinces"]}
    cultures = set(seed["cultures"])
    species = set(seed["species"])
    characters, id_issues = _ids_by_row(snapshot["characters"], "id", "runtime.characters")
    issues.extend(id_issues)
    army_ids, id_issues = _ids_by_row(snapshot["armies"], "id", "runtime.armies")
    issues.extend(id_issues)
    war_ids, id_issues = _ids_by_row(snapshot["wars"], "id", "runtime.wars")
    issues.extend(id_issues)

    def add(code: str, location: str, message: str) -> None:
        issues.append(ValidationIssue(code, location, message))

    for idx, army in enumerate(snapshot["armies"], start=2):
        loc = f"runtime.armies[row {idx}, id={army.get('id')}]"
        if army["faction"] not in factions:
            add("unknown_army_faction", f"{loc}.faction", army["faction"])
        if army["loc"] not in provinces:
            add("unknown_army_location", f"{loc}.loc", army["loc"])
        if army.get("nextLoc") and army["nextLoc"] not in provinces:
            add("unknown_army_next_location", f"{loc}.nextLoc", army["nextLoc"])
        if army.get("dest") and army["dest"] not in provinces:
            add("unknown_army_destination", f"{loc}.dest", army["dest"])
        if army["commanderId"] not in characters:
            add("unknown_army_commander", f"{loc}.commanderId", army["commanderId"])
        if army.get("warId") and army["warId"] not in war_ids:
            add("unknown_army_war", f"{loc}.warId", army["warId"])
        for field in ["size", "supply", "maxSupply", "dailySupplyUse", "morale"]:
            if army.get(field, 0) < 0:
                add("negative_army_number", f"{loc}.{field}", str(army.get(field)))
        if army.get("supply", 0) > army.get("maxSupply", 0) + 0.1:
            add("army_supply_over_cap", f"{loc}.supply", f"{army.get('supply')} > {army.get('maxSupply')}")

    for idx, war in enumerate(snapshot["wars"], start=2):
        loc = f"runtime.wars[row {idx}, id={war.get('id')}]"
        if war["attacker"] not in factions:
            add("unknown_war_attacker", f"{loc}.attacker", war["attacker"])
        if war["defender"] not in factions:
            add("unknown_war_defender", f"{loc}.defender", war["defender"])
        if war["goal"].get("province") not in provinces:
            add("unknown_war_goal", f"{loc}.goal.province", str(war["goal"]))
        for side_name in ["atkSide", "defSide"]:
            bad = set(war.get(side_name, [])) - factions
            if bad:
                add("unknown_war_side", f"{loc}.{side_name}", ", ".join(sorted(bad)))
        if not isinstance(war.get("score", 0), (int, float)):
            add("invalid_war_score", f"{loc}.score", str(war.get("score")))

    for idx, character in enumerate(snapshot["characters"], start=2):
        loc = f"runtime.characters[row {idx}, id={character.get('id')}]"
        if character["faction"] not in factions:
            add("unknown_character_faction", f"{loc}.faction", character["faction"])
        if character["culture"] not in cultures:
            add("unknown_character_culture", f"{loc}.culture", character["culture"])
        if character["species"] not in species:
            add("unknown_character_species", f"{loc}.species", character["species"])
        if character.get("age", 0) < 0:
            add("negative_character_age", f"{loc}.age", str(character.get("age")))

    for province_id, state in snapshot["provinceState"].items():
        loc = f"province_state:{province_id}"
        if province_id not in provinces:
            add("unknown_runtime_province", loc, province_id)
        if state["controller"] not in factions:
            add("unknown_runtime_controller", f"{loc}.controller", state["controller"])
        if state.get("occupier") and state["occupier"] not in factions:
            add("unknown_runtime_occupier", f"{loc}.occupier", state["occupier"])
        if state.get("siege") and state["siege"].get("by") not in factions:
            add("unknown_runtime_sieger", f"{loc}.siege.by", state["siege"].get("by"))
        revolt_ids = {revolt.get("id") for revolt in snapshot.get("revolts", [])}
        if state.get("revoltId") and state["revoltId"] not in revolt_ids:
            add("unknown_province_revolt", f"{loc}.revoltId", state["revoltId"])
        for field in ["pop", "garrison", "devastation", "instability", "recentConquest"]:
            if state.get(field, 0) < 0:
                add("negative_province_state_number", f"{loc}.{field}", str(state.get(field)))

    for faction_id, state in snapshot["factionState"].items():
        loc = f"faction_state:{faction_id}"
        if faction_id not in factions:
            add("unknown_runtime_faction", loc, faction_id)
        if state.get("rulerId") and state["rulerId"] not in characters:
            add("unknown_runtime_ruler", f"{loc}.rulerId", state["rulerId"])
        for field in ["treasury", "manpower", "maxManpower", "prestige", "exhaustion"]:
            if state.get(field, 0) < 0:
                add("negative_faction_state_number", f"{loc}.{field}", str(state.get(field)))
        internal = state.get("internal")
        if not internal:
            add("missing_internal_politics", f"{loc}.internal", "Faction has no internal politics state.")
        else:
            for field in [
                "courtTension", "successionTension", "armyInfluence", "taxBurden", "faithTension",
                "cultureTension", "regionalAutonomy", "nobleLoyalty", "merchantLoyalty",
                "revoltRisk", "successionPressure",
            ]:
                value = internal.get(field)
                if not isinstance(value, (int, float)):
                    add("invalid_internal_politics_number", f"{loc}.internal.{field}", str(value))
                elif value < 0 or value > 100:
                    add("internal_politics_out_of_range", f"{loc}.internal.{field}", str(value))

    for revolt in snapshot.get("revolts", []):
        loc = f"runtime.revolts[id={revolt.get('id')}]"
        if revolt.get("province") not in provinces:
            add("unknown_revolt_province", f"{loc}.province", str(revolt.get("province")))
        if revolt.get("against") not in factions:
            add("unknown_revolt_target", f"{loc}.against", str(revolt.get("against")))
        if revolt.get("status") not in {"active", "won", "suppressed", "invalid"}:
            add("invalid_revolt_status", f"{loc}.status", str(revolt.get("status")))
        if revolt.get("strength", 0) < 0:
            add("negative_revolt_strength", f"{loc}.strength", str(revolt.get("strength")))
        progress = revolt.get("progress")
        if not isinstance(progress, (int, float)) or progress < 0 or progress > 1:
            add("invalid_revolt_progress", f"{loc}.progress", str(progress))

    return issues

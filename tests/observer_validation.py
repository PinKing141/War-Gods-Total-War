"""Shared validation helpers for observer data and runtime snapshots."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


VALID_AMBITIONS = {
    "become ruler",
    "protect dynasty",
    "win glory",
    "secure wealth",
    "defend faith",
    "restore old claims",
    "keep peace",
    "master the court",
}

VALID_FEARS = {
    "dying forgotten",
    "losing legitimacy",
    "court betrayal",
    "dynasty failure",
    "poverty",
    "magical scandal",
    "foreign conquest",
    "open revolt",
}

VALID_RELATIONSHIP_TYPES = {
    "parent",
    "child",
    "sibling",
    "spouse",
    "lover",
    "friend",
    "rival",
    "enemy",
    "mentor",
    "student",
    "commander",
    "vassal",
    "patron",
    "hostage",
    "betrayer",
    "rescuer",
}

RECIPROCAL_RELATIONSHIP = {
    "parent": "child",
    "child": "parent",
    "sibling": "sibling",
    "spouse": "spouse",
    "lover": "lover",
    "friend": "friend",
    "rival": "rival",
    "enemy": "enemy",
    "mentor": "student",
    "student": "mentor",
    "commander": "vassal",
    "vassal": "commander",
    "patron": "vassal",
    "hostage": "hostage",
    "betrayer": "enemy",
    "rescuer": "friend",
}

COURT_OFFICES = {
    "ruler",
    "heir",
    "chancellor",
    "marshal",
    "steward",
    "spymaster",
    "court_mage",
    "high_priest",
    "captain_of_guard",
    "governor",
    "regent",
}

SOCIAL_GROUPS = {
    "nobles",
    "clergy",
    "merchants",
    "peasants",
    "craftsmen",
    "soldiers",
    "mages",
    "scholars",
    "minorities",
    "tribes",
    "foreign_settlers",
    "refugees",
    "urban_poor",
}

VALID_MEMORY_TYPES = {
    "family death",
    "battle victory",
    "battle defeat",
    "promotion",
    "betrayal",
    "humiliation",
    "wound",
    "lost province",
    "saved life",
    "first command",
    "exile",
}


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
    religions = set(seed["religions"])
    species = set(seed["species"])
    characters, id_issues = _ids_by_row(snapshot["characters"], "id", "runtime.characters")
    issues.extend(id_issues)
    army_ids, id_issues = _ids_by_row(snapshot["armies"], "id", "runtime.armies")
    issues.extend(id_issues)
    war_ids, id_issues = _ids_by_row(snapshot["wars"], "id", "runtime.wars")
    issues.extend(id_issues)
    characters_by_id = {character.get("id"): character for character in snapshot["characters"]}
    dynasty_ids, id_issues = _ids_by_row(snapshot.get("dynasties", []), "id", "runtime.dynasties")
    issues.extend(id_issues)
    house_ids, id_issues = _ids_by_row(snapshot.get("houses", []), "id", "runtime.houses")
    issues.extend(id_issues)

    def add(code: str, location: str, message: str) -> None:
        issues.append(ValidationIssue(code, location, message))

    def parent_ids(character: dict) -> list[str]:
        family = character.get("family") or {}
        return [pid for pid in [character.get("parentId"), family.get("father"), family.get("mother")] if pid]

    def has_parent_loop(character_id: str, path: set[str] | None = None) -> bool:
        path = set(path or set())
        if character_id in path:
            return True
        character = characters_by_id.get(character_id)
        if not character:
            return False
        path.add(character_id)
        return any(has_parent_loop(parent_id, path) for parent_id in parent_ids(character))

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
        if character.get("faith") and character["faith"] not in religions:
            add("unknown_character_faith", f"{loc}.faith", character["faith"])
        if not isinstance(character.get("birthYear"), (int, float)):
            add("missing_character_birth_year", f"{loc}.birthYear", str(character.get("birthYear")))
        death_year = character.get("deathYear")
        if death_year is not None and not isinstance(death_year, (int, float)):
            add("invalid_character_death_year", f"{loc}.deathYear", str(death_year))
        for field in ["stress", "health", "wealth", "legitimacy", "reputation"]:
            value = character.get(field)
            if not isinstance(value, (int, float)):
                add("invalid_character_state_number", f"{loc}.{field}", str(value))
            elif value < 0:
                add("negative_character_state_number", f"{loc}.{field}", str(value))
        for field in ["stress", "health", "legitimacy", "reputation"]:
            value = character.get(field)
            if isinstance(value, (int, float)) and value > 100:
                add("character_state_out_of_range", f"{loc}.{field}", str(value))
        if not character.get("ambition"):
            add("missing_character_ambition", f"{loc}.ambition", "Character needs an ambition.")
        elif character["ambition"] not in VALID_AMBITIONS:
            add("invalid_character_ambition", f"{loc}.ambition", str(character["ambition"]))
        if not character.get("fear"):
            add("missing_character_fear", f"{loc}.fear", "Character needs a fear.")
        elif character["fear"] not in VALID_FEARS:
            add("invalid_character_fear", f"{loc}.fear", str(character["fear"]))
        if not character.get("loyalties") or not character["loyalties"].get("faction"):
            add("missing_character_loyalties", f"{loc}.loyalties", "Character needs loyalties.")
        memories = character.get("memories")
        if not isinstance(memories, list):
            add("invalid_character_memories", f"{loc}.memories", "Character memories must be an array.")
            memories = []
        for memory in memories:
            mem_loc = f"{loc}.memory:{memory.get('id')}"
            if not memory.get("id"):
                add("missing_memory_id", mem_loc, "Memory needs an ID.")
            if memory.get("type") not in VALID_MEMORY_TYPES:
                add("invalid_memory_type", f"{mem_loc}.type", str(memory.get("type")))
            if not memory.get("text"):
                add("missing_memory_text", f"{mem_loc}.text", "Memory needs readable text.")
            if not isinstance(memory.get("day"), (int, float)) or memory.get("day") < 0:
                add("invalid_memory_day", f"{mem_loc}.day", str(memory.get("day")))
            refs = memory.get("refs") or {}
            if refs.get("character") and refs["character"] not in characters:
                add("unknown_memory_character", f"{mem_loc}.refs.character", refs["character"])
            if refs.get("faction") and refs["faction"] not in factions:
                add("unknown_memory_faction", f"{mem_loc}.refs.faction", refs["faction"])
            if refs.get("province") and refs["province"] not in provinces:
                add("unknown_memory_province", f"{mem_loc}.refs.province", refs["province"])
            if refs.get("war") and refs["war"] not in war_ids:
                add("unknown_memory_war", f"{mem_loc}.refs.war", refs["war"])
        record = character.get("militaryRecord")
        if not record:
            add("missing_military_record", f"{loc}.militaryRecord", "Character needs a military record.")
        else:
            for field in ["battlesFought", "battlesWon", "battlesLost", "siegesLed", "wounds"]:
                value = record.get(field)
                if not isinstance(value, (int, float)):
                    add("invalid_military_record_number", f"{loc}.militaryRecord.{field}", str(value))
                elif value < 0:
                    add("negative_military_record_number", f"{loc}.militaryRecord.{field}", str(value))
            if record.get("battlesWon", 0) + record.get("battlesLost", 0) > record.get("battlesFought", 0):
                add("invalid_military_record_totals", f"{loc}.militaryRecord", "Wins and losses cannot exceed battles fought.")
            for field in ["notableVictories", "notableDefeats"]:
                if not isinstance(record.get(field), list):
                    add("invalid_military_record_list", f"{loc}.militaryRecord.{field}", "Notable records must be arrays.")
        family = character.get("family")
        if not family:
            add("missing_family_state", f"{loc}.family", "Character needs family state.")
        else:
            for field in ["father", "mother"]:
                value = family.get(field)
                if value and value not in characters:
                    add("unknown_family_parent", f"{loc}.family.{field}", value)
                if value == character.get("id"):
                    add("self_family_parent", f"{loc}.family.{field}", "Character cannot be their own parent.")
            for field in ["spouses", "lovers", "children", "siblings"]:
                values = family.get(field)
                if not isinstance(values, list):
                    add("invalid_family_list", f"{loc}.family.{field}", "Family links must be arrays.")
                    values = []
                for value in values:
                    if value not in characters:
                        add("unknown_family_link", f"{loc}.family.{field}", value)
                    if value == character.get("id"):
                        add("self_family_link", f"{loc}.family.{field}", "Character cannot link to themselves.")
            if not family.get("dynasty"):
                add("missing_family_dynasty", f"{loc}.family.dynasty", "Dynasty is required.")
            if not family.get("house"):
                add("missing_family_house", f"{loc}.family.house", "House is required.")
            if family.get("dynastyId") and family["dynastyId"] not in dynasty_ids:
                add("unknown_character_dynasty", f"{loc}.family.dynastyId", family["dynastyId"])
            if family.get("houseId") and family["houseId"] not in house_ids:
                add("unknown_character_house", f"{loc}.family.houseId", family["houseId"])
            branch_type = family.get("branchType", "main")
            if branch_type not in {"main", "cadet"}:
                add("invalid_family_branch_type", f"{loc}.family.branchType", str(branch_type))
            if family.get("branchFounder") and family["branchFounder"] not in characters:
                add("unknown_family_branch_founder", f"{loc}.family.branchFounder", family["branchFounder"])
            if family.get("parentHouseId") and family["parentHouseId"] not in house_ids:
                add("unknown_family_parent_house", f"{loc}.family.parentHouseId", family["parentHouseId"])
            if not isinstance(family.get("bastard", False), bool):
                add("invalid_family_bastard", f"{loc}.family.bastard", str(family.get("bastard")))
            if not isinstance(family.get("legitimised", False), bool):
                add("invalid_family_legitimised", f"{loc}.family.legitimised", str(family.get("legitimised")))
            if family.get("legitimised") is True and family.get("bastard") is not True:
                add("legitimised_without_bastard", f"{loc}.family.legitimised", "Only bastards can be marked legitimised.")
            legitimacy = family.get("legitimacy")
            if not isinstance(legitimacy, (int, float)) or legitimacy < 0 or legitimacy > 100:
                add("invalid_family_legitimacy", f"{loc}.family.legitimacy", str(legitimacy))
            rank = family.get("inheritanceRank")
            if rank is not None and (not isinstance(rank, (int, float)) or rank < 1):
                add("invalid_inheritance_rank", f"{loc}.family.inheritanceRank", str(rank))
            claim_strength = family.get("claimStrength")
            if not isinstance(claim_strength, (int, float)) or claim_strength < 0 or claim_strength > 100:
                add("invalid_family_claim_strength", f"{loc}.family.claimStrength", str(claim_strength))
            if has_parent_loop(character.get("id")):
                add("family_parent_loop", f"{loc}.family", "Family parent links contain a loop.")

    for dynasty in snapshot.get("dynasties", []):
        loc = f"runtime.dynasties[id={dynasty.get('id')}]"
        if not dynasty.get("name"):
            add("missing_dynasty_name", f"{loc}.name", "Dynasty needs a name.")
        if dynasty.get("founder") not in characters:
            add("unknown_dynasty_founder", f"{loc}.founder", str(dynasty.get("founder")))
        if dynasty.get("head") and dynasty["head"] not in characters:
            add("unknown_dynasty_head", f"{loc}.head", str(dynasty.get("head")))
        if dynasty.get("homeProvince") and dynasty["homeProvince"] not in provinces:
            add("unknown_dynasty_home_province", f"{loc}.homeProvince", dynasty["homeProvince"])
        for member in dynasty.get("members", []):
            if member not in characters:
                add("unknown_dynasty_member", f"{loc}.members", str(member))
        for house_id in dynasty.get("houses", []):
            if house_id not in house_ids:
                add("unknown_dynasty_house", f"{loc}.houses", str(house_id))
        for branch in dynasty.get("cadetBranches", []):
            if branch.get("house") not in house_ids:
                add("unknown_dynasty_cadet_house", f"{loc}.cadetBranches.house", str(branch.get("house")))
            if branch.get("founder") and branch["founder"] not in characters:
                add("unknown_dynasty_cadet_founder", f"{loc}.cadetBranches.founder", str(branch["founder"]))
            if branch.get("parentHouseId") and branch["parentHouseId"] not in house_ids:
                add("unknown_dynasty_cadet_parent_house", f"{loc}.cadetBranches.parentHouseId", str(branch["parentHouseId"]))
        for rival in dynasty.get("rivals", []):
            if rival not in dynasty_ids:
                add("unknown_dynasty_rival", f"{loc}.rivals", str(rival))
        for alliance in dynasty.get("alliances", []):
            if alliance not in dynasty_ids:
                add("unknown_dynasty_alliance", f"{loc}.alliances", str(alliance))
        if dynasty.get("prestige", 0) < 0 or dynasty.get("renown", 0) < 0:
            add("negative_dynasty_number", loc, "Dynasty prestige and renown must be non-negative.")

    for house in snapshot.get("houses", []):
        loc = f"runtime.houses[id={house.get('id')}]"
        if not house.get("name"):
            add("missing_house_name", f"{loc}.name", "House needs a name.")
        if house.get("dynasty") not in dynasty_ids:
            add("unknown_house_dynasty", f"{loc}.dynasty", str(house.get("dynasty")))
        if house.get("founder") not in characters:
            add("unknown_house_founder", f"{loc}.founder", str(house.get("founder")))
        if house.get("head") not in characters:
            add("unknown_house_head", f"{loc}.head", str(house.get("head")))
        if house.get("homeProvince") and house["homeProvince"] not in provinces:
            add("unknown_house_home_province", f"{loc}.homeProvince", house["homeProvince"])
        branch_type = house.get("branchType", "main")
        if branch_type not in {"main", "cadet"}:
            add("invalid_house_branch_type", f"{loc}.branchType", str(branch_type))
        if house.get("branchFounder") and house["branchFounder"] not in characters:
            add("unknown_house_branch_founder", f"{loc}.branchFounder", str(house["branchFounder"]))
        if house.get("parentHouseId") and house["parentHouseId"] not in house_ids:
            add("unknown_house_parent_house", f"{loc}.parentHouseId", str(house["parentHouseId"]))
        for member in house.get("members", []):
            if member not in characters:
                add("unknown_house_member", f"{loc}.members", str(member))
        if house.get("head") and isinstance(house.get("members"), list) and house["head"] not in house["members"]:
            add("house_head_not_member", f"{loc}.head", "House head must be a member.")
        legitimacy = house.get("legitimacy")
        if not isinstance(legitimacy, (int, float)) or legitimacy < 0 or legitimacy > 100:
            add("invalid_house_legitimacy", f"{loc}.legitimacy", str(legitimacy))
        if house.get("prestige", 0) < 0:
            add("negative_house_prestige", f"{loc}.prestige", str(house.get("prestige")))

    relationship_ids, id_issues = _ids_by_row(snapshot.get("relationships", []), "id", "runtime.relationships")
    issues.extend(id_issues)
    del relationship_ids
    relationships = snapshot.get("relationships", [])
    for idx, relationship in enumerate(relationships, start=2):
        loc = f"runtime.relationships[row {idx}, id={relationship.get('id')}]"
        from_id = relationship.get("from")
        to_id = relationship.get("to")
        rel_type = relationship.get("type")
        if from_id not in characters:
            add("unknown_relationship_from", f"{loc}.from", str(from_id))
        if to_id not in characters:
            add("unknown_relationship_to", f"{loc}.to", str(to_id))
        if from_id == to_id:
            add("self_relationship", loc, "Character cannot have a relationship to themselves.")
        if rel_type not in VALID_RELATIONSHIP_TYPES:
            add("invalid_relationship_type", f"{loc}.type", str(rel_type))
        strength = relationship.get("strength")
        if not isinstance(strength, (int, float)) or strength < 1 or strength > 100:
            add("invalid_relationship_strength", f"{loc}.strength", str(strength))
        reciprocal = RECIPROCAL_RELATIONSHIP.get(rel_type)
        if reciprocal and from_id in characters and to_id in characters:
            has_back = any(
                back.get("from") == to_id and back.get("to") == from_id and back.get("type") == reciprocal
                for back in relationships
            )
            if not has_back:
                add("missing_reciprocal_relationship", loc, f"{rel_type} needs {reciprocal} back.")

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
        society = state.get("society")
        if not society:
            add("missing_province_society", f"{loc}.society", "Province has no social group state.")
        else:
            for group in SOCIAL_GROUPS:
                if group not in society:
                    add("missing_social_group", f"{loc}.society.{group}", "Required social group is missing.")
            for group, social in society.items():
                group_loc = f"{loc}.society.{group}"
                if group not in SOCIAL_GROUPS:
                    add("invalid_social_group", group_loc, group)
                for field in ["size", "loyalty", "unrest", "wealth", "influence"]:
                    value = social.get(field) if isinstance(social, dict) else None
                    if not isinstance(value, (int, float)):
                        add("invalid_social_group_number", f"{group_loc}.{field}", str(value))
                    elif value < 0 or (field != "size" and value > 100):
                        add("social_group_out_of_range", f"{group_loc}.{field}", str(value))
                needs = social.get("needs") if isinstance(social, dict) else None
                if not isinstance(needs, str) or not needs.strip():
                    add("missing_social_group_needs", f"{group_loc}.needs", "Social group needs must be readable.")

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
        succession = state.get("succession")
        if not succession:
            add("missing_succession_state", f"{loc}.succession", "Faction has no succession state.")
        else:
            if not succession.get("law"):
                add("missing_succession_law", f"{loc}.succession.law", "Succession law is required.")
            legitimacy = succession.get("heirLegitimacy")
            if not isinstance(legitimacy, (int, float)) or legitimacy < 0 or legitimacy > 100:
                add("invalid_heir_legitimacy", f"{loc}.succession.heirLegitimacy", str(legitimacy))
            for pretender in succession.get("pretenders", []):
                if pretender.get("character") not in characters:
                    add("unknown_pretender_character", f"{loc}.succession.pretenders", str(pretender.get("character")))
                strength = pretender.get("claimStrength", 0)
                if strength < 0 or strength > 100:
                    add("invalid_pretender_claim_strength", f"{loc}.succession.pretenders.claimStrength", str(strength))
        economy = state.get("economy")
        if not economy:
            add("missing_economy_state", f"{loc}.economy", "Faction has no economy state.")
        else:
            for field in ["warDebt", "foodStress", "tradeValue", "devastationLoss", "tributeDue"]:
                value = economy.get(field)
                if not isinstance(value, (int, float)):
                    add("invalid_economy_number", f"{loc}.economy.{field}", str(value))
                elif value < 0:
                    add("negative_economy_number", f"{loc}.economy.{field}", str(value))
            if isinstance(economy.get("foodStress"), (int, float)) and economy["foodStress"] > 100:
                add("economy_food_stress_out_of_range", f"{loc}.economy.foodStress", str(economy["foodStress"]))
            decision = economy.get("lastDecision")
            if decision and (not decision.get("type") or not decision.get("text")):
                add("invalid_economy_decision", f"{loc}.economy.lastDecision", str(decision))
        court = state.get("court")
        if not court:
            add("missing_court_state", f"{loc}.court", "Faction has no court state.")
        else:
            if court.get("faction") != faction_id:
                add("invalid_court_faction", f"{loc}.court.faction", str(court.get("faction")))
            stability = court.get("stability")
            if not isinstance(stability, (int, float)) or stability < 0 or stability > 100:
                add("invalid_court_stability", f"{loc}.court.stability", str(stability))
            offices = court.get("offices") or {}
            for office in COURT_OFFICES:
                if office not in offices:
                    add("missing_court_office", f"{loc}.court.offices.{office}", "Office slot is missing.")
            for office, assignment in offices.items():
                office_loc = f"{loc}.court.offices.{office}"
                if office not in COURT_OFFICES:
                    add("invalid_court_office", office_loc, str(office))
                if assignment is None:
                    continue
                if not isinstance(assignment, dict):
                    add("invalid_court_assignment", office_loc, "Office assignment must be null or an object.")
                    continue
                if assignment.get("office") != office:
                    add("court_office_mismatch", f"{office_loc}.office", str(assignment.get("office")))
                holder_id = assignment.get("character")
                holder = characters_by_id.get(holder_id)
                if not holder:
                    add("unknown_court_office_holder", f"{office_loc}.character", str(holder_id))
                else:
                    if holder.get("faction") != faction_id:
                        add("wrong_faction_court_office_holder", f"{office_loc}.character", str(holder_id))
                    if holder.get("alive") is False:
                        add("dead_court_office_holder", f"{office_loc}.character", str(holder_id))
                effectiveness = assignment.get("effectiveness")
                if not isinstance(effectiveness, (int, float)) or effectiveness < 0 or effectiveness > 100:
                    add("invalid_court_office_effectiveness", f"{office_loc}.effectiveness", str(effectiveness))

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

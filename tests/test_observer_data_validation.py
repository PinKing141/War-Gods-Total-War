"""Validation checks for the observer map and simulation data contract."""

from __future__ import annotations

import csv
import json
import os
import re
import sys
import tempfile
from pathlib import Path

from tests.observer_validation import (
    collect_runtime_validation_issues,
    collect_static_validation_issues,
    format_issues,
)


ROOT = Path(__file__).resolve().parents[1]
DATA_JS = ROOT / "docs" / "assets" / "data.js"
RNG_JS = ROOT / "docs" / "assets" / "rng.js"
SIM_JS = ROOT / "docs" / "assets" / "sim.js"
MAP_LAYERS_JS = ROOT / "docs" / "assets" / "map_layers.js"
PROVINCE_DEFINITIONS = ROOT / "docs" / "assets" / "provinces" / "world_province_definitions.csv"
PROVINCE_ADJACENCY = ROOT / "docs" / "assets" / "provinces" / "world_province_adjacency.csv"
PROVINCE_RIVER_FEATURES = ROOT / "docs" / "assets" / "rivers" / "province_river_features.csv"
SCENARIO_DIR = ROOT / "docs" / "assets" / "scenarios"


def _load_seed() -> dict:
    text = DATA_JS.read_text(encoding="utf-8")
    match = re.search(r"window\.WG_SEED\s*=\s*(\{.*\});\s*$", text, re.S)
    assert match, "docs/assets/data.js must expose window.WG_SEED as JSON"
    return json.loads(match.group(1))


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _local_map_faction_ids() -> set[str]:
    text = MAP_LAYERS_JS.read_text(encoding="utf-8")
    match = re.search(r"const LOCAL_FACTIONS = \{(.*?)\n  \};", text, re.S)
    if not match:
        return set()
    return set(re.findall(r"\bid: \"([^\"]+)\"", match.group(1)))


def _scenario_docs() -> list[tuple[str, dict]]:
    return [
        (str(path.relative_to(ROOT)).replace("\\", "/"), json.loads(path.read_text(encoding="utf-8")))
        for path in sorted(SCENARIO_DIR.glob("*.json"))
    ]


def test_validation_module_reports_clear_static_output():
    issues = collect_static_validation_issues(
        _load_seed(),
        _csv_rows(PROVINCE_DEFINITIONS),
        _csv_rows(PROVINCE_ADJACENCY),
        _csv_rows(PROVINCE_RIVER_FEATURES),
        _local_map_faction_ids(),
        _scenario_docs(),
        ROOT,
    )
    assert not issues, format_issues(issues)


def test_normal_ui_copy_avoids_debug_language():
    ui_text = (ROOT / "docs" / "assets" / "ui.js").read_text(encoding="utf-8")
    sim_text = (ROOT / "docs" / "assets" / "sim.js").read_text(encoding="utf-8")
    normal_ui_text = re.sub(
        r"debugMapPanel\(info\).*?\n    \/\* ---------- events ---------- \*\/",
        "",
        ui_text,
        flags=re.S,
    )
    banned_ui_phrases = [
        "Why it matters",
        "Likely goal",
        "Economy pressure",
        "Political pressure",
        "River data",
        "Current status",
        "War intent",
        "mapped placeholder",
        "world-map province",
    ]
    for phrase in banned_ui_phrases:
        assert phrase not in normal_ui_text
    assert "seeded risk" not in sim_text
    assert "current chance" not in sim_text
    assert "Intent:" not in sim_text


def test_validation_cli_outputs_clear_report():
    with tempfile.NamedTemporaryFile("w", suffix=".out", delete=False) as f:
        stdout_path = Path(f.name)
    with tempfile.NamedTemporaryFile("w", suffix=".err", delete=False) as f:
        stderr_path = Path(f.name)
    try:
        script = ROOT / "scripts" / "validate_observer_data.py"
        exit_code = os.system(
            f'cd /d "{ROOT}" && "{sys.executable}" "{script}" --runtime-days 5 --seed 123 '
            f'> "{stdout_path}" 2> "{stderr_path}"'
        )
        output = stdout_path.read_text(encoding="utf-8") + stderr_path.read_text(encoding="utf-8")
    finally:
        stdout_path.unlink(missing_ok=True)
        stderr_path.unlink(missing_ok=True)
    assert exit_code == 0, output
    assert "Observer Data Validation" in output
    assert "Static seed/map data: OK" in output
    assert "Runtime sample (5 day(s), seed 123, with sample war): OK" in output
    assert "Simulation self-check: OK" in output
    assert "Validation passed: no issues found." in output


def test_validation_cli_supports_25_year_smoke_gate():
    with tempfile.NamedTemporaryFile("w", suffix=".out", delete=False) as f:
        stdout_path = Path(f.name)
    with tempfile.NamedTemporaryFile("w", suffix=".err", delete=False) as f:
        stderr_path = Path(f.name)
    try:
        script = ROOT / "scripts" / "validate_observer_data.py"
        exit_code = os.system(
            f'cd /d "{ROOT}" && "{sys.executable}" "{script}" --years 25 --seed 123 '
            f'> "{stdout_path}" 2> "{stderr_path}"'
        )
        output = stdout_path.read_text(encoding="utf-8") + stderr_path.read_text(encoding="utf-8")
    finally:
        stdout_path.unlink(missing_ok=True)
        stderr_path.unlink(missing_ok=True)
    assert exit_code == 0, output
    assert "Runtime sample (25 year(s), seed 123, with sample war): OK" in output
    assert "Simulation self-check: OK" in output


def test_static_validation_reports_exact_broken_rows_and_fields():
    seed = json.loads(json.dumps(_load_seed()))
    seed["factions"][1]["id"] = seed["factions"][0]["id"]
    seed["factions"][2]["tier"] = "tier_missing"
    seed["factions"][3]["tierWeight"] = 0
    seed["provinces"][0]["controller"] = "FAC_MISSING"
    seed["provinces"][1]["fort"] = -1
    seed["claims"][0]["target"] = "PROV_MISSING"
    seed["mages"][0]["patron"] = "FAC_MISSING"
    province_rows = _csv_rows(PROVINCE_DEFINITIONS)
    province_rows[0] = {**province_rows[0], "controller": "FAC_MISSING", "road_level": "-1"}
    adjacency_rows = _csv_rows(PROVINCE_ADJACENCY)
    adjacency_rows[0] = {**adjacency_rows[0], "province_b": "PROV_MISSING"}
    river_rows = _csv_rows(PROVINCE_RIVER_FEATURES)
    river_rows[0] = {**river_rows[0], "province_id": "PROV_MISSING", "river_trade_value": "-1"}

    issues = collect_static_validation_issues(
        seed,
        province_rows,
        adjacency_rows,
        river_rows,
        _local_map_faction_ids(),
        _scenario_docs(),
        ROOT,
    )
    report = format_issues(issues)
    codes = {issue.code for issue in issues}

    assert "duplicate_id" in codes
    assert "invalid_faction_tier" in codes
    assert "invalid_faction_tier_weight" in codes
    assert "unknown_controller" in codes
    assert "negative_province_number" in codes
    assert "unknown_claim_target" in codes
    assert "unknown_mage_patron" in codes
    assert "unknown_map_controller" in codes
    assert "unknown_adjacency_province" in codes
    assert "unknown_river_feature_province" in codes
    assert "negative_river_feature_number" in codes
    assert "docs/assets/data.js:seed.factions:row 3.id" in report
    assert "docs/assets/provinces/world_province_definitions.csv:row 2" in report
    assert ".controller" in report


def test_default_scenario_manifest_validates_references():
    scenarios = _scenario_docs()
    assert [scenario["scenario_id"] for _, scenario in scenarios] == ["SCN_FRONTIER_CHRONICLE"]
    assert 16 <= len(scenarios[0][1]["active_factions"]) <= 20
    issues = collect_static_validation_issues(
        _load_seed(),
        _csv_rows(PROVINCE_DEFINITIONS),
        _csv_rows(PROVINCE_ADJACENCY),
        _csv_rows(PROVINCE_RIVER_FEATURES),
        _local_map_faction_ids(),
        scenarios,
        ROOT,
    )
    assert not issues, format_issues(issues)


def test_scenario_validation_reports_bad_references_and_paths():
    scenario = json.loads((SCENARIO_DIR / "default_frontier.json").read_text(encoding="utf-8"))
    scenario["scenario_id"] = ""
    scenario["start_year"] = -1
    scenario["data_sources"]["web_seed"] = "docs/assets/missing_seed.js"
    scenario["active_factions"].append("FAC_MISSING")
    scenario["focus_provinces"].append("PROV_MISSING")
    scenario["starting_wars"] = [{
        "attacker": "FAC_MISSING",
        "defender": "FAC_ROV_HALEN",
        "goal_province": "PROV_MISSING",
    }]
    issues = collect_static_validation_issues(
        _load_seed(),
        _csv_rows(PROVINCE_DEFINITIONS),
        _csv_rows(PROVINCE_ADJACENCY),
        _csv_rows(PROVINCE_RIVER_FEATURES),
        _local_map_faction_ids(),
        [("docs/assets/scenarios/broken.json", scenario)],
        ROOT,
    )
    codes = {issue.code for issue in issues}
    report = format_issues(issues)
    assert "missing_scenario_id" in codes
    assert "negative_scenario_start_year" in codes
    assert "missing_scenario_data_source" in codes
    assert "unknown_scenario_faction" in codes
    assert "unknown_scenario_province" in codes
    assert "unknown_scenario_war_attacker" in codes
    assert "unknown_scenario_war_goal" in codes
    assert "docs/assets/scenarios/broken.json:data_sources.web_seed" in report


def test_runtime_validation_reports_bad_army_war_and_state_fields():
    seed = _load_seed()
    snapshot = {
        "characters": [
            {**seed["characters"][0]},
            {**seed["characters"][0]},
            {**seed["characters"][1], "faction": "FAC_MISSING", "age": -2},
        ],
        "armies": [
            {
                "id": "ARMY_BAD",
                "faction": "FAC_MISSING",
                "loc": "PROV_MISSING",
                "nextLoc": "PROV_MISSING_NEXT",
                "dest": "PROV_MISSING_DEST",
                "commanderId": "CHAR_MISSING",
                "warId": "WAR_MISSING",
                "size": -1,
                "morale": -1,
                "supply": 8,
                "maxSupply": 3,
                "dailySupplyUse": -1,
            },
            {
                "id": "ARMY_BAD",
                "faction": seed["factions"][0]["id"],
                "loc": seed["provinces"][0]["id"],
                "commanderId": seed["characters"][0]["id"],
                "warId": "WAR_BAD",
                "size": 1,
                "morale": 1,
                "supply": 1,
                "maxSupply": 2,
                "dailySupplyUse": 0,
            },
        ],
        "wars": [
            {
                "id": "WAR_BAD",
                "attacker": "FAC_MISSING",
                "defender": seed["factions"][1]["id"],
                "goal": {"province": "PROV_MISSING"},
                "atkSide": ["FAC_MISSING"],
                "defSide": [seed["factions"][1]["id"]],
                "score": 0,
            },
            {
                "id": "WAR_BAD",
                "attacker": seed["factions"][0]["id"],
                "defender": "FAC_MISSING",
                "goal": {"province": seed["provinces"][0]["id"]},
                "atkSide": [seed["factions"][0]["id"]],
                "defSide": ["FAC_MISSING"],
                "score": "bad",
            },
        ],
        "revolts": [
            {
                "id": "REVOLT_BAD",
                "province": "PROV_MISSING",
                "against": "FAC_MISSING",
                "type": "peasant_revolt",
                "status": "bad",
                "strength": -5,
                "progress": 2,
                "causes": [],
            }
        ],
        "provinceState": {
            seed["provinces"][0]["id"]: {
                "controller": "FAC_MISSING",
                "occupier": "FAC_MISSING",
                "siege": {"by": "FAC_MISSING", "progress": 0},
                "revoltId": "REVOLT_MISSING",
                "pop": -1,
                "garrison": -1,
                "devastation": -1,
                "instability": -1,
                "recentConquest": -1,
            }
        },
        "factionState": {
            seed["factions"][0]["id"]: {
                "rulerId": "CHAR_MISSING",
                "treasury": -1,
                "manpower": -1,
                "maxManpower": -1,
                "prestige": -1,
                "exhaustion": -1,
                "internal": {
                    "courtTension": 101,
                    "successionTension": 0,
                    "armyInfluence": 0,
                    "taxBurden": 0,
                    "faithTension": 0,
                    "cultureTension": 0,
                    "regionalAutonomy": 0,
                    "nobleLoyalty": 0,
                    "merchantLoyalty": 0,
                    "revoltRisk": 0,
                    "successionPressure": 0,
                },
            }
        },
    }

    issues = collect_runtime_validation_issues(snapshot, seed)
    codes = {issue.code for issue in issues}
    report = format_issues(issues)

    assert "duplicate_id" in codes
    assert "unknown_army_faction" in codes
    assert "unknown_army_location" in codes
    assert "unknown_army_next_location" in codes
    assert "unknown_army_destination" in codes
    assert "unknown_army_commander" in codes
    assert "unknown_army_war" in codes
    assert "negative_army_number" in codes
    assert "army_supply_over_cap" in codes
    assert "unknown_war_attacker" in codes
    assert "unknown_war_defender" in codes
    assert "unknown_war_goal" in codes
    assert "invalid_war_score" in codes
    assert "unknown_runtime_controller" in codes
    assert "unknown_runtime_ruler" in codes
    assert "internal_politics_out_of_range" in codes
    assert "unknown_province_revolt" in codes
    assert "unknown_revolt_province" in codes
    assert "unknown_revolt_target" in codes
    assert "invalid_revolt_status" in codes
    assert "negative_revolt_strength" in codes
    assert "invalid_revolt_progress" in codes
    assert "runtime.armies[row 2" in report
    assert ".warId" in report


def test_seed_observer_ids_are_consistent():
    seed = _load_seed()
    factions = {f["id"] for f in seed["factions"]}
    provinces = {p["id"] for p in seed["provinces"]}
    cultures = set(seed["cultures"])
    religions = set(seed["religions"])
    species = set(seed["species"])
    characters = {c["id"] for c in seed["characters"]}

    assert len(factions) == len(seed["factions"])
    assert 16 <= len(factions) <= 20
    assert len(provinces) == len(seed["provinces"])
    assert len(characters) == len(seed["characters"])
    assert {f["tier"] for f in seed["factions"]} <= {"tier_1", "tier_2", "tier_3", "tier_4"}
    assert all(f["tierLabel"] for f in seed["factions"])
    assert all(f["tierWeight"] > 0 for f in seed["factions"])

    for faction in seed["factions"]:
      assert faction["culture"] in cultures
      assert faction["religion"] in religions
      assert faction["species"] in species

    for province in seed["provinces"]:
      assert province["controller"] in factions
      assert province["terrain"] in seed["terrains"]
      assert 0 <= province["x"] <= seed["world"]["width"]
      assert 0 <= province["y"] <= seed["world"]["height"]
      assert province["value"] >= 0
      assert province["fort"] >= 0
      assert province["roads"] >= 0

    for relation in seed["relations"]:
      assert relation["a"] in factions
      assert relation["b"] in factions
      assert relation["a"] != relation["b"]

    for claim in seed["claims"]:
      assert claim["claimant"] in factions
      assert claim["target"] in provinces
      assert claim["strength"] >= 0
      recognized_by = claim.get("recognizedBy")
      if isinstance(recognized_by, list):
        assert set(recognized_by) <= religions
      elif recognized_by:
        assert recognized_by in religions

    for character in seed["characters"]:
      assert character["faction"] in factions
      assert character["culture"] in cultures
      assert character["species"] in species
      assert character["age"] >= 0

    for mage in seed["mages"]:
      assert mage["character"] in characters
      assert mage["patron"] in factions
      assert mage["species"] in species
      assert mage["capacity"] >= 0
      assert mage["control"] >= 0
      assert mage["risk"] >= 0


def test_layered_province_csv_schema_and_values():
    seed = _load_seed()
    rows = _csv_rows(PROVINCE_DEFINITIONS)
    headers = set(rows[0])
    required = {
        "province_id", "red", "green", "blue", "common_name", "region_id",
        "controller", "terrain", "biome", "terrain_feature", "primary_resource",
        "road_level", "port_level", "fort_level", "strategic_value",
        "center_x", "center_y", "pixel_area", "is_seed_frontier",
    }
    assert required <= headers

    seed_provinces = {p["id"] for p in seed["provinces"]}
    known_factions = {f["id"] for f in seed["factions"]} | _local_map_faction_ids()
    province_ids = [row["province_id"] for row in rows]
    rgb_keys = [(row["red"], row["green"], row["blue"]) for row in rows]

    assert len(province_ids) == len(set(province_ids))
    assert len(rgb_keys) == len(set(rgb_keys))
    assert seed_provinces <= set(province_ids)

    for row in rows:
      assert row["controller"] in known_factions
      assert row["terrain"]
      assert row["biome"] in {"forest", "marsh", "steppe", "dryland", "mountain", "oasis", "farmland", "coast"}
      assert row["terrain_feature"]
      assert 0 <= int(row["red"]) <= 255
      assert 0 <= int(row["green"]) <= 255
      assert 0 <= int(row["blue"]) <= 255
      assert 0 <= float(row["center_x"]) <= 3072
      assert 0 <= float(row["center_y"]) <= 2048
      assert int(row["pixel_area"]) > 0
      assert int(row["road_level"]) >= 0
      assert int(row["port_level"]) >= 0
      assert int(row["fort_level"]) >= 0
      assert int(row["strategic_value"]) >= 0


def test_layered_adjacency_and_river_feature_ids_resolve():
    defined = {row["province_id"] for row in _csv_rows(PROVINCE_DEFINITIONS)}

    adjacency_rows = _csv_rows(PROVINCE_ADJACENCY)
    assert adjacency_rows
    for row in adjacency_rows:
      assert row["province_a"] in defined
      assert row["province_b"] in defined
      assert row["province_a"] != row["province_b"]

    river_headers = set(_csv_rows(PROVINCE_RIVER_FEATURES)[0])
    assert {
        "province_id", "river_ids", "primary_river_id", "has_major_river",
        "has_tributary", "has_floodplain", "has_crossing", "navigable_river",
        "river_trade_value", "river_defense_bonus", "river_movement_penalty",
        "supply_bonus", "farmland_bonus",
    } <= river_headers
    for row in _csv_rows(PROVINCE_RIVER_FEATURES):
      assert row["province_id"] in defined
      for field in ["river_trade_value", "river_defense_bonus", "river_movement_penalty", "supply_bonus", "farmland_bonus"]:
        assert int(row[field]) >= 0


def test_live_simulation_generates_valid_runtime_references():
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        snapshot_path = Path(f.name)
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
        runner_path = Path(f.name)
    script = f"""
const fs = require('fs');
const vm = require('vm');
global.window = global;
global.WG = {{}};
for (const file of {json.dumps([str(DATA_JS), str(RNG_JS), str(SIM_JS)])}) {{
  vm.runInThisContext(fs.readFileSync(file, 'utf8'), {{ filename: file }});
}}
function parseCsv(text) {{
  return text.trim().split(/\\r?\\n/).slice(1).map((line) => line.split(','));
}}
const sim = new WG.Simulation(WG_SEED, 123);
const seedProvinceIds = new Set(WG_SEED.provinces.map((p) => p.id));
sim.adjacency = Object.fromEntries([...seedProvinceIds].map((id) => [id, []]));
for (const [a, b] of parseCsv(fs.readFileSync({json.dumps(str(PROVINCE_ADJACENCY))}, 'utf8'))) {{
  if (seedProvinceIds.has(a) && seedProvinceIds.has(b)) {{
    sim.adjacency[a].push(b);
    sim.adjacency[b].push(a);
  }}
}}
sim._declareWar('FAC_ROV_HALEN', 'FAC_NINE_BANNERS_HALLOW', null, false);
for (let i = 0; i < 40; i++) sim.tick();
fs.writeFileSync({json.dumps(str(snapshot_path))}, JSON.stringify({{
  wars: sim.wars,
  revolts: sim.revolts,
  armies: sim.armies,
  characters: sim.characters,
  provinceState: sim.provinceState,
  factionState: sim.factionState,
  monthlyRecaps: sim.monthlyRecaps,
  simulationHealth: sim.validateState(),
}}));
"""
    try:
        runner_path.write_text(script, encoding="utf-8")
        exit_code = os.system(f'cd /d "{ROOT}" && node "{runner_path}" >NUL 2>NUL')
        assert exit_code == 0
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    finally:
        runner_path.unlink(missing_ok=True)
        snapshot_path.unlink(missing_ok=True)
    seed = _load_seed()
    issues = collect_runtime_validation_issues(snapshot, seed)
    assert not issues, format_issues(issues)

    factions = {f["id"] for f in seed["factions"]}
    provinces = {p["id"] for p in seed["provinces"]}
    cultures = set(seed["cultures"])
    species = set(seed["species"])
    characters = {c["id"] for c in snapshot["characters"]}

    assert snapshot["wars"]
    assert snapshot["armies"]
    assert snapshot["monthlyRecaps"]
    assert snapshot["simulationHealth"]["ok"] is True
    assert snapshot["simulationHealth"]["issues"] == []

    for war in snapshot["wars"]:
      assert war["attacker"] in factions
      assert war["defender"] in factions
      assert set(war["atkSide"]) <= factions
      assert set(war["defSide"]) <= factions
      assert war["goal"]["province"] in provinces
      assert isinstance(war["score"], (int, float))
      assert war["intentReason"]
      for battle in war["battles"]:
        assert battle["winner"] in factions
        assert battle["loser"] in factions
        assert battle["loc"] in provinces
        assert battle["winnerLosses"] >= 0
        assert battle["loserLosses"] >= 0

    for army in snapshot["armies"]:
      assert army["faction"] in factions
      assert army["loc"] in provinces
      assert army["commanderId"] in characters
      assert army["size"] >= 0
      assert army["supply"] >= 0
      assert army["maxSupply"] >= 0
      assert army["dailySupplyUse"] >= 0
      assert isinstance(army["undersupplied"], bool)
      assert army["intentReason"]

    for character in snapshot["characters"]:
      assert character["faction"] in factions
      assert character["culture"] in cultures
      assert character["species"] in species
      assert character["age"] >= 0

    for province_id, state in snapshot["provinceState"].items():
      assert province_id in provinces
      assert state["controller"] in factions
      assert state["pop"] >= 0
      assert state["garrison"] >= 0
      assert state["devastation"] >= 0
      if state["occupier"]:
        assert state["occupier"] in factions
      if state["siege"]:
        assert state["siege"]["by"] in factions
        assert state["siege"]["progress"] >= 0

    for faction_id, state in snapshot["factionState"].items():
      assert faction_id in factions
      assert state["treasury"] >= 0
      assert state["manpower"] >= 0
      assert state["maxManpower"] >= 0
      assert state["prestige"] >= 0
      assert state["exhaustion"] >= 0


def test_supply_movement_siege_and_peace_contracts():
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        snapshot_path = Path(f.name)
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
        runner_path = Path(f.name)
    script = f"""
const fs = require('fs');
const vm = require('vm');
global.window = global;
global.WG = {{}};
for (const file of {json.dumps([str(DATA_JS), str(RNG_JS), str(SIM_JS)])}) {{
  vm.runInThisContext(fs.readFileSync(file, 'utf8'), {{ filename: file }});
}}
const sim = new WG.Simulation(WG_SEED, 777);
sim.adjacency = {{
  PROV_ROV_HALEM: ['PROV_NINTH_BANNER', 'PROV_WEST_GEAR'],
  PROV_NINTH_BANNER: ['PROV_ROV_HALEM'],
  PROV_WEST_GEAR: ['PROV_ROV_HALEM'],
  PROV_SEVRIN_CANAL: ['PROV_ROV_HALEM'],
  PROV_RED_BOG: ['PROV_ROV_HALEM'],
  PROV_OPEN_GATE: ['PROV_NINTH_BANNER'],
  PROV_THIRD_CHARTER: ['PROV_NINTH_BANNER'],
  PROV_BLUE_CHAIN: ['PROV_ROV_HALEM'],
  PROV_WHITE_MARE: ['PROV_NINTH_BANNER'],
}};
sim._declareWar('FAC_ROV_HALEN', 'FAC_NINE_BANNERS_HALLOW', null, false);
const war = sim.wars[0];
const army = sim.armies.find((a) => a.faction === 'FAC_ROV_HALEN');
const roadMove = sim._movementDays(army, 'PROV_ROV_HALEM');
const mountainMove = sim._movementDays(army, 'PROV_WEST_GEAR');
const baseSupplyUse = sim._supplyUseFor(army, sim.province('PROV_ROV_HALEM'), 'camp');
const marshSupplyUse = sim._supplyUseFor(army, sim.province('PROV_RED_BOG'), 'camp');
const drylandSupplyUse = sim._supplyUseFor(army, sim.province('PROV_WHITE_MARE'), 'camp');
army.loc = 'PROV_NINTH_BANNER';
army.supply = 1;
const beforeAttrition = army.size;
sim._consumeArmySupply(army, war, 'siege');
const afterAttrition = army.size;
army.maxSupply = 500;
army.supply = army.maxSupply;
sim.province('PROV_NINTH_BANNER').fort = 1;
sim.provinceState.PROV_NINTH_BANNER.garrison = 80;
sim.provinceState.PROV_NINTH_BANNER.siege = null;
for (let i = 0; i < 140 && !sim.provinceState.PROV_NINTH_BANNER.occupier; i++) {{
  sim._siegeTick(army, war);
}}
const siegeState = sim.provinceState.PROV_NINTH_BANNER;
const occupiedBeforePeace = siegeState.occupier;
war.score = 60;
sim._peacePulse();
fs.writeFileSync({json.dumps(str(snapshot_path))}, JSON.stringify({{
  roadMove,
  mountainMove,
  baseSupplyUse,
  marshSupplyUse,
  drylandSupplyUse,
  beforeAttrition,
  afterAttrition,
  undersupplied: army.undersupplied,
  dailySupplyUse: army.dailySupplyUse,
  siegeOccupiedBy: occupiedBeforePeace,
  peaceSummary: war.peaceSummary,
  revolts: sim.revolts,
  warOver: war.over,
  intentReason: war.intentReason,
  armyIntentReason: army.intentReason,
  siegeEventsLogged: sim.events.filter((ev) => ev.type === 'siege').map((ev) => ev.text),
  simulationHealth: sim.validateState(),
}}));
"""
    try:
        runner_path.write_text(script, encoding="utf-8")
        exit_code = os.system(f'cd /d "{ROOT}" && node "{runner_path}" >NUL 2>NUL')
        assert exit_code == 0
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    finally:
        runner_path.unlink(missing_ok=True)
        snapshot_path.unlink(missing_ok=True)

    assert snapshot["mountainMove"] > snapshot["roadMove"]
    assert snapshot["marshSupplyUse"] > snapshot["baseSupplyUse"]
    assert snapshot["drylandSupplyUse"] > snapshot["baseSupplyUse"]
    assert snapshot["afterAttrition"] < snapshot["beforeAttrition"]
    assert snapshot["undersupplied"] is True
    assert snapshot["dailySupplyUse"] > 0
    assert snapshot["siegeOccupiedBy"] == "FAC_ROV_HALEN"
    assert len(snapshot["siegeEventsLogged"]) >= 3
    assert snapshot["warOver"] is True
    assert snapshot["peaceSummary"]["reason"]
    assert snapshot["peaceSummary"]["changedHands"]
    assert snapshot["peaceSummary"]["prestige"]
    assert "truce" in snapshot["peaceSummary"]["truce"]
    assert snapshot["intentReason"]
    assert snapshot["armyIntentReason"]
    assert snapshot["simulationHealth"]["ok"] is True


def test_simulation_self_check_reports_broken_runtime_references():
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        snapshot_path = Path(f.name)
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
        runner_path = Path(f.name)
    script = f"""
const fs = require('fs');
const vm = require('vm');
global.window = global;
global.WG = {{}};
for (const file of {json.dumps([str(DATA_JS), str(RNG_JS), str(SIM_JS)])}) {{
  vm.runInThisContext(fs.readFileSync(file, 'utf8'), {{ filename: file }});
}}
const sim = new WG.Simulation(WG_SEED, 222);
sim.armies.push({{
  id: 'ARMY_BAD',
  faction: 'FAC_DOES_NOT_EXIST',
  loc: 'PROV_MISSING',
  commanderId: 'CHAR_MISSING',
  warId: 'WAR_MISSING',
  size: -10,
  morale: 50,
  supply: -1,
  maxSupply: 0,
  dailySupplyUse: -2,
  undersupplied: true,
}});
sim.provinceState.PROV_ROV_HALEM.controller = 'FAC_MISSING';
sim.claims.push({{ id: 'CLAIM_BAD', claimant: 'FAC_MISSING', target: 'PROV_MISSING', strength: -3 }});
fs.writeFileSync({json.dumps(str(snapshot_path))}, JSON.stringify(sim.validateState()));
"""
    try:
        runner_path.write_text(script, encoding="utf-8")
        exit_code = os.system(f'cd /d "{ROOT}" && node "{runner_path}" >NUL 2>NUL')
        assert exit_code == 0
        health = json.loads(snapshot_path.read_text(encoding="utf-8"))
    finally:
        runner_path.unlink(missing_ok=True)
        snapshot_path.unlink(missing_ok=True)

    codes = {issue["code"] for issue in health["issues"]}
    assert health["ok"] is False
    assert "unknown_army_faction" in codes
    assert "unknown_army_location" in codes
    assert "unknown_army_commander" in codes
    assert "negative_army_number" in codes
    assert "unknown_runtime_controller" in codes
    assert "unknown_claim_target" in codes

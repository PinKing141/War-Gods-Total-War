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


def test_validation_module_reports_clear_static_output():
    issues = collect_static_validation_issues(
        _load_seed(),
        _csv_rows(PROVINCE_DEFINITIONS),
        _csv_rows(PROVINCE_ADJACENCY),
        _csv_rows(PROVINCE_RIVER_FEATURES),
        _local_map_faction_ids(),
    )
    assert not issues, format_issues(issues)


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
    assert "Validation passed: no issues found." in output


def test_seed_observer_ids_are_consistent():
    seed = _load_seed()
    factions = {f["id"] for f in seed["factions"]}
    provinces = {p["id"] for p in seed["provinces"]}
    cultures = set(seed["cultures"])
    religions = set(seed["religions"])
    species = set(seed["species"])
    characters = {c["id"] for c in seed["characters"]}

    assert len(factions) == len(seed["factions"])
    assert len(provinces) == len(seed["provinces"])
    assert len(characters) == len(seed["characters"])

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
  armies: sim.armies,
  characters: sim.characters,
  provinceState: sim.provinceState,
  factionState: sim.factionState,
  monthlyRecaps: sim.monthlyRecaps,
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
  warOver: war.over,
  intentReason: war.intentReason,
  armyIntentReason: army.intentReason,
  siegeEventsLogged: sim.events.filter((ev) => ev.type === 'siege').map((ev) => ev.text),
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

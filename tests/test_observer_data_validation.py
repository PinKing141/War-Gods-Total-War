"""Validation checks for the observer map and simulation data contract."""

from __future__ import annotations

import csv
import json
import os
import re
import tempfile
from pathlib import Path


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

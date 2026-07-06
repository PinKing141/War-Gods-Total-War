"""Smoke tests for the browser map data wiring."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB_SEED = ROOT / "docs" / "assets" / "data.js"
INDEX_HTML = ROOT / "docs" / "index.html"
MAIN_JS = ROOT / "docs" / "assets" / "main.js"
MAP_LAYERS = ROOT / "docs" / "assets" / "map_layers.js"
PROCEDURAL_ARCHIVE = ROOT / "docs" / "assets" / "map_procedural_old.js"
PROVINCE_DEFINITIONS = ROOT / "docs" / "assets" / "provinces" / "world_province_definitions.csv"
PROVINCE_ADJACENCY = ROOT / "docs" / "assets" / "provinces" / "world_province_adjacency.csv"


def _load_web_seed() -> dict:
    text = WEB_SEED.read_text(encoding="utf-8")
    match = re.search(r"window\.WG_SEED\s*=\s*(\{.*\});\s*$", text, re.S)
    assert match, "docs/assets/data.js must expose window.WG_SEED as JSON"
    return json.loads(match.group(1))


def _province_definition_ids() -> set[str]:
    with PROVINCE_DEFINITIONS.open(newline="", encoding="utf-8") as f:
        return {row["province_id"] for row in csv.DictReader(f)}


def test_web_army_locations_exist_in_province_definitions():
    """Browser armies spawn at faction capitals, and every such loc must be a map province ID."""
    seed = _load_web_seed()
    defined_ids = _province_definition_ids()

    owned_by_faction: dict[str, list[dict]] = {}
    for province in seed["provinces"]:
        assert province["id"] in defined_ids
        owned_by_faction.setdefault(province["controller"], []).append(province)

    army_locations = {
        max(provinces, key=lambda p: p["value"])["id"]
        for provinces in owned_by_faction.values()
    }

    assert army_locations
    assert army_locations <= defined_ids


def test_world_adjacency_references_defined_provinces():
    """CSV movement neighbours must not point outside the unique-RGB province definition table."""
    defined_ids = _province_definition_ids()
    with PROVINCE_ADJACENCY.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            assert row["province_a"] in defined_ids
            assert row["province_b"] in defined_ids


def test_normal_app_uses_layered_map_without_procedural_fallback():
    """Normal gameplay must not load or silently fall back to the old procedural ownership grid."""
    html = INDEX_HTML.read_text(encoding="utf-8")
    scripts = re.findall(r'<script src="([^"]+)"></script>', html)

    assert "assets/map_base.js" in scripts
    assert "assets/map_layers.js" in scripts
    assert "assets/map.js" not in scripts
    assert "assets/map_procedural_old.js" not in scripts
    assert scripts.index("assets/map_base.js") < scripts.index("assets/map_layers.js")

    main = MAIN_JS.read_text(encoding="utf-8")
    layers = MAP_LAYERS.read_text(encoding="utf-8")
    archive = PROCEDURAL_ARCHIVE.read_text(encoding="utf-8")

    assert "WG.LayeredWorldMap || WG.WorldMap" not in main
    assert "useOldMap ? WG.ProceduralWorldMap : WG.LayeredWorldMap" in main
    assert "class LayeredWorldMap extends WG.MapBase" in layers
    assert "using generated map fallback" not in layers
    assert "super.provinceAt" not in layers
    assert "super._paintWorld" not in layers
    assert "this.cellOwner = this._renderProvinceIndex" in layers
    assert "window.WG.ProceduralWorldMap = ProceduralWorldMap" in archive

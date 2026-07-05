"""Smoke tests for the browser map data wiring."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB_SEED = ROOT / "docs" / "assets" / "data.js"
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

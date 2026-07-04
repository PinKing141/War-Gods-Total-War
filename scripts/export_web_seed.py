"""Bake the lore CSV layer into a static JS seed for the web observer app.

Reads src/warfare_simulation/config/lore_csv and writes docs/assets/data.js
containing `window.WG_SEED`. The web app (docs/) is fully static so it can be
served by GitHub Pages; this script is the only bridge from the Python side.

Usage:
    python scripts/export_web_seed.py
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LORE = ROOT / "src" / "warfare_simulation" / "config" / "lore_csv"
OUT = ROOT / "docs" / "assets" / "data.js"

# ---------------------------------------------------------------------------
# Hand-authored presentation data the CSVs don't carry: map coordinates,
# faction colors, and heraldic charge keys. World space is 1600 x 1000.
# ---------------------------------------------------------------------------

PROVINCE_COORDS = {
    "PROV_WEST_GEAR":     (250, 470),
    "PROV_RED_BOG":       (620, 195),
    "PROV_OPEN_GATE":     (935, 250),
    "PROV_ROV_HALEM":     (665, 520),
    "PROV_SEVRIN_CANAL":  (470, 650),
    "PROV_NINTH_BANNER":  (835, 420),
    "PROV_THIRD_CHARTER": (1000, 585),
    "PROV_BLUE_CHAIN":    (700, 810),
    "PROV_WHITE_MARE":    (1300, 400),
}

FACTION_STYLE = {
    "FAC_ROV_HALEN":          {"color": "#3f6fc4", "charge": "bridge"},
    "FAC_KAERN_RED_BOG":      {"color": "#a83a2c", "charge": "cairn"},
    "FAC_GHARU_OPEN_GATE":    {"color": "#4d8a3c", "charge": "gate"},
    "FAC_KAVARI_WEST_GEAR":   {"color": "#8a7440", "charge": "peak"},
    "FAC_NALARI_THIRD_CHARTER": {"color": "#7f5ca8", "charge": "scroll"},
    "FAC_MAREN_BLUE_CHAIN":   {"color": "#2e9aa0", "charge": "bell"},
    "FAC_TALUUN_WHITE_MARE":  {"color": "#c08a34", "charge": "horseshoe"},
    "FAC_NINE_BANNERS_HALLOW": {"color": "#a03058", "charge": "banners"},
}

# Rivers as polylines in world space (mountains -> Rov Halem -> sea).
RIVERS = [
    [(300, 430), (420, 470), (540, 500), (640, 525), (690, 600), (700, 700), (705, 830), (715, 940)],
    [(640, 230), (655, 330), (690, 420), (665, 505)],
    [(470, 660), (560, 620), (650, 545)],
]

TERRAIN_INFO = {
    "river_city":        {"label": "River City",        "base": "#b2a37c", "moveDays": 2, "defense": 2},
    "canal_farmland":    {"label": "Canal Farmland",    "base": "#a4a870", "moveDays": 2, "defense": 0},
    "bog_forest":        {"label": "Bog Forest",        "base": "#6e7a52", "moveDays": 4, "defense": 3},
    "frontier_farms":    {"label": "Frontier Farms",    "base": "#aaa671", "moveDays": 2, "defense": 0},
    "mountain_pass":     {"label": "Mountain Pass",     "base": "#8d8578", "moveDays": 5, "defense": 5},
    "charter_city":      {"label": "Charter City",      "base": "#b3a184", "moveDays": 2, "defense": 2},
    "river_port":        {"label": "River Port",        "base": "#a09f73", "moveDays": 2, "defense": 1},
    "steppe_market":     {"label": "Steppe Market",     "base": "#c2ae74", "moveDays": 3, "defense": 0},
    "sacred_battlefield": {"label": "Sacred Battlefield", "base": "#af9f7a", "moveDays": 2, "defense": 1},
}

SPECIES_LIFESPAN = {
    # start of elderly decline, hard ceiling-ish
    "human": (52, 90),
    "orc": (44, 78),
    "human_orc_mixed": (48, 84),
    "dwarf": (120, 230),
    "elf": (300, 600),
    "mixed": (55, 95),
}


def read_csv(rel: str) -> list[dict[str, str]]:
    with open(LORE / rel, newline="", encoding="utf-8") as fh:
        return [dict(row) for row in csv.DictReader(fh)]


def to_int(value: str, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def build_seed() -> dict:
    factions = []
    for row in read_csv("12_seed_frontier/seed_factions.csv"):
        style = FACTION_STYLE[row["faction_id"]]
        factions.append({
            "id": row["faction_id"],
            "name": row["name"],
            "identity": row["identity"],
            "culture": row["dominant_culture"],
            "species": row["dominant_species"],
            "religion": row["religion_id"],
            "government": row["government"],
            "pressure": row["conflict_pressure"],
            "goal": row["primary_goal"],
            "color": style["color"],
            "charge": style["charge"],
        })

    provinces = []
    for row in read_csv("12_seed_frontier/seed_provinces.csv"):
        x, y = PROVINCE_COORDS[row["province_id"]]
        provinces.append({
            "id": row["province_id"],
            "name": row["common_name"],
            "localName": row["local_name"],
            "imperialName": row["old_imperial_name"],
            "religiousName": row["religious_name"],
            "enemyName": row["enemy_name"],
            "region": row["region_id"],
            "controller": row["controller"],
            "terrain": row["terrain"],
            "resource": row["primary_resource"],
            "roads": to_int(row["road_level"]),
            "port": to_int(row["port_level"]),
            "fort": to_int(row["fort_level"]),
            "manaSite": to_int(row["mana_site_level"]),
            "value": to_int(row["strategic_value"]),
            "x": x,
            "y": y,
        })

    relations = [
        {
            "a": row["faction_a"],
            "b": row["faction_b"],
            "score": to_int(row["score"]),
            "tension": row["main_tension"].replace("_", " "),
            "warRisk": to_int(row["war_risk"]),
        }
        for row in read_csv("12_seed_frontier/seed_relations.csv")
    ]

    characters = [
        {
            "id": row["character_id"],
            "name": row["name"],
            "species": row["species_id"],
            "culture": row["culture_id"],
            "faction": row["faction_id"],
            "role": row["role"].replace("_", " "),
            "age": to_int(row["age"]),
            "pressure": row["core_pressure"],
        }
        for row in read_csv("12_seed_frontier/seed_characters.csv")
    ]

    claims = [
        {
            "id": row["claim_id"],
            "claimant": row["claimant"],
            "target": row["target"],
            "type": row["claim_type"].replace("_", " "),
            "source": row["source"],
            "strength": to_int(row["strength"]),
            "myth": row["myth_status"].replace("_", " "),
            "recognizedBy": row["recognized_by"],
        }
        for row in read_csv("12_seed_frontier/seed_claims.csv")
    ]

    mages = [
        {
            "id": row["mage_id"],
            "character": row["character_id"],
            "species": row["species_id"],
            "capacity": to_int(row["capacity"]),
            "control": to_int(row["control"]),
            "strain": to_int(row["strain_tolerance"]),
            "specialization": row["specialization"].replace("_", " "),
            "legal": row["legal_status"].replace("_", " "),
            "patron": row["patron_faction"],
            "risk": to_int(row["risk_score"]),
        }
        for row in read_csv("12_seed_frontier/seed_mages.csv")
    ]

    cultures = {
        row["culture_id"]: {
            "selfName": row["self_name"],
            "name": row["common_name"],
            "meaning": row["meaning"],
            "location": row["location"],
            "values": row["values"].replace(",", ", ").replace("_", " "),
            "military": row["military_style"].replace(",", ", ").replace("_", " "),
            "contradiction": row["contradiction"],
        }
        for row in read_csv("05_cultures/cultures.csv")
    }

    religions = {
        row["religion_id"]: {
            "name": row["name"],
            "type": row["type"].replace("_", " "),
            "claim": row["core_claim"],
            "warStance": row["war_stance"].replace("_", " "),
            "mageStance": row["mage_stance"].replace("_", " "),
        }
        for row in read_csv("06_religion/religions.csv")
    }

    species = {}
    for row in read_csv("03_species/species.csv"):
        old_age, max_age = SPECIES_LIFESPAN.get(row["species_id"], (55, 95))
        species[row["species_id"]] = {
            "name": row["common_name"],
            "selfName": row["self_name"],
            "oldAge": old_age,
            "maxAge": max_age,
        }
    for sid, (old_age, max_age) in SPECIES_LIFESPAN.items():
        species.setdefault(sid, {"name": sid.replace("_", " ").title(),
                                 "selfName": "", "oldAge": old_age, "maxAge": max_age})

    naming: dict[str, dict[str, list[str]]] = {}
    for row in read_csv("10_naming_data/name_generation_morphemes.csv"):
        culture = "CULT_" + row["style_id"].removeprefix("NSTYLE_")
        bucket = naming.setdefault(culture, {"roots": [], "suffixes": []})
        key = "roots" if row["type"] == "root" else "suffixes"
        bucket[key].append(row["value"])

    return {
        "world": {"width": 1600, "height": 1000, "startYear": 1,
                  "region": "Rov Basin north-east frontier"},
        "factions": factions,
        "provinces": provinces,
        "relations": relations,
        "characters": characters,
        "claims": claims,
        "mages": mages,
        "cultures": cultures,
        "religions": religions,
        "species": species,
        "naming": naming,
        "terrains": TERRAIN_INFO,
        "rivers": [[list(pt) for pt in river] for river in RIVERS],
    }


def main() -> None:
    seed = build_seed()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(seed, ensure_ascii=False, indent=1)
    OUT.write_text(
        "// Generated by scripts/export_web_seed.py — do not edit by hand.\n"
        f"window.WG_SEED = {payload};\n",
        encoding="utf-8",
    )
    print(f"wrote {OUT} ({OUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()

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
    "FAC_ROV_HALEN":          {"color": "#3f6fc4", "charge": "bridge", "short": "Rov Halem"},
    "FAC_KAERN_RED_BOG":      {"color": "#a83a2c", "charge": "cairn", "short": "Red Bog"},
    "FAC_GHARU_OPEN_GATE":    {"color": "#4d8a3c", "charge": "gate", "short": "Open Gate"},
    "FAC_KAVARI_WEST_GEAR":   {"color": "#8a7440", "charge": "peak", "short": "West Gear"},
    "FAC_NALARI_THIRD_CHARTER": {"color": "#7f5ca8", "charge": "scroll", "short": "Third Charter"},
    "FAC_MAREN_BLUE_CHAIN":   {"color": "#2e9aa0", "charge": "bell", "short": "Blue Chain"},
    "FAC_TALUUN_WHITE_MARE":  {"color": "#c08a34", "charge": "horseshoe", "short": "White Mare"},
    "FAC_NINE_BANNERS_HALLOW": {"color": "#a03058", "charge": "banners", "short": "Nine Banners"},
    "FAC_LANTER_SEA_LEAGUE":  {"color": "#1f7f93", "charge": "bell", "short": "Lanter Sea"},
    "FAC_NORTHGREY_HIGHLANDS": {"color": "#7c4a36", "charge": "cairn", "short": "Northgrey"},
    "FAC_QERESH_SALT_ROAD":   {"color": "#b99a35", "charge": "horseshoe", "short": "Qeresh Road"},
    "FAC_EASTERN_REED_CONFED": {"color": "#6f8f4e", "charge": "gate", "short": "Eastern Reed"},
    "FAC_OSTREN_BANNERFIELDS": {"color": "#9f8f45", "charge": "banners", "short": "Ostren"},
    "FAC_SALT_WITNESS_PROTECTORATE": {"color": "#c0a24a", "charge": "scroll", "short": "Salt Witness"},
    "FAC_GREEN_CROWN_COURT":  {"color": "#3f7a45", "charge": "cairn", "short": "Green Crown"},
    "FAC_DEEP_LEDGER_HOLD":   {"color": "#6d6a60", "charge": "peak", "short": "Deep Ledger"},
}

CULTURE_COLORS = {
    "CULT_ROVANT": "#4a6fc0", "CULT_KAERN": "#b04a38", "CULT_GHARU": "#55923f",
    "CULT_KAVARI": "#97803e", "CULT_NALARI": "#8a63b8", "CULT_MAREN": "#3a9d9d",
    "CULT_TALUUN": "#cf9a3e", "CULT_QERESH": "#c2a14a", "CULT_OSTREN": "#7a9a5a",
    "multi_culture": "#9a5a72",
}

RELIGION_COLORS = {
    "REL_MEASURE_ROADS": "#5577cc", "REL_NINE_BANNERS": "#b34a6b",
    "REL_HEARTH_BELOW": "#a05a32", "REL_INNER_STONE": "#8d8578",
    "REL_LONG_ACCOUNT": "#7f5ca8", "REL_BELL_RETURN": "#2e9aa0",
    "REL_SALT_WITNESS": "#c2a14a",
}

FACTION_TIERS = {
    "tier_1": {"label": "Great Power", "weight": 1.35},
    "tier_2": {"label": "Regional Power", "weight": 1.10},
    "tier_3": {"label": "Minor State", "weight": 0.88},
    "tier_4": {"label": "Background Power", "weight": 0.55},
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
            "tier": row.get("tier") or "tier_3",
            "tierLabel": FACTION_TIERS.get(row.get("tier") or "tier_3", FACTION_TIERS["tier_3"])["label"],
            "tierWeight": FACTION_TIERS.get(row.get("tier") or "tier_3", FACTION_TIERS["tier_3"])["weight"],
            "pressure": row["conflict_pressure"],
            "goal": row["primary_goal"],
            "color": style["color"],
            "charge": style["charge"],
            "shortName": style["short"],
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
        "cultureColors": CULTURE_COLORS,
        "religionColors": RELIGION_COLORS,
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

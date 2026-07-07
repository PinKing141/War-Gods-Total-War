"""Validate observer seed data and a small runtime simulation sample.

Usage:
    python scripts/validate_observer_data.py
    python scripts/validate_observer_data.py --runtime-days 120 --seed 777
    python scripts/validate_observer_data.py --static-only
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.observer_validation import (  # noqa: E402
    ValidationIssue,
    collect_runtime_validation_issues,
    collect_static_validation_issues,
)


DATA_JS = ROOT / "docs" / "assets" / "data.js"
RNG_JS = ROOT / "docs" / "assets" / "rng.js"
SIM_JS = ROOT / "docs" / "assets" / "sim.js"
MAP_LAYERS_JS = ROOT / "docs" / "assets" / "map_layers.js"
PROVINCE_DEFINITIONS = ROOT / "docs" / "assets" / "provinces" / "world_province_definitions.csv"
PROVINCE_ADJACENCY = ROOT / "docs" / "assets" / "provinces" / "world_province_adjacency.csv"
PROVINCE_RIVER_FEATURES = ROOT / "docs" / "assets" / "rivers" / "province_river_features.csv"


def load_seed() -> dict:
    text = DATA_JS.read_text(encoding="utf-8")
    match = re.search(r"window\.WG_SEED\s*=\s*(\{.*\});\s*$", text, re.S)
    if not match:
        raise RuntimeError(f"{DATA_JS} must expose window.WG_SEED as JSON")
    return json.loads(match.group(1))


def csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def local_map_faction_ids() -> set[str]:
    if not MAP_LAYERS_JS.exists():
        return set()
    text = MAP_LAYERS_JS.read_text(encoding="utf-8")
    match = re.search(r"const LOCAL_FACTIONS = \{(.*?)\n  \};", text, re.S)
    if not match:
        return set()
    return set(re.findall(r"\bid: \"([^\"]+)\"", match.group(1)))


def collect_static(seed: dict) -> list[ValidationIssue]:
    return collect_static_validation_issues(
        seed,
        csv_rows(PROVINCE_DEFINITIONS),
        csv_rows(PROVINCE_ADJACENCY),
        csv_rows(PROVINCE_RIVER_FEATURES),
        local_map_faction_ids(),
    )


def runtime_snapshot(*, seed: int, runtime_days: int, sample_war: bool) -> dict:
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as snapshot_file:
        snapshot_path = Path(snapshot_file.name)
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as runner_file:
        runner_path = Path(runner_file.name)
    with tempfile.NamedTemporaryFile("w", suffix=".out", delete=False, encoding="utf-8") as stdout_file:
        stdout_path = Path(stdout_file.name)
    with tempfile.NamedTemporaryFile("w", suffix=".err", delete=False, encoding="utf-8") as stderr_file:
        stderr_path = Path(stderr_file.name)

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
const sim = new WG.Simulation(WG_SEED, {seed});
const seedProvinceIds = new Set(WG_SEED.provinces.map((p) => p.id));
sim.adjacency = Object.fromEntries([...seedProvinceIds].map((id) => [id, []]));
for (const [a, b] of parseCsv(fs.readFileSync({json.dumps(str(PROVINCE_ADJACENCY))}, 'utf8'))) {{
  if (seedProvinceIds.has(a) && seedProvinceIds.has(b)) {{
    sim.adjacency[a].push(b);
    sim.adjacency[b].push(a);
  }}
}}
if ({str(sample_war).lower()}) {{
  sim._declareWar('FAC_ROV_HALEN', 'FAC_NINE_BANNERS_HALLOW', null, false);
}}
for (let i = 0; i < {runtime_days}; i++) sim.tick();
fs.writeFileSync({json.dumps(str(snapshot_path))}, JSON.stringify({{
  wars: sim.wars,
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
        cd = f'cd /d "{ROOT}"' if os.name == "nt" else f'cd "{ROOT}"'
        exit_code = os.system(f'{cd} && node "{runner_path}" > "{stdout_path}" 2> "{stderr_path}"')
        if exit_code != 0:
            output = (
                stderr_path.read_text(encoding="utf-8")
                + stdout_path.read_text(encoding="utf-8")
                or "no node output"
            ).strip()
            raise RuntimeError(f"Node runtime sample failed:\n{output}")
        return json.loads(snapshot_path.read_text(encoding="utf-8"))
    finally:
        runner_path.unlink(missing_ok=True)
        snapshot_path.unlink(missing_ok=True)
        stdout_path.unlink(missing_ok=True)
        stderr_path.unlink(missing_ok=True)


def print_group(title: str, issues: list[ValidationIssue]) -> None:
    status = "OK" if not issues else f"{len(issues)} issue(s)"
    print(f"{title}: {status}")
    for issue in issues:
        print(f"  {issue.format()}")


def simulation_health_issues(snapshot: dict) -> list[ValidationIssue]:
    health = snapshot.get("simulationHealth") or {}
    issues = []
    for issue in health.get("issues", []):
        severity = issue.get("severity", "error")
        code = f"sim_{severity}_{issue.get('code', 'unknown')}"
        issues.append(ValidationIssue(code, issue.get("location", "simulation"), issue.get("message", "")))
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate War Gods observer data.")
    parser.add_argument("--seed", type=int, default=123, help="Runtime sample RNG seed.")
    parser.add_argument("--runtime-days", type=int, default=40, help="Days to tick in the runtime sample.")
    parser.add_argument("--static-only", action="store_true", help="Only validate static seed/map CSV data.")
    parser.add_argument("--no-sample-war", action="store_true", help="Do not create a deterministic sample war before ticking.")
    args = parser.parse_args()

    seed = load_seed()
    static_issues = collect_static(seed)
    runtime_issues: list[ValidationIssue] = []
    health_issues: list[ValidationIssue] = []

    if not args.static_only:
        snapshot = runtime_snapshot(
            seed=args.seed,
            runtime_days=max(0, args.runtime_days),
            sample_war=not args.no_sample_war,
        )
        runtime_issues = collect_runtime_validation_issues(snapshot, seed)
        health_issues = simulation_health_issues(snapshot)

    print("Observer Data Validation")
    print_group("Static seed/map data", static_issues)
    if args.static_only:
        print("Runtime sample: skipped")
    else:
        sample = "with sample war" if not args.no_sample_war else "without sample war"
        print_group(f"Runtime sample ({args.runtime_days} day(s), seed {args.seed}, {sample})", runtime_issues)
        print_group("Simulation self-check", health_issues)

    total = len(static_issues) + len(runtime_issues) + len(health_issues)
    if total:
        print(f"\nValidation failed: {total} issue(s) found.")
        return 1
    print("\nValidation passed: no issues found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

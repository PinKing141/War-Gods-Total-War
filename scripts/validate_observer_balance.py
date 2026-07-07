"""Run the Phase 5-C observer balance gate.

The gate is intentionally small and deterministic: it does not try to prove
the world is perfectly balanced, only that the expanded 16-power setup avoids
the obvious failures called out in the roadmap.

Usage:
    python scripts/validate_observer_balance.py
    python scripts/validate_observer_balance.py --years 25 --seeds 101 202
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_JS = ROOT / "docs" / "assets" / "data.js"
RNG_JS = ROOT / "docs" / "assets" / "rng.js"
SIM_JS = ROOT / "docs" / "assets" / "sim.js"
PROVINCE_ADJACENCY = ROOT / "docs" / "assets" / "provinces" / "world_province_adjacency.csv"


def run_sample(seed: int, years: int) -> dict:
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
for (let i = 0; i < {years * 360}; i++) sim.tick();
const originalControllers = new Set(WG_SEED.provinces.map((p) => p.controller));
const controllers = {{}};
for (const [provinceId, state] of Object.entries(sim.provinceState)) {{
  controllers[state.controller] = (controllers[state.controller] || 0) + 1;
}}
const participants = new Set();
for (const war of sim.wars) {{
  for (const factionId of [...war.atkSide, ...war.defSide]) participants.add(factionId);
}}
const health = sim.validateState();
const values = Object.values(controllers);
fs.writeFileSync(process.argv[2], JSON.stringify({{
  seed: {seed},
  years: {years},
  wars: sim.wars.length,
  endedWars: sim.wars.filter((w) => w.over).length,
  activeWars: sim.wars.filter((w) => !w.over).length,
  participants: participants.size,
  controlledFactions: Object.keys(controllers).length,
  restoredPowers: Object.keys(controllers).filter((id) => !originalControllers.has(id)).length,
  largestController: values.length ? Math.max(...values) : 0,
  events: sim.events.length,
  recaps: sim.monthlyRecaps.length,
  healthOk: health.ok,
  healthIssues: health.issues,
  controllers,
}}));
"""
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as runner:
        runner_path = Path(runner.name)
        runner.write(script)
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as output:
        output_path = Path(output.name)
    with tempfile.NamedTemporaryFile("w", suffix=".out", delete=False, encoding="utf-8") as stdout:
        stdout_path = Path(stdout.name)
    with tempfile.NamedTemporaryFile("w", suffix=".err", delete=False, encoding="utf-8") as stderr:
        stderr_path = Path(stderr.name)
    try:
        cd = f'cd /d "{ROOT}"' if os.name == "nt" else f'cd "{ROOT}"'
        exit_code = os.system(f'{cd} && node "{runner_path}" "{output_path}" > "{stdout_path}" 2> "{stderr_path}"')
        if exit_code:
            output_text = (
                stderr_path.read_text(encoding="utf-8")
                + stdout_path.read_text(encoding="utf-8")
                or "node balance sample failed"
            ).strip()
            raise RuntimeError(output_text)
        return json.loads(output_path.read_text(encoding="utf-8"))
    finally:
        runner_path.unlink(missing_ok=True)
        output_path.unlink(missing_ok=True)
        stdout_path.unlink(missing_ok=True)
        stderr_path.unlink(missing_ok=True)


def sample_issues(sample: dict) -> list[str]:
    issues = []
    if not sample["healthOk"]:
        issues.append(f"simulation health failed: {sample['healthIssues']}")
    if sample["wars"] < 3:
        issues.append(f"no-war dead world risk: only {sample['wars']} war(s)")
    if sample["endedWars"] < 1:
        issues.append("permanent-war or no-resolution risk: no wars ended")
    if sample["activeWars"] > 4:
        issues.append(f"total chaos risk: {sample['activeWars']} active wars remain")
    if sample["participants"] < 6:
        issues.append(f"regional tension too narrow: only {sample['participants']} war participant(s)")
    if sample["controlledFactions"] < 5:
        issues.append(f"collapse risk: only {sample['controlledFactions']} faction(s) still hold provinces")
    if sample["largestController"] > 5:
        issues.append(f"snowball risk: largest controller holds {sample['largestController']} provinces")
    if sample["restoredPowers"] < 2:
        issues.append(f"expanded powers too passive: only {sample['restoredPowers']} restored power(s)")
    if sample["events"] < 250:
        issues.append(f"chronicle silence risk: only {sample['events']} event(s)")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 5-C observer balance.")
    parser.add_argument("--years", type=int, default=50, help="Years per deterministic balance sample.")
    parser.add_argument("--seeds", type=int, nargs="+", default=[101, 202, 303, 404, 505])
    args = parser.parse_args()

    print("Observer Balance Validation")
    print(f"Years per sample: {args.years}")
    failures = []
    for seed in args.seeds:
        sample = run_sample(seed, args.years)
        issues = sample_issues(sample)
        status = "OK" if not issues else f"{len(issues)} issue(s)"
        print(
            f"Seed {seed}: {status} | wars={sample['wars']} ended={sample['endedWars']} "
            f"active={sample['activeWars']} participants={sample['participants']} "
            f"holders={sample['controlledFactions']} restored={sample['restoredPowers']} "
            f"largest={sample['largestController']} events={sample['events']}"
        )
        for issue in issues:
            print(f"  - {issue}")
        if issues:
            failures.append((seed, issues))

    if failures:
        print(f"\nBalance validation failed: {len(failures)} seed(s) failed.")
        return 1
    print("\nBalance validation passed: expanded world avoids silence, collapse and runaway snowballing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

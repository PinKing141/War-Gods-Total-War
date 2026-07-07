"""Phase 6-B internal politics tests."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _run_node(script: str) -> dict:
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as runner:
        runner_path = Path(runner.name)
        runner.write(script)
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as output:
        output_path = Path(output.name)
    with tempfile.NamedTemporaryFile("w", suffix=".out", delete=False) as stdout:
        stdout_path = Path(stdout.name)
    with tempfile.NamedTemporaryFile("w", suffix=".err", delete=False) as stderr:
        stderr_path = Path(stderr.name)
    try:
        exit_code = os.system(
            f'cd /d "{ROOT}" && node "{runner_path}" "{output_path}" '
            f'> "{stdout_path}" 2> "{stderr_path}"'
        )
        output_text = stdout_path.read_text(encoding="utf-8") + stderr_path.read_text(encoding="utf-8")
        assert exit_code == 0, output_text
        return json.loads(output_path.read_text(encoding="utf-8"))
    finally:
        runner_path.unlink(missing_ok=True)
        output_path.unlink(missing_ok=True)
        stdout_path.unlink(missing_ok=True)
        stderr_path.unlink(missing_ok=True)


def test_internal_politics_stress_changes_economy_and_war_willingness():
    script = r"""
const fs = require('fs');
const vm = require('vm');
global.window = global;
global.WG = {};
for (const file of ['docs/assets/data.js', 'docs/assets/rng.js', 'docs/assets/sim.js']) {
  vm.runInThisContext(fs.readFileSync(file, 'utf8'), { filename: file });
}
const sim = new WG.Simulation(WG_SEED, 321);
const fid = 'FAC_MAREN_BLUE_CHAIN';
const defender = 'FAC_LANTER_SEA_LEAGUE';
const beforeIncome = sim.monthlyIncome(fid);
const beforeInstability = sim.internalInstability(fid);
const beforeWar = sim._priorityWarMultiplier(fid, defender, null, false);
Object.assign(sim.factionState[fid].internal, {
  courtTension: 80,
  successionTension: 72,
  armyInfluence: 30,
  taxBurden: 82,
  faithTension: 35,
  cultureTension: 42,
  regionalAutonomy: 76,
  nobleLoyalty: 24,
  merchantLoyalty: 18,
  revoltRisk: 70,
  successionPressure: 75,
});
const afterIncome = sim.monthlyIncome(fid);
const afterInstability = sim.internalInstability(fid);
const afterWar = sim._priorityWarMultiplier(fid, defender, null, false);
fs.writeFileSync(process.argv[2], JSON.stringify({
  beforeIncome,
  afterIncome,
  beforeInstability,
  afterInstability,
  beforeWar,
  afterWar,
  summary: sim.internalPoliticsSummary(fid),
  health: sim.validateState(),
}));
"""
    result = _run_node(script)

    assert result["afterInstability"] > result["beforeInstability"]
    assert result["afterIncome"] < result["beforeIncome"]
    assert result["afterWar"] < result["beforeWar"]
    assert any(row["label"] == "Court tension" for row in result["summary"])
    assert result["health"]["ok"] is True


def test_monthly_internal_politics_tracks_pressure_and_stays_valid():
    script = r"""
const fs = require('fs');
const vm = require('vm');
global.window = global;
global.WG = {};
for (const file of ['docs/assets/data.js', 'docs/assets/rng.js', 'docs/assets/sim.js']) {
  vm.runInThisContext(fs.readFileSync(file, 'utf8'), { filename: file });
}
const sim = new WG.Simulation(WG_SEED, 654);
const fid = 'FAC_ROV_HALEN';
const before = { ...sim.factionState[fid].internal };
sim.factionState[fid].treasury = 15;
sim.factionState[fid].exhaustion = 58;
sim.factionState[fid].manpower = 0;
sim.provinceState.PROV_ROV_HALEM.occupier = 'FAC_NINE_BANNERS_HALLOW';
sim.provinceState.PROV_SEVRIN_CANAL.siege = { by: 'FAC_NINE_BANNERS_HALLOW', progress: 0.4 };
sim._updateInternalPolitics(fid);
const after = sim.factionState[fid].internal;
fs.writeFileSync(process.argv[2], JSON.stringify({
  before,
  after,
  instability: sim.internalInstability(fid),
  health: sim.validateState(),
}));
"""
    result = _run_node(script)

    assert result["after"]["taxBurden"] > result["before"]["taxBurden"]
    assert result["after"]["successionPressure"] >= result["before"]["successionPressure"]
    assert result["after"]["revoltRisk"] > result["before"]["revoltRisk"]
    assert 0 <= result["instability"] <= 100
    assert result["health"]["ok"] is True

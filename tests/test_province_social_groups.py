"""Phase 9-B province social group tests."""

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


def test_province_society_exists_and_inspector_shows_readable_summary():
    script = r"""
const fs = require('fs');
const vm = require('vm');
global.window = global;
global.WG = {};
for (const file of ['docs/assets/data.js', 'docs/assets/rng.js', 'docs/assets/sim.js']) {
  vm.runInThisContext(fs.readFileSync(file, 'utf8'), { filename: file });
}
const sim = new WG.Simulation(WG_SEED, 9101);
const pid = 'PROV_ROV_HALEM';
const expected = ['nobles', 'clergy', 'merchants', 'peasants', 'craftsmen', 'soldiers', 'mages', 'scholars', 'minorities', 'tribes', 'foreign_settlers', 'refugees', 'urban_poor'];
const society = sim.provinceState[pid].society;
const summary = sim.provinceSocietySummary(pid);
const uiSource = fs.readdirSync('docs/assets/ui').sort().map((f) => fs.readFileSync('docs/assets/ui/' + f, 'utf8')).join('\n');
fs.writeFileSync(process.argv[2], JSON.stringify({
  groups: Object.keys(society).sort(),
  sample: society.peasants,
  summary,
  health: sim.validateState(),
  uiMentionsSociety: uiSource.includes('<h3>Society</h3>') && uiSource.includes('provinceSocietySummary') && uiSource.includes('Social Pressure'),
  expected,
}));
"""
    result = _run_node(script)

    assert result["groups"] == sorted(result["expected"])
    assert result["sample"]["size"] > 0
    assert 0 <= result["sample"]["loyalty"] <= 100
    assert result["sample"]["needs"]
    assert result["summary"]["dominant"]
    assert "tax" in result["summary"]["effects"]
    assert result["health"]["ok"] is True
    assert result["uiMentionsSociety"] is True


def test_social_groups_affect_tax_recruitment_unrest_and_tension():
    script = r"""
const fs = require('fs');
const vm = require('vm');
global.window = global;
global.WG = {};
for (const file of ['docs/assets/data.js', 'docs/assets/rng.js', 'docs/assets/sim.js']) {
  vm.runInThisContext(fs.readFileSync(file, 'utf8'), { filename: file });
}
const pid = 'PROV_ROV_HALEM';
const fid = 'FAC_ROV_HALEN';
function tuned(overrides) {
  const sim = new WG.Simulation(WG_SEED, 9102);
  Object.assign(sim.provinceState[pid].society.merchants, overrides.merchants || {});
  Object.assign(sim.provinceState[pid].society.craftsmen, overrides.craftsmen || {});
  Object.assign(sim.provinceState[pid].society.soldiers, overrides.soldiers || {});
  Object.assign(sim.provinceState[pid].society.nobles, overrides.nobles || {});
  Object.assign(sim.provinceState[pid].society.minorities, overrides.minorities || {});
  Object.assign(sim.provinceState[pid].society.refugees, overrides.refugees || {});
  return {
    effects: sim.societyEffects(pid),
    income: sim.monthlyIncome(fid),
    instability: sim.provinceInstability(pid),
    manpowerBefore: sim.factionState[fid].maxManpower,
    sim,
  };
}
const calm = tuned({
  merchants: { wealth: 90, loyalty: 85, unrest: 3 },
  craftsmen: { wealth: 88, loyalty: 82, unrest: 4 },
  soldiers: { loyalty: 82, influence: 75, unrest: 3 },
  nobles: { loyalty: 82, influence: 70, unrest: 4 },
  minorities: { loyalty: 80, unrest: 3 },
  refugees: { loyalty: 72, unrest: 5 },
});
const troubled = tuned({
  merchants: { wealth: 18, loyalty: 18, unrest: 78 },
  craftsmen: { wealth: 16, loyalty: 20, unrest: 76 },
  soldiers: { loyalty: 18, influence: 22, unrest: 72 },
  nobles: { loyalty: 20, influence: 22, unrest: 74 },
  minorities: { loyalty: 8, unrest: 90 },
  refugees: { loyalty: 7, unrest: 92 },
});
troubled.sim._updateInternalPolitics(fid);
fs.writeFileSync(process.argv[2], JSON.stringify({
  calm: { effects: calm.effects, income: calm.income, instability: calm.instability.score },
  troubled: {
    effects: troubled.effects,
    income: troubled.income,
    instability: troubled.instability.score,
    causes: troubled.instability.causes,
    internal: troubled.sim.factionState[fid].internal,
  },
}));
"""
    result = _run_node(script)

    assert result["calm"]["effects"]["tax"] > result["troubled"]["effects"]["tax"]
    assert result["calm"]["effects"]["recruitment"] > result["troubled"]["effects"]["recruitment"]
    assert result["troubled"]["effects"]["unrest"] > result["calm"]["effects"]["unrest"]
    assert result["troubled"]["effects"]["cultureTension"] > result["calm"]["effects"]["cultureTension"]
    assert result["troubled"]["effects"]["faithTension"] > result["calm"]["effects"]["faithTension"]
    assert result["troubled"]["instability"] > result["calm"]["instability"]
    assert "social unrest" in result["troubled"]["causes"]
    assert result["troubled"]["internal"]["revoltRisk"] > 0


def test_social_group_validation_reports_broken_province_society():
    script = r"""
const fs = require('fs');
const vm = require('vm');
global.window = global;
global.WG = {};
for (const file of ['docs/assets/data.js', 'docs/assets/rng.js', 'docs/assets/sim.js']) {
  vm.runInThisContext(fs.readFileSync(file, 'utf8'), { filename: file });
}
const sim = new WG.Simulation(WG_SEED, 9103);
sim.provinceState.PROV_ROV_HALEM.society = {
  nobles: { size: -1, loyalty: 200, unrest: 'bad', needs: '', wealth: -3, influence: 101 },
  fake_group: { size: 1, loyalty: 50, unrest: 10, needs: 'noise', wealth: 20, influence: 5 },
};
fs.writeFileSync(process.argv[2], JSON.stringify(sim.validateState()));
"""
    health = _run_node(script)
    codes = {issue["code"] for issue in health["issues"]}

    assert health["ok"] is False
    assert "missing_social_group" in codes
    assert "invalid_social_group" in codes
    assert "invalid_social_group_number" in codes
    assert "social_group_out_of_range" in codes
    assert "missing_social_group_needs" in codes

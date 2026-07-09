"""Phase 9-A court and office system tests."""

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


def test_courts_assign_offices_and_inspectors_show_them():
    script = r"""
const fs = require('fs');
const vm = require('vm');
global.window = global;
global.WG = {};
for (const file of ['docs/assets/data.js', 'docs/assets/rng.js', 'docs/assets/sim.js']) {
  vm.runInThisContext(fs.readFileSync(file, 'utf8'), { filename: file });
}
const sim = new WG.Simulation(WG_SEED, 9901);
const fid = 'FAC_ROV_HALEN';
const court = sim.courtOf(fid);
const ruler = sim.rulerOf(fid);
const rulerOffices = sim.characterOffices(ruler.id);
const uiSource = fs.readFileSync('docs/assets/ui.js', 'utf8');
fs.writeFileSync(process.argv[2], JSON.stringify({
  court,
  rulerId: ruler.id,
  rulerOfficeNames: rulerOffices.map((o) => o.office),
  effects: sim.courtEffects(fid),
  health: sim.validateState(),
  uiMentionsCourt: uiSource.includes('Court & Offices') && uiSource.includes('Office') && uiSource.includes('courtOfficeRows'),
}));
"""
    result = _run_node(script)

    assert result["court"]["offices"]["ruler"]["character"] == result["rulerId"]
    assert "ruler" in result["rulerOfficeNames"]
    assert result["court"]["filled"] >= 1
    assert 0 <= result["court"]["stability"] <= 100
    assert "war" in result["effects"]
    assert result["health"]["ok"] is True
    assert result["uiMentionsCourt"] is True


def test_offices_affect_income_internal_tension_and_ai_priorities():
    script = r"""
const fs = require('fs');
const vm = require('vm');
global.window = global;
global.WG = {};
for (const file of ['docs/assets/data.js', 'docs/assets/rng.js', 'docs/assets/sim.js']) {
  vm.runInThisContext(fs.readFileSync(file, 'utf8'), { filename: file });
}
const fid = 'FAC_MAREN_BLUE_CHAIN';
function withCourt(effectiveness) {
  const sim = new WG.Simulation(WG_SEED, 9902);
  const court = sim.courtOf(fid);
  const holder = sim.rulerOf(fid).id;
  for (const office of ['chancellor', 'steward', 'spymaster', 'marshal', 'captain_of_guard', 'governor', 'regent', 'high_priest']) {
    court.offices[office] = { office, label: sim.officeLabel(office), character: holder, effectiveness };
  }
  sim.factionState[fid].court = court;
  Object.assign(sim.factionState[fid].internal, {
    courtTension: 70,
    successionTension: 55,
    armyInfluence: 55,
    taxBurden: 55,
    faithTension: 55,
    regionalAutonomy: 55,
    nobleLoyalty: 35,
  });
  const income = sim.monthlyIncome(fid);
  const priority = Object.fromEntries(sim.aiPriorityScores(fid).map((p) => [p.id, p.score]));
  for (let i = 0; i < 8; i++) sim._updateInternalPolitics(fid);
  return { income, priority, internal: sim.factionState[fid].internal };
}
const weak = withCourt(0);
const strong = withCourt(100);
fs.writeFileSync(process.argv[2], JSON.stringify({ weak, strong }));
"""
    result = _run_node(script)

    assert result["strong"]["income"] > result["weak"]["income"]
    assert result["strong"]["internal"]["courtTension"] < result["weak"]["internal"]["courtTension"]
    assert result["strong"]["internal"]["taxBurden"] < result["weak"]["internal"]["taxBurden"]
    assert result["strong"]["priority"]["secure_trade_routes"] > result["weak"]["priority"]["secure_trade_routes"]


def test_court_validation_reports_broken_office_state():
    script = r"""
const fs = require('fs');
const vm = require('vm');
global.window = global;
global.WG = {};
for (const file of ['docs/assets/data.js', 'docs/assets/rng.js', 'docs/assets/sim.js']) {
  vm.runInThisContext(fs.readFileSync(file, 'utf8'), { filename: file });
}
const sim = new WG.Simulation(WG_SEED, 9903);
const fid = 'FAC_TALUUN_WHITE_MARE';
const other = sim.rulerOf('FAC_ROV_HALEN');
sim.factionState[fid].court = {
  faction: 'FAC_MISSING',
  stability: 150,
  offices: {
    ruler: { office: 'marshal', character: 'CHAR_MISSING', effectiveness: 120 },
    fake_office: { office: 'fake_office', character: other.id, effectiveness: 10 },
    marshal: { office: 'marshal', character: other.id, effectiveness: 20 },
  },
};
fs.writeFileSync(process.argv[2], JSON.stringify(sim.validateState()));
"""
    health = _run_node(script)
    codes = {issue["code"] for issue in health["issues"]}

    assert health["ok"] is False
    assert "invalid_court_faction" in codes
    assert "invalid_court_stability" in codes
    assert "missing_court_office" in codes
    assert "court_office_mismatch" in codes
    assert "unknown_court_office_holder" in codes
    assert "wrong_faction_court_office_holder" in codes
    assert "invalid_court_office" in codes
    assert "invalid_court_office_effectiveness" in codes

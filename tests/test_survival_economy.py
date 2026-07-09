"""Phase 6-E simple survival economy tests."""

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


def test_survival_economy_tracks_debt_food_trade_and_decisions():
    script = r"""
const fs = require('fs');
const vm = require('vm');
global.window = global;
global.WG = {};
for (const file of ['docs/assets/data.js', 'docs/assets/rng.js', 'docs/assets/sim.js']) {
  vm.runInThisContext(fs.readFileSync(file, 'utf8'), { filename: file });
}
const sim = new WG.Simulation(WG_SEED, 8101);
const fid = 'FAC_MAREN_BLUE_CHAIN';
const st = sim.factionState[fid];
st.treasury = 40;
st.economy.warDebt = 0;
st.internal.taxBurden = 30;
for (const p of sim.ownedProvinces(fid)) sim.provinceState[p.id].devastation = 68;
const before = sim.economySnapshot(fid);
sim._survivalEconomyDecision(fid, { ...before, net: -180, foodStress: 20, warDebt: 0, treasury: 40 });
const afterDecision = sim.economySnapshot(fid);
sim._monthlyPulse();
const afterMonth = sim.economySnapshot(fid);
fs.writeFileSync(process.argv[2], JSON.stringify({
  before,
  afterDecision,
  afterMonth,
  decision: sim.factionState[fid].economy.lastDecision,
  health: sim.validateState(),
}));
"""
    result = _run_node(script)

    assert result["before"]["tradeValue"] > 0
    assert result["before"]["devastationLoss"] > 0
    assert result["decision"]["type"] in {"raise taxes", "borrow money"}
    assert result["afterMonth"]["foodStress"] >= 0
    assert result["afterMonth"]["warDebt"] >= 0
    assert result["health"]["ok"] is True


def test_survival_economy_can_borrow_dismiss_and_push_peace():
    script = r"""
const fs = require('fs');
const vm = require('vm');
global.window = global;
global.WG = {};
for (const file of ['docs/assets/data.js', 'docs/assets/rng.js', 'docs/assets/sim.js']) {
  vm.runInThisContext(fs.readFileSync(file, 'utf8'), { filename: file });
}
const sim = new WG.Simulation(WG_SEED, 8102);
sim.adjacency = {
  PROV_ROV_HALEM: ['PROV_NINTH_BANNER'],
  PROV_NINTH_BANNER: ['PROV_ROV_HALEM'],
  PROV_SEVRIN_CANAL: ['PROV_ROV_HALEM'],
  PROV_RED_BOG: ['PROV_ROV_HALEM'],
  PROV_OPEN_GATE: ['PROV_NINTH_BANNER'],
  PROV_WEST_GEAR: ['PROV_ROV_HALEM'],
  PROV_THIRD_CHARTER: ['PROV_NINTH_BANNER'],
  PROV_BLUE_CHAIN: ['PROV_ROV_HALEM'],
  PROV_WHITE_MARE: ['PROV_NINTH_BANNER'],
};
sim._declareWar('FAC_ROV_HALEN', 'FAC_NINE_BANNERS_HALLOW', null, false);
const fid = 'FAC_ROV_HALEN';
const st = sim.factionState[fid];
st.treasury = 20;
st.economy.warDebt = 850;
st.internal.taxBurden = 80;
const beforeArmies = sim.armies.length;
sim._survivalEconomyDecision(fid, { ...sim.economySnapshot(fid), treasury: 20, net: -220, warDebt: 850, foodStress: 20 });
const decision = st.economy.lastDecision;
st.economy.warDebt = 1000;
const army = sim.armies.find((a) => a.faction === fid);
if (army) army.size = 50000;
for (const war of sim.wars) if (war.attacker === fid) war.score = -10;
sim._peacePulse();
const war = sim.wars.find((w) => w.attacker === fid);
fs.writeFileSync(process.argv[2], JSON.stringify({
  beforeArmies,
  afterArmies: sim.armies.length,
  decision,
  debt: st.economy.warDebt,
  warOver: war.over,
  peaceReason: war.peaceSummary && war.peaceSummary.reason,
  health: sim.validateState(),
}));
"""
    result = _run_node(script)

    assert result["decision"]["type"] in {"borrow money", "sell privileges"}
    assert result["debt"] >= 0
    assert result["warOver"] is True
    assert "war debt" in result["peaceReason"]
    assert result["health"]["ok"] is True

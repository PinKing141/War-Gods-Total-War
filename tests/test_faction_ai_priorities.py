"""Phase 6-A faction AI priority tests."""

from __future__ import annotations

import json
import os
import sys
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


def test_faction_ai_priorities_are_archetype_specific():
    script = r"""
const fs = require('fs');
const vm = require('vm');
global.window = global;
global.WG = {};
for (const file of ['docs/assets/data.js', 'docs/assets/rng.js', 'docs/assets/sim.js']) {
  vm.runInThisContext(fs.readFileSync(file, 'utf8'), { filename: file });
}
const sim = new WG.Simulation(WG_SEED, 123);
function top(fid, n = 5) {
  return sim.aiPriorityScores(fid).slice(0, n).map((p) => p.id);
}
const rovClaim = sim.claims.find((c) => c.claimant === 'FAC_ROV_HALEN');
fs.writeFileSync(process.argv[2], JSON.stringify({
  taluun: top('FAC_TALUUN_WHITE_MARE'),
  maren: top('FAC_MAREN_BLUE_CHAIN'),
  kavari: top('FAC_KAVARI_WEST_GEAR'),
  banners: top('FAC_NINE_BANNERS_HALLOW'),
  summary: sim.aiPrioritySummary('FAC_MAREN_BLUE_CHAIN'),
  warReason: sim._warIntentReason('FAC_ROV_HALEN', 'FAC_GHARU_OPEN_GATE', rovClaim, false),
}));
"""
    result = _run_node(script)

    assert result["taluun"][0] == "raid_for_wealth"
    assert result["maren"][0] == "secure_trade_routes"
    assert "control_ports" in result["maren"][:3]
    assert "hold_mountain_passes" in result["kavari"][:3]
    assert "defend_faith" in result["banners"][:4]
    assert "Secure trade routes" in result["summary"]
    assert "court priority" in result["warReason"]


def test_faction_ai_priorities_respond_to_runtime_stress():
    script = r"""
const fs = require('fs');
const vm = require('vm');
global.window = global;
global.WG = {};
for (const file of ['docs/assets/data.js', 'docs/assets/rng.js', 'docs/assets/sim.js']) {
  vm.runInThisContext(fs.readFileSync(file, 'utf8'), { filename: file });
}
const sim = new WG.Simulation(WG_SEED, 456);
const fid = 'FAC_MAREN_BLUE_CHAIN';
const before = sim.aiPriorityScores(fid).slice(0, 3).map((p) => p.id);
sim.factionState[fid].treasury = 20;
sim.factionState[fid].manpower = 0;
sim.factionState[fid].exhaustion = 55;
const after = sim.aiPriorityScores(fid).slice(0, 4).map((p) => p.id);
fs.writeFileSync(process.argv[2], JSON.stringify({ before, after }));
"""
    result = _run_node(script)

    assert result["before"][0] == "secure_trade_routes"
    assert "avoid_war" in result["after"][:3]
    assert "survive_economic_stress" in result["after"][:4]

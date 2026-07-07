"""Phase 6-C revolt and province instability tests."""

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


def test_revolt_can_start_win_and_be_recorded():
    script = r"""
const fs = require('fs');
const vm = require('vm');
global.window = global;
global.WG = {};
for (const file of ['docs/assets/data.js', 'docs/assets/rng.js', 'docs/assets/sim.js']) {
  vm.runInThisContext(fs.readFileSync(file, 'utf8'), { filename: file });
}
const sim = new WG.Simulation(WG_SEED, 9001);
const pid = 'PROV_OPEN_GATE';
const st = sim.provinceState[pid];
st.devastation = 80;
st.garrison = 40;
st.recentConquest = 40;
Object.assign(sim.factionState[st.controller].internal, {
  taxBurden: 90,
  regionalAutonomy: 88,
  cultureTension: 70,
  faithTension: 64,
  nobleLoyalty: 18,
  revoltRisk: 88,
});
const instability = sim.provinceInstability(pid);
const revolt = sim._startRevolt(pid, 'separatist_revolt');
revolt.progress = 0.98;
sim._revoltPulse();
fs.writeFileSync(process.argv[2], JSON.stringify({
  instability,
  revolt,
  province: sim.provinceState[pid],
  events: sim.events.filter((ev) => ev.type === 'revolt').map((ev) => ev.text),
  health: sim.validateState(),
}));
"""
    result = _run_node(script)

    assert result["instability"]["score"] >= 55
    assert "high taxes" in result["instability"]["causes"]
    assert result["revolt"]["status"] == "won"
    assert result["province"]["revoltId"] is None
    assert result["province"]["recentConquest"] > 0
    assert any("wins because" in event for event in result["events"])
    assert result["health"]["ok"] is True


def test_revolt_can_be_suppressed_and_validation_catches_bad_revolts():
    script = r"""
const fs = require('fs');
const vm = require('vm');
global.window = global;
global.WG = {};
for (const file of ['docs/assets/data.js', 'docs/assets/rng.js', 'docs/assets/sim.js']) {
  vm.runInThisContext(fs.readFileSync(file, 'utf8'), { filename: file });
}
const sim = new WG.Simulation(WG_SEED, 9002);
const pid = 'PROV_ROV_HALEM';
sim.provinceState[pid].garrison = 1200;
sim.provinceState[pid].devastation = 70;
const revolt = sim._startRevolt(pid, 'peasant_revolt');
revolt.progress = 0.01;
sim._revoltPulse();
sim.revolts.push({
  id: 'REVOLT_BAD',
  type: 'peasant_revolt',
  province: 'PROV_MISSING',
  against: 'FAC_MISSING',
  status: 'bad',
  strength: -1,
  progress: 2,
  causes: [],
});
const health = sim.validateState();
fs.writeFileSync(process.argv[2], JSON.stringify({
  revolt,
  province: sim.provinceState[pid],
  eventTexts: sim.events.filter((ev) => ev.type === 'revolt').map((ev) => ev.text),
  health,
}));
"""
    result = _run_node(script)
    codes = {issue["code"] for issue in result["health"]["issues"]}

    assert result["revolt"]["status"] == "suppressed"
    assert result["province"]["revoltId"] is None
    assert any("suppressed because" in event for event in result["eventTexts"])
    assert result["health"]["ok"] is False
    assert "unknown_revolt_province" in codes
    assert "unknown_revolt_target" in codes
    assert "invalid_revolt_status" in codes
    assert "negative_revolt_strength" in codes
    assert "invalid_revolt_progress" in codes

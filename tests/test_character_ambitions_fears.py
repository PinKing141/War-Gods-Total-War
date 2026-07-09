"""Phase 7-B ambition and fear behavior tests."""

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


def test_ambition_and_fear_bias_war_decisions_and_intent_text():
    script = r"""
const fs = require('fs');
const vm = require('vm');
global.window = global;
global.WG = {};
for (const file of ['docs/assets/data.js', 'docs/assets/rng.js', 'docs/assets/sim.js']) {
  vm.runInThisContext(fs.readFileSync(file, 'utf8'), { filename: file });
}
const sim = new WG.Simulation(WG_SEED, 9301);
const ruler = sim.rulerOf('FAC_ROV_HALEN');
const claim = sim.claims.find((c) => c.id === 'CLAIM_ROV_OPEN_GATE');

ruler.ambition = 'restore old claims';
ruler.fear = 'dying forgotten';
const aggressive = sim._rulerWarDriveMultiplier('FAC_ROV_HALEN', 'FAC_GHARU_OPEN_GATE', claim, false);
const aggressiveReason = sim._warIntentReason('FAC_ROV_HALEN', 'FAC_GHARU_OPEN_GATE', claim, false, null, 0.1);

ruler.ambition = 'keep peace';
ruler.fear = 'open revolt';
sim.factionState.FAC_ROV_HALEN.internal.revoltRisk = 70;
const cautious = sim._rulerWarDriveMultiplier('FAC_ROV_HALEN', 'FAC_GHARU_OPEN_GATE', claim, false);
const cautiousProfile = sim.characterDriveProfile(ruler, {
  claim,
  revoltRiskHigh: true,
  faithConflict: true,
});

fs.writeFileSync(process.argv[2], JSON.stringify({
  aggressive,
  cautious,
  aggressiveReason,
  cautiousSummary: cautiousProfile.summary,
}));
"""
    result = _run_node(script)

    assert result["aggressive"] > 1
    assert result["cautious"] < 1
    assert "ambition (restore old claims)" in result["aggressiveReason"]
    assert "fear (dying forgotten)" in result["aggressiveReason"]
    assert "old claims" in result["aggressiveReason"]
    assert "peacekeeping" in result["cautiousSummary"]


def test_invalid_ambition_and_fear_values_are_validation_errors():
    script = r"""
const fs = require('fs');
const vm = require('vm');
global.window = global;
global.WG = {};
for (const file of ['docs/assets/data.js', 'docs/assets/rng.js', 'docs/assets/sim.js']) {
  vm.runInThisContext(fs.readFileSync(file, 'utf8'), { filename: file });
}
const sim = new WG.Simulation(WG_SEED, 9302);
sim.characters[0].ambition = 'collect every moon';
sim.characters[0].fear = 'rain on parade day';
fs.writeFileSync(process.argv[2], JSON.stringify(sim.validateState()));
"""
    health = _run_node(script)
    codes = {issue["code"] for issue in health["issues"]}

    assert health["ok"] is False
    assert "invalid_character_ambition" in codes
    assert "invalid_character_fear" in codes

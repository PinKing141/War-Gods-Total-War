"""Phase 7-A character schema expansion tests."""

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


def test_characters_have_expanded_identity_state_and_generated_characters_match():
    script = r"""
const fs = require('fs');
const vm = require('vm');
global.window = global;
global.WG = {};
for (const file of ['docs/assets/data.js', 'docs/assets/rng.js', 'docs/assets/sim.js']) {
  vm.runInThisContext(fs.readFileSync(file, 'utf8'), { filename: file });
}
const sim = new WG.Simulation(WG_SEED, 9201);
const seeded = sim.characters[0];
const generated = sim._spawnCharacter('FAC_ROV_HALEN', 'court envoy');
const ruler = sim.rulerOf('FAC_ROV_HALEN');
sim._kill(generated, 'dies in a roadside fever');
fs.writeFileSync(process.argv[2], JSON.stringify({
  seeded,
  generated,
  ruler,
  health: sim.validateState(),
}));
"""
    result = _run_node(script)

    for character in [result["seeded"], result["generated"], result["ruler"]]:
        assert isinstance(character["birthYear"], (int, float))
        assert character["faith"]
        assert character["ambition"]
        assert character["fear"]
        assert character["loyalties"]["faction"]
        assert 0 <= character["stress"] <= 100
        assert 0 <= character["health"] <= 100
        assert character["wealth"] >= 0
        assert 0 <= character["legitimacy"] <= 100
        assert 0 <= character["reputation"] <= 100

    assert result["generated"]["alive"] is False
    assert isinstance(result["generated"]["deathYear"], (int, float))
    assert result["generated"]["health"] == 0
    assert result["health"]["ok"] is True


def test_character_validation_reports_broken_expanded_state():
    script = r"""
const fs = require('fs');
const vm = require('vm');
global.window = global;
global.WG = {};
for (const file of ['docs/assets/data.js', 'docs/assets/rng.js', 'docs/assets/sim.js']) {
  vm.runInThisContext(fs.readFileSync(file, 'utf8'), { filename: file });
}
const sim = new WG.Simulation(WG_SEED, 9202);
Object.assign(sim.characters[0], {
  faith: 'REL_MISSING',
  birthYear: 'bad',
  deathYear: 'bad',
  ambition: '',
  fear: '',
  loyalties: {},
  stress: 101,
  health: -1,
  wealth: -1,
  legitimacy: 101,
  reputation: 101,
});
fs.writeFileSync(process.argv[2], JSON.stringify(sim.validateState()));
"""
    health = _run_node(script)
    codes = {issue["code"] for issue in health["issues"]}

    assert health["ok"] is False
    assert "unknown_character_faith" in codes
    assert "missing_character_birth_year" in codes
    assert "invalid_character_death_year" in codes
    assert "missing_character_ambition" in codes
    assert "missing_character_fear" in codes
    assert "missing_character_loyalties" in codes
    assert "negative_character_state_number" in codes
    assert "character_state_out_of_range" in codes

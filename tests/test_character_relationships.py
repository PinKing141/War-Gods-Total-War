"""Phase 7-C character relationship system tests."""

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


def test_relationships_seed_from_diplomacy_and_affect_succession_and_diplomacy():
    script = r"""
const fs = require('fs');
const vm = require('vm');
global.window = global;
global.WG = {};
for (const file of ['docs/assets/data.js', 'docs/assets/rng.js', 'docs/assets/sim.js']) {
  vm.runInThisContext(fs.readFileSync(file, 'utf8'), { filename: file });
}
const sim = new WG.Simulation(WG_SEED, 9401);
const rov = sim.rulerOf('FAC_ROV_HALEN');
const openGate = sim.rulerOf('FAC_GHARU_OPEN_GATE');
const seededEnemy = sim.relationshipBetween(rov.id, openGate.id, 'enemy');

const heir = sim._hydrateCharacter({
  id: 'CHAR_TEST_HEIR',
  name: 'Test Heir',
  species: rov.species,
  culture: rov.culture,
  faction: rov.faction,
  role: 'heir',
  age: 19,
  pressure: 'must inherit cleanly',
  parentId: rov.id,
}, { isRuler: false });
sim.characters.push(heir);
const beforeBond = sim.heirLegitimacy('FAC_ROV_HALEN', heir);
sim._addRelationship(rov.id, heir.id, 'parent', 95, 'test parent bond');
const afterBond = sim.heirLegitimacy('FAC_ROV_HALEN', heir);

const oldBias = sim._relationshipDiplomacyBias('FAC_ROV_HALEN', 'FAC_KAERN_RED_BOG');
const kaern = sim.rulerOf('FAC_KAERN_RED_BOG');
sim._addRelationship(rov.id, kaern.id, 'friend', 80, 'test friendship');
const friendBias = sim._relationshipDiplomacyBias('FAC_ROV_HALEN', 'FAC_KAERN_RED_BOG');

fs.writeFileSync(process.argv[2], JSON.stringify({
  relationshipCount: sim.relationships.length,
  seededEnemy,
  beforeBond,
  afterBond,
  oldBias,
  friendBias,
  health: sim.validateState(),
}));
"""
    result = _run_node(script)

    assert result["relationshipCount"] > 0
    assert result["seededEnemy"]["type"] == "enemy"
    assert result["afterBond"] > result["beforeBond"]
    assert result["friendBias"] > result["oldBias"]
    assert result["health"]["ok"] is True


def test_relationship_validation_reports_broken_relationships_and_ui_has_section():
    script = r"""
const fs = require('fs');
const vm = require('vm');
global.window = global;
global.WG = {};
for (const file of ['docs/assets/data.js', 'docs/assets/rng.js', 'docs/assets/sim.js']) {
  vm.runInThisContext(fs.readFileSync(file, 'utf8'), { filename: file });
}
const sim = new WG.Simulation(WG_SEED, 9402);
sim.relationships.push({
  id: 'REL_BROKEN',
  from: 'CHAR_MISSING',
  to: sim.characters[0].id,
  type: 'false_friend',
  strength: 140,
  source: 'test',
});
sim.relationships.push({
  id: 'REL_ONE_WAY',
  from: sim.characters[0].id,
  to: sim.characters[1].id,
  type: 'friend',
  strength: 50,
  source: 'test',
});
const uiSource = fs.readdirSync('docs/assets/ui').sort().map((f) => fs.readFileSync('docs/assets/ui/' + f, 'utf8')).join('\n');
fs.writeFileSync(process.argv[2], JSON.stringify({
  health: sim.validateState(),
  inspectorMentionsRelationships: uiSource.includes('Bonds & Grudges') && uiSource.includes('relationshipsOf'),
}));
"""
    result = _run_node(script)
    codes = {issue["code"] for issue in result["health"]["issues"]}

    assert result["health"]["ok"] is False
    assert "unknown_relationship_from" in codes
    assert "invalid_relationship_type" in codes
    assert "invalid_relationship_strength" in codes
    assert "missing_reciprocal_relationship" in codes
    assert result["inspectorMentionsRelationships"] is True

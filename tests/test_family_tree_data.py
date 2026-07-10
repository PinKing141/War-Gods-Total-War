"""Phase 8-A family tree data tests."""

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


def test_family_tree_fields_are_normalized_and_drive_heir_order():
    script = r"""
const fs = require('fs');
const vm = require('vm');
global.window = global;
global.WG = {};
for (const file of ['docs/assets/data.js', 'docs/assets/rng.js', 'docs/assets/sim.js']) {
  vm.runInThisContext(fs.readFileSync(file, 'utf8'), { filename: file });
}
const sim = new WG.Simulation(WG_SEED, 9601);
const ruler = sim.rulerOf('FAC_ROV_HALEN');
const older = sim._hydrateCharacter({
  id: 'CHAR_FAMILY_OLDER',
  name: 'Older Sevrin',
  species: ruler.species,
  culture: ruler.culture,
  faction: ruler.faction,
  role: 'elder child',
  age: 25,
  pressure: 'must wait',
  parentId: ruler.id,
  family: { father: ruler.id, dynasty: ruler.family.dynasty, house: ruler.family.house, inheritanceRank: 2, claimStrength: 45, legitimacy: 65 },
}, { isRuler: false });
const younger = sim._hydrateCharacter({
  id: 'CHAR_FAMILY_YOUNGER',
  name: 'Younger Sevrin',
  species: ruler.species,
  culture: ruler.culture,
  faction: ruler.faction,
  role: 'preferred child',
  age: 18,
  pressure: 'must inherit',
  parentId: ruler.id,
  family: { father: ruler.id, dynasty: ruler.family.dynasty, house: ruler.family.house, inheritanceRank: 1, claimStrength: 70, legitimacy: 80 },
}, { isRuler: false });
sim.characters.push(older, younger);
sim._syncFamilyLinks();
const close = sim.closeFamilyOf(ruler.id);
const heir = sim.heirOf('FAC_ROV_HALEN');
const uiSource = fs.readdirSync('docs/assets/ui').sort().map((f) => fs.readFileSync('docs/assets/ui/' + f, 'utf8')).join('\n');
fs.writeFileSync(process.argv[2], JSON.stringify({
  rulerFamily: ruler.family,
  closeChildren: close.children.map((c) => c.id),
  olderSiblings: older.family.siblings,
  heirId: heir && heir.id,
  health: sim.validateState(),
  inspectorMentionsFamily: uiSource.includes('familyPortraitRow("Siblings"') && uiSource.includes('Inheritance'),
}));
"""
    result = _run_node(script)

    assert result["rulerFamily"]["dynasty"]
    assert result["rulerFamily"]["house"]
    assert "CHAR_FAMILY_OLDER" in result["closeChildren"]
    assert "CHAR_FAMILY_YOUNGER" in result["closeChildren"]
    assert "CHAR_FAMILY_YOUNGER" in result["olderSiblings"]
    assert result["heirId"] == "CHAR_FAMILY_YOUNGER"
    assert result["health"]["ok"] is True
    assert result["inspectorMentionsFamily"] is True


def test_family_validation_reports_broken_references_and_parent_loops():
    script = r"""
const fs = require('fs');
const vm = require('vm');
global.window = global;
global.WG = {};
for (const file of ['docs/assets/data.js', 'docs/assets/rng.js', 'docs/assets/sim.js']) {
  vm.runInThisContext(fs.readFileSync(file, 'utf8'), { filename: file });
}
const sim = new WG.Simulation(WG_SEED, 9602);
sim.characters[0].family = {
  father: sim.characters[0].id,
  mother: 'CHAR_MISSING',
  spouses: ['CHAR_MISSING'],
  lovers: 'bad',
  children: [sim.characters[0].id],
  siblings: ['CHAR_MISSING'],
  dynasty: '',
  house: '',
  legitimacy: 140,
  inheritanceRank: 0,
  claimStrength: 140,
};
sim.characters[1].family.father = sim.characters[2].id;
sim.characters[2].family.father = sim.characters[1].id;
fs.writeFileSync(process.argv[2], JSON.stringify(sim.validateState()));
"""
    health = _run_node(script)
    codes = {issue["code"] for issue in health["issues"]}

    assert health["ok"] is False
    assert "unknown_family_parent" in codes
    assert "self_family_parent" in codes
    assert "invalid_family_list" in codes
    assert "unknown_family_link" in codes
    assert "self_family_link" in codes
    assert "missing_family_dynasty" in codes
    assert "missing_family_house" in codes
    assert "invalid_family_legitimacy" in codes
    assert "invalid_inheritance_rank" in codes
    assert "invalid_family_claim_strength" in codes
    assert "family_parent_loop" in codes

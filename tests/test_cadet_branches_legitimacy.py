"""Phase 8-C cadet branches, bastards and legitimacy tests."""

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


def test_legitimised_bastard_can_found_valid_cadet_branch_and_gain_support():
    script = r"""
const fs = require('fs');
const vm = require('vm');
global.window = global;
global.WG = {};
for (const file of ['docs/assets/data.js', 'docs/assets/rng.js', 'docs/assets/sim.js']) {
  vm.runInThisContext(fs.readFileSync(file, 'utf8'), { filename: file });
}
const sim = new WG.Simulation(WG_SEED, 9801);
const fid = 'FAC_ROV_HALEN';
const ruler = sim.rulerOf(fid);
const bastard = sim._hydrateCharacter({
  id: 'CHAR_LEGIT_BASTARD',
  name: 'Tovan Sevrin',
  species: ruler.species,
  culture: ruler.culture,
  faction: fid,
  role: 'acknowledged bastard',
  age: 19,
  pressure: 'must turn blood into law',
  parentId: ruler.id,
  family: {
    father: ruler.id,
    dynasty: ruler.family.dynasty,
    house: ruler.family.house,
    inheritanceRank: 3,
    claimStrength: 24,
    legitimacy: 18,
    bastard: true,
  },
}, { isRuler: false });
sim.characters.push(bastard);
sim._syncFamilyLinks();
sim._refreshDynastyHouseRecords();
const supportBefore = sim.factionSupportForCharacter(bastard);
const branch = sim.legitimizeBastard(bastard.id, 'legitimised_bastard');
const supportAfter = sim.factionSupportForCharacter(bastard);
const dynasty = sim.dynasty(bastard.family.dynastyId);
const house = sim.house(bastard.family.houseId);
const uiSource = fs.readFileSync('docs/assets/ui.js', 'utf8');
fs.writeFileSync(process.argv[2], JSON.stringify({
  branch,
  bastardFamily: bastard.family,
  supportBefore,
  supportAfter,
  dynastyBranches: dynasty.cadetBranches,
  house,
  health: sim.validateState(),
  uiMentionsBirthStatus: uiSource.includes('Birth status') && uiSource.includes('Cadet branch'),
}));
"""
    result = _run_node(script)

    assert result["branch"]["founder"] == "CHAR_LEGIT_BASTARD"
    assert result["bastardFamily"]["branchType"] == "cadet"
    assert result["bastardFamily"]["legitimised"] is True
    assert result["supportAfter"] > result["supportBefore"]
    assert result["dynastyBranches"]
    assert result["house"]["branchType"] == "cadet"
    assert result["health"]["ok"] is True
    assert result["uiMentionsBirthStatus"] is True


def test_legitimacy_changes_heir_order_claim_support_and_validation_reports_bad_state():
    script = r"""
const fs = require('fs');
const vm = require('vm');
global.window = global;
global.WG = {};
for (const file of ['docs/assets/data.js', 'docs/assets/rng.js', 'docs/assets/sim.js']) {
  vm.runInThisContext(fs.readFileSync(file, 'utf8'), { filename: file });
}
const sim = new WG.Simulation(WG_SEED, 9802);
const fid = 'FAC_GHARU_OPEN_GATE';
const ruler = sim.rulerOf(fid);
const low = sim._hydrateCharacter({
  id: 'CHAR_LOW_LEGIT_HEIR',
  name: 'Low Gate',
  species: ruler.species,
  culture: ruler.culture,
  faction: fid,
  role: 'first child',
  age: 28,
  pressure: 'must survive court doubt',
  parentId: ruler.id,
  family: { father: ruler.id, dynasty: ruler.family.dynasty, house: ruler.family.house, inheritanceRank: 1, claimStrength: 20, legitimacy: 8 },
  legitimacy: 10,
  prestige: 4,
}, { isRuler: false });
const high = sim._hydrateCharacter({
  id: 'CHAR_HIGH_LEGIT_HEIR',
  name: 'High Gate',
  species: ruler.species,
  culture: ruler.culture,
  faction: fid,
  role: 'second child',
  age: 23,
  pressure: 'must answer the council',
  parentId: ruler.id,
  family: { father: ruler.id, dynasty: ruler.family.dynasty, house: ruler.family.house, inheritanceRank: 2, claimStrength: 82, legitimacy: 94 },
  legitimacy: 92,
  prestige: 60,
}, { isRuler: false });
sim.characters.push(low, high);
sim._syncFamilyLinks();
sim._refreshDynastyHouseRecords();
const heir = sim.heirOf(fid);
const supportLow = sim.factionSupportForCharacter(low);
const supportHigh = sim.factionSupportForCharacter(high);

low.family.branchType = 'bad_branch';
low.family.bastard = 'yes';
low.family.legitimised = true;
low.family.branchFounder = 'CHAR_MISSING';
low.family.parentHouseId = 'HOUSE_MISSING';
fs.writeFileSync(process.argv[2], JSON.stringify({
  heirId: heir && heir.id,
  supportLow,
  supportHigh,
  health: sim.validateState(),
}));
"""
    result = _run_node(script)
    codes = {issue["code"] for issue in result["health"]["issues"]}

    assert result["heirId"] == "CHAR_HIGH_LEGIT_HEIR"
    assert result["supportHigh"] > result["supportLow"]
    assert result["health"]["ok"] is False
    assert "invalid_family_branch_type" in codes
    assert "invalid_family_bastard" in codes
    assert "unknown_family_branch_founder" in codes
    assert "unknown_family_parent_house" in codes

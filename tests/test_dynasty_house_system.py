"""Phase 8-B dynasty and house system tests."""

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


def test_dynasty_and_house_records_exist_and_house_head_updates_after_succession():
    script = r"""
const fs = require('fs');
const vm = require('vm');
global.window = global;
global.WG = {};
for (const file of ['docs/assets/data.js', 'docs/assets/rng.js', 'docs/assets/sim.js']) {
  vm.runInThisContext(fs.readFileSync(file, 'utf8'), { filename: file });
}
const sim = new WG.Simulation(WG_SEED, 9701);
const fid = 'FAC_ROV_HALEN';
const ruler = sim.rulerOf(fid);
const heir = sim._hydrateCharacter({
  id: 'CHAR_DYNASTY_HEIR',
  name: 'Dynasty Heir Sevrin',
  species: ruler.species,
  culture: ruler.culture,
  faction: fid,
  role: 'heir',
  age: 24,
  pressure: 'must inherit the house',
  parentId: ruler.id,
  family: {
    father: ruler.id,
    dynasty: ruler.family.dynasty,
    house: ruler.family.house,
    inheritanceRank: 1,
    claimStrength: 75,
    legitimacy: 80,
  },
}, { isRuler: false });
sim.characters.push(heir);
sim._syncFamilyLinks();
sim._refreshDynastyHouseRecords();
const before = sim.dynastySummaryForFaction(fid);
sim.factionState[fid].internal.successionPressure = 5;
sim.factionState[fid].internal.successionTension = 5;
sim._kill(ruler, 'dies in a dynasty test');
const after = sim.dynastySummaryForFaction(fid);
const uiSource = fs.readdirSync('docs/assets/ui').sort().map((f) => fs.readFileSync('docs/assets/ui/' + f, 'utf8')).join('\n');
fs.writeFileSync(process.argv[2], JSON.stringify({
  dynastyCount: sim.dynasties.length,
  houseCount: sim.houses.length,
  beforeHead: before.house.head,
  afterHead: after.house.head,
  heirId: heir.id,
  founder: after.founder && after.founder.id,
  members: after.members.map((c) => c.id),
  claimsVisible: Array.isArray(after.claims),
  rivalsVisible: Array.isArray(after.rivals),
  health: sim.validateState(),
  uiMentionsDynasty: uiSource.includes('<h3>Dynasty & House</h3>') && uiSource.includes('House head'),
  uiHasCharacterSheet: uiSource.includes('ck2-sheet') &&
    uiSource.includes('ck-portrait') &&
    uiSource.includes('ck-silhouette') &&
    uiSource.includes('characterTooltip') &&
    uiSource.includes('title="${esc(this.characterTooltip(c))}"'),
}));
"""
    result = _run_node(script)

    assert result["dynastyCount"] > 0
    assert result["houseCount"] > 0
    assert result["beforeHead"]
    assert result["afterHead"] == result["heirId"]
    assert result["founder"]
    assert result["heirId"] in result["members"]
    assert result["claimsVisible"] is True
    assert result["rivalsVisible"] is True
    assert result["health"]["ok"] is True
    assert result["uiMentionsDynasty"] is True
    assert result["uiHasCharacterSheet"] is True


def test_dynasty_and_house_validation_reports_broken_records():
    script = r"""
const fs = require('fs');
const vm = require('vm');
global.window = global;
global.WG = {};
for (const file of ['docs/assets/data.js', 'docs/assets/rng.js', 'docs/assets/sim.js']) {
  vm.runInThisContext(fs.readFileSync(file, 'utf8'), { filename: file });
}
const sim = new WG.Simulation(WG_SEED, 9702);
sim.characters[0].family.dynastyId = 'DYN_MISSING';
sim.characters[0].family.houseId = 'HOUSE_MISSING';
sim.dynasties.push({
  id: 'DYN_BROKEN',
  name: '',
  founder: 'CHAR_MISSING',
  head: 'CHAR_MISSING',
  homeProvince: 'PROV_MISSING',
  prestige: -1,
  renown: -1,
  famousAncestors: [],
  rivals: ['DYN_MISSING'],
  alliances: ['DYN_MISSING'],
  bloodlineTraits: [],
  cadetBranches: [],
  houses: ['HOUSE_MISSING'],
  members: ['CHAR_MISSING'],
});
sim.houses.push({
  id: 'HOUSE_BROKEN',
  dynasty: 'DYN_MISSING',
  name: '',
  founder: 'CHAR_MISSING',
  head: sim.characters[0].id,
  homeProvince: 'PROV_MISSING',
  legitimacy: 150,
  prestige: -1,
  livingMembers: [],
  members: [],
});
fs.writeFileSync(process.argv[2], JSON.stringify(sim.validateState()));
"""
    health = _run_node(script)
    codes = {issue["code"] for issue in health["issues"]}

    assert health["ok"] is False
    assert "unknown_character_dynasty" in codes
    assert "unknown_character_house" in codes
    assert "missing_dynasty_name" in codes
    assert "unknown_dynasty_founder" in codes
    assert "unknown_dynasty_head" in codes
    assert "unknown_dynasty_home_province" in codes
    assert "unknown_dynasty_member" in codes
    assert "unknown_dynasty_house" in codes
    assert "unknown_dynasty_rival" in codes
    assert "unknown_dynasty_alliance" in codes
    assert "negative_dynasty_number" in codes
    assert "missing_house_name" in codes
    assert "unknown_house_dynasty" in codes
    assert "unknown_house_founder" in codes
    assert "unknown_house_home_province" in codes
    assert "house_head_not_member" in codes
    assert "invalid_house_legitimacy" in codes
    assert "negative_house_prestige" in codes

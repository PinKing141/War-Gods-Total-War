"""Character attribute system tests: the five base attributes
(diplomacy, martial, stewardship, intrigue, learning), their live
modifiers, and the sim effects they drive."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

ATTRIBUTE_KEYS = ["diplomacy", "martial", "stewardship", "intrigue", "learning"]


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


def test_every_character_has_attributes_in_range_and_ui_reads_them():
    script = r"""
const fs = require('fs');
const vm = require('vm');
global.window = global;
global.WG = {};
for (const file of ['docs/assets/data.js', 'docs/assets/rng.js', 'docs/assets/sim.js']) {
  vm.runInThisContext(fs.readFileSync(file, 'utf8'), { filename: file });
}
const sim = new WG.Simulation(WG_SEED, 4242);
sim.adjacency = Object.fromEntries(WG_SEED.provinces.map((p) => [p.id, []]));
for (let i = 0; i < 3 * 360; i++) sim.tick();
const keys = ['diplomacy', 'martial', 'stewardship', 'intrigue', 'learning'];
const badBase = [];
for (const c of sim.characters) {
  if (!c.attributes) { badBase.push(c.id + ':missing'); continue; }
  for (const key of keys) {
    const v = c.attributes[key];
    if (typeof v !== 'number' || v < 0 || v > 20) badBase.push(`${c.id}.${key}=${v}`);
  }
}
const ruler = sim.characters.find((c) => c.isRuler && c.alive);
const view = sim.attributesOf(ruler.id);
const one = sim.attribute(ruler.id, 'martial');
const uiSource = fs.readdirSync('docs/assets/ui').sort().map((f) => fs.readFileSync('docs/assets/ui/' + f, 'utf8')).join('\n');
fs.writeFileSync(process.argv[2], JSON.stringify({
  characters: sim.characters.length,
  badBase,
  viewKeys: Object.keys(view),
  viewShape: keys.every((k) => view[k] && typeof view[k].base === 'number' &&
    typeof view[k].total === 'number' && Array.isArray(view[k].modifiers)),
  totalInRange: one.total >= 0 && one.total <= 24,
  missingIsNull: sim.attributesOf('CHAR_DOES_NOT_EXIST') === null,
  health: sim.validateState(),
  uiReadsAttributes: uiSource.includes('this.sim.attributesOf') &&
    !uiSource.includes('(placeholder)'),
}));
"""
    result = _run_node(script)

    assert result["characters"] > 0
    assert result["badBase"] == []
    assert sorted(result["viewKeys"]) == sorted(ATTRIBUTE_KEYS)
    assert result["viewShape"] is True
    assert result["totalInRange"] is True
    assert result["missingIsNull"] is True
    assert result["health"]["ok"] is True
    assert result["uiReadsAttributes"] is True


def test_traits_age_and_rule_modify_totals_deterministically():
    script = r"""
const fs = require('fs');
const vm = require('vm');
global.window = global;
global.WG = {};
for (const file of ['docs/assets/data.js', 'docs/assets/rng.js', 'docs/assets/sim.js']) {
  vm.runInThisContext(fs.readFileSync(file, 'utf8'), { filename: file });
}
const sim = new WG.Simulation(WG_SEED, 777);
const c = sim.characters.find((x) => x.alive);
c.traits = [{ id: 'ironhanded', label: 'Iron-Handed' }, { id: 'cunning', label: 'Cunning' }];
c.attributes = { diplomacy: 10, martial: 10, stewardship: 10, intrigue: 10, learning: 10 };
c.age = 30; c.stress = 10; c.health = 90; c.isRuler = false;
const adult = sim.attributesOf(c);
c.age = 6;
const child = sim.attribute(c, 'martial');
c.age = 30; c.stress = 80;
const stressed = sim.attribute(c, 'learning');
c.stress = 10; c.isRuler = true; c.reignStart = sim.date.year - 20;
const veteranRuler = sim.attribute(c, 'stewardship');
const again = sim.attributesOf(c);
const sameTwice = JSON.stringify(sim.attributesOf(c)) === JSON.stringify(again);
fs.writeFileSync(process.argv[2], JSON.stringify({
  martialWithTrait: adult.martial.total,
  diplomacyWithTrait: adult.diplomacy.total,
  intrigueWithTrait: adult.intrigue.total,
  martialLabels: adult.martial.modifiers.map((m) => m.label),
  childMartial: child.total,
  stressedLearning: stressed.total,
  veteranStewardship: veteranRuler.total,
  veteranLabels: veteranRuler.modifiers.map((m) => m.label),
  sameTwice,
}));
"""
    result = _run_node(script)

    assert result["martialWithTrait"] == 12          # Iron-Handed +2
    assert result["diplomacyWithTrait"] == 8         # Iron-Handed -2
    assert result["intrigueWithTrait"] == 12         # Cunning +2
    assert "Iron-Handed" in result["martialLabels"]
    assert result["childMartial"] < 12               # youth penalty applies
    assert result["stressedLearning"] < 11           # stress drags totals
    assert result["veteranStewardship"] >= 13        # +2 trait-free base... experience + throne years
    assert "Years on the throne" in result["veteranLabels"]
    assert result["sameTwice"] is True


def test_attributes_drive_offices_income_battle_and_inheritance():
    script = r"""
const fs = require('fs');
const vm = require('vm');
global.window = global;
global.WG = {};
for (const file of ['docs/assets/data.js', 'docs/assets/rng.js', 'docs/assets/sim.js']) {
  vm.runInThisContext(fs.readFileSync(file, 'utf8'), { filename: file });
}
const sim = new WG.Simulation(WG_SEED, 31337);
const fid = sim.seed.factions[0].id;
const ruler = sim.rulerOf(fid);

// offices prefer the skilled: give one courtier towering martial
const courtiers = sim.characters.filter((c) => c.faction === fid && c.alive && !c.isRuler);
while (courtiers.length < 2) {
  courtiers.push(sim._spawnCharacter(fid, 'landless sword'));
}
for (const c of courtiers) {
  c.attributes = { diplomacy: 5, martial: 5, stewardship: 5, intrigue: 5, learning: 5 };
  c.prestige = 20; c.reputation = 40; c.legitimacy = 40; c.age = 30;
  c.traits = [{ id: 'patient', label: 'Patient' }];
}
/* a pure soldier: towering martial, hopeless at everything else, so the
   chancellor/steward chairs go to others and the marshal pick is clean */
courtiers[0].attributes = { diplomacy: 0, martial: 19, stewardship: 0, intrigue: 0, learning: 0 };
sim._refreshCourt(fid);
const marshal = sim.courtOf(fid).offices.marshal;

// income responds to the ruler's stewardship
ruler.attributes.stewardship = 0;
const poor = sim.monthlyIncome(fid);
ruler.attributes.stewardship = 20;
const sharp = sim.monthlyIncome(fid);

// battle commanders swing harder with martial
const was = ruler.attributes.martial;
ruler.attributes.martial = 0;
const weak = sim.attributeTotal(ruler, 'martial');
ruler.attributes.martial = 20;
const strong = sim.attributeTotal(ruler, 'martial');
ruler.attributes.martial = was;

// children inherit a lean toward their parents' gifts
ruler.attributes = { diplomacy: 20, martial: 20, stewardship: 20, intrigue: 20, learning: 20 };
const kids = [];
for (let i = 0; i < 12; i++) {
  kids.push(sim._hydrateCharacter({
    id: 'CHAR_ATTR_KID_' + i, name: 'Test Kid', species: ruler.species,
    culture: ruler.culture, faction: fid, role: 'scion of the ruling line',
    age: 0, pressure: 'test', prestige: 0, kills: 0, parentId: ruler.id,
    family: { father: ruler.id },
  }, { isRuler: false }));
}
const kidAvg = kids.reduce((s, k) => s + Object.values(k.attributes).reduce((a, b) => a + b, 0) / 5, 0) / kids.length;

// validation flags a broken attribute
sim.characters[0].attributes.martial = 99;
const broken = sim.validateState();
sim.characters[0].attributes.martial = 9;
fs.writeFileSync(process.argv[2], JSON.stringify({
  marshalIsSkilled: marshal && marshal.character === courtiers[0].id,
  marshalEffectiveness: marshal ? marshal.effectiveness : 0,
  poor, sharp,
  weak, strong,
  kidAvg,
  brokenCodes: broken.issues.map((i) => i.code),
}));
"""
    result = _run_node(script)

    assert result["marshalIsSkilled"] is True
    assert result["marshalEffectiveness"] > 0
    assert result["sharp"] > result["poor"]          # stewardship pays
    assert result["weak"] < result["strong"]         # martial totals move
    assert result["kidAvg"] > 8                      # gifted parents lift children
    assert "invalid_character_attribute" in result["brokenCodes"]

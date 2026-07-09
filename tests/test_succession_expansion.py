"""Phase 6-D succession and ruler-death expansion tests."""

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


def test_ruler_death_can_create_stable_succession_and_regency():
    script = r"""
const fs = require('fs');
const vm = require('vm');
global.window = global;
global.WG = {};
for (const file of ['docs/assets/data.js', 'docs/assets/rng.js', 'docs/assets/sim.js']) {
  vm.runInThisContext(fs.readFileSync(file, 'utf8'), { filename: file });
}
const sim = new WG.Simulation(WG_SEED, 7101);
function addChild(fid, ruler, age, name) {
  const child = {
    id: name.replace(/\s+/g, '_').toUpperCase(),
    name,
    species: ruler.species,
    culture: ruler.culture,
    faction: fid,
    role: 'scion of the ruling line',
    age,
    pressure: 'must inherit cleanly',
    alive: true,
    isRuler: false,
    traits: sim._rollTraits(),
    prestige: age >= 16 ? 45 : 0,
    kills: 0,
    parentId: ruler.id,
  };
  sim.characters.push(child);
  return child;
}
const stableFid = 'FAC_ROV_HALEN';
const stableRuler = sim.rulerOf(stableFid);
const adultHeir = addChild(stableFid, stableRuler, 24, 'Stable Heir');
sim.factionState[stableFid].internal.successionPressure = 8;
sim.factionState[stableFid].internal.successionTension = 8;
sim._kill(stableRuler, 'dies in bed');

const regencyFid = 'FAC_GHARU_OPEN_GATE';
const regencyRuler = sim.rulerOf(regencyFid);
const childHeir = addChild(regencyFid, regencyRuler, 9, 'Child Heir');
sim.factionState[regencyFid].internal.successionPressure = 12;
sim.factionState[regencyFid].internal.successionTension = 12;
sim._kill(regencyRuler, 'dies after a fever');

fs.writeFileSync(process.argv[2], JSON.stringify({
  adultHeir: adultHeir.id,
  stableRulerId: sim.factionState[stableFid].rulerId,
  stableTransition: sim.factionState[stableFid].succession.lastTransition,
  childHeir: childHeir.id,
  regencyRulerId: sim.factionState[regencyFid].rulerId,
  regencyTransition: sim.factionState[regencyFid].succession.lastTransition,
  regency: sim.factionState[regencyFid].succession.regency,
  successionEvents: sim.events.filter((ev) => ev.type === 'succession').map((ev) => ev.text),
  health: sim.validateState(),
}));
"""
    result = _run_node(script)

    assert result["stableRulerId"] == result["adultHeir"]
    assert result["stableTransition"]["outcome"] == "stable"
    assert result["regencyRulerId"] == result["childHeir"]
    assert result["regencyTransition"]["outcome"] == "regency"
    assert result["regency"] is True
    assert any("accepted without open crisis" in event for event in result["successionEvents"])
    assert any("regency" in event.lower() for event in result["successionEvents"])
    assert result["health"]["ok"] is True


def test_ruler_death_can_create_succession_crisis_pretender_and_claim():
    script = r"""
const fs = require('fs');
const vm = require('vm');
global.window = global;
global.WG = {};
for (const file of ['docs/assets/data.js', 'docs/assets/rng.js', 'docs/assets/sim.js']) {
  vm.runInThisContext(fs.readFileSync(file, 'utf8'), { filename: file });
}
const sim = new WG.Simulation(WG_SEED, 7102);
const fid = 'FAC_MAREN_BLUE_CHAIN';
const ruler = sim.rulerOf(fid);
const child = {
  id: 'CRISIS_CHILD',
  name: 'Crisis Child',
  species: ruler.species,
  culture: ruler.culture,
  faction: fid,
  role: 'scion of the ruling line',
  age: 8,
  pressure: 'must survive the succession',
  alive: true,
  isRuler: false,
  traits: sim._rollTraits(),
  prestige: 0,
  kills: 0,
  parentId: ruler.id,
};
sim.characters.push(child);
Object.assign(sim.factionState[fid].internal, {
  successionPressure: 92,
  successionTension: 90,
  courtTension: 84,
  nobleLoyalty: 20,
});
sim._kill(ruler, 'dies suddenly');
const state = sim.factionState[fid];
fs.writeFileSync(process.argv[2], JSON.stringify({
  rulerId: state.rulerId,
  transition: state.succession.lastTransition,
  succession: state.succession,
  pretenderClaims: sim.claims.filter((c) => c.type === 'pretender claim' && c.claimant === fid),
  successionEvents: sim.events.filter((ev) => ev.type === 'succession').map((ev) => ev.text),
  revoltEvents: sim.events.filter((ev) => ev.type === 'revolt').map((ev) => ev.text),
  health: sim.validateState(),
}));
"""
    result = _run_node(script)

    assert result["rulerId"] == "CRISIS_CHILD"
    assert result["transition"]["outcome"] == "crisis"
    assert result["succession"]["crisis"]
    assert result["succession"]["pretenders"]
    assert result["pretenderClaims"]
    assert any("Succession crisis follows" in event for event in result["successionEvents"])
    assert result["health"]["ok"] is True

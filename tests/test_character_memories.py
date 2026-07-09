"""Phase 7-D personal memories and military record tests."""

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


def test_battles_deaths_and_commands_create_memories_records_and_grudges():
    script = r"""
const fs = require('fs');
const vm = require('vm');
global.window = global;
global.WG = {};
for (const file of ['docs/assets/data.js', 'docs/assets/rng.js', 'docs/assets/sim.js']) {
  vm.runInThisContext(fs.readFileSync(file, 'utf8'), { filename: file });
}
const sim = new WG.Simulation(WG_SEED, 9501);
const war = {
  id: 'WAR_MEMORY_TEST',
  name: 'Memory Test War',
  attacker: 'FAC_ROV_HALEN',
  defender: 'FAC_GHARU_OPEN_GATE',
  goal: { type: 'conquest', province: 'PROV_OPEN_GATE' },
  score: 0,
  startDay: sim.day,
  startDate: sim.formatDate(),
  battles: [],
  over: false,
  atkSide: ['FAC_ROV_HALEN'],
  defSide: ['FAC_GHARU_OPEN_GATE'],
};
sim.wars.push(war);
const rov = sim.rulerOf('FAC_ROV_HALEN');
const gharu = sim.rulerOf('FAC_GHARU_OPEN_GATE');
sim._addRelationship(rov.id, gharu.id, 'rival', 50, 'test rivalry');

const A = {
  id: 'ARMY_A',
  faction: 'FAC_ROV_HALEN',
  size: 2500,
  morale: 100,
  quality: 2,
  commanderId: rov.id,
  loc: 'PROV_OPEN_GATE',
  warId: war.id,
};
const B = {
  id: 'ARMY_B',
  faction: 'FAC_GHARU_OPEN_GATE',
  size: 90,
  morale: 10,
  quality: 0.5,
  commanderId: gharu.id,
  loc: 'PROV_OPEN_GATE',
  warId: war.id,
};
sim._battleRound(A, B, war, 'PROV_OPEN_GATE');

const child = sim._hydrateCharacter({
  id: 'CHAR_MEMORY_CHILD',
  name: 'Memory Child',
  species: rov.species,
  culture: rov.culture,
  faction: rov.faction,
  role: 'child',
  age: 10,
  pressure: 'must remember the house',
  parentId: rov.id,
}, { isRuler: false });
sim.characters.push(child);
sim._addRelationship(rov.id, child.id, 'parent', 90, 'test family');
sim._kill(rov, 'dies in a memory test');

const uiSource = fs.readFileSync('docs/assets/ui.js', 'utf8');
fs.writeFileSync(process.argv[2], JSON.stringify({
  winnerMemories: gharu.memories.filter((m) => m.type === 'battle defeat').length,
  loserMemories: rov.memories.filter((m) => m.type === 'battle victory').length,
  childFamilyMemories: child.memories.filter((m) => m.type === 'family death').length,
  rovRecord: rov.militaryRecord,
  gharuRecord: gharu.militaryRecord,
  grudge: sim.relationshipBetween(gharu.id, rov.id, 'rival'),
  health: sim.validateState(),
  inspectorMentionsMemory: uiSource.includes('<h3>Memories</h3>') && uiSource.includes('Military record'),
}));
"""
    result = _run_node(script)

    assert result["loserMemories"] >= 1
    assert result["winnerMemories"] >= 1
    assert result["childFamilyMemories"] >= 1
    assert result["rovRecord"]["battlesWon"] >= 1
    assert result["gharuRecord"]["battlesLost"] >= 1
    assert result["grudge"]["strength"] >= 48
    assert result["health"]["ok"] is True
    assert result["inspectorMentionsMemory"] is True


def test_invalid_memories_and_military_records_are_validation_errors():
    script = r"""
const fs = require('fs');
const vm = require('vm');
global.window = global;
global.WG = {};
for (const file of ['docs/assets/data.js', 'docs/assets/rng.js', 'docs/assets/sim.js']) {
  vm.runInThisContext(fs.readFileSync(file, 'utf8'), { filename: file });
}
const sim = new WG.Simulation(WG_SEED, 9502);
const c = sim.characters[0];
c.memories = [{
  id: '',
  type: 'bad memory',
  text: '',
  day: -1,
  refs: { character: 'CHAR_MISSING', faction: 'FAC_MISSING', province: 'PROV_MISSING', war: 'WAR_MISSING' },
}];
c.militaryRecord = {
  battlesFought: 1,
  battlesWon: 2,
  battlesLost: 1,
  siegesLed: -1,
  wounds: -1,
  notableVictories: 'bad',
  notableDefeats: 'bad',
};
fs.writeFileSync(process.argv[2], JSON.stringify(sim.validateState()));
"""
    health = _run_node(script)
    codes = {issue["code"] for issue in health["issues"]}

    assert health["ok"] is False
    assert "missing_memory_id" in codes
    assert "invalid_memory_type" in codes
    assert "missing_memory_text" in codes
    assert "invalid_memory_day" in codes
    assert "unknown_memory_character" in codes
    assert "unknown_memory_faction" in codes
    assert "unknown_memory_province" in codes
    assert "unknown_memory_war" in codes
    assert "negative_military_record_number" in codes
    assert "invalid_military_record_totals" in codes
    assert "invalid_military_record_list" in codes

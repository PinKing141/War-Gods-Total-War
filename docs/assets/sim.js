/* The living world. Runs entirely in the browser — no player input exists.
   Day ticks drive armies and battles; monthly pulses drive economy, diplomacy
   and peace; yearly pulses drive aging, death and succession. */
(function () {
  "use strict";

  const DAYS_PER_MONTH = 30, MONTHS_PER_YEAR = 12;
  const MONTH_NAMES = ["Firstmark", "Thawmoon", "Seedtide", "Rainmoon", "Highsun",
    "Haytide", "Harvest", "Emberfall", "Frostmark", "Longnight", "Icemoon", "Yearsend"];

  const TRAIT_POOL = [
    { id: "bold", label: "Bold", war: 1.6, battle: 1.12 },
    { id: "cautious", label: "Cautious", war: 0.55, battle: 1.0, defense: 1.12 },
    { id: "greedy", label: "Greedy", war: 1.25, battle: 1.0 },
    { id: "vengeful", label: "Vengeful", war: 1.35, battle: 1.05 },
    { id: "just", label: "Just", war: 0.8, battle: 1.0 },
    { id: "cunning", label: "Cunning", war: 1.1, battle: 1.08 },
    { id: "pious", label: "Pious", war: 0.9, battle: 1.04 },
    { id: "ironhanded", label: "Iron-Handed", war: 1.2, battle: 1.06 },
    { id: "patient", label: "Patient", war: 0.7, battle: 1.02 },
  ];

  const PRESSURE_TEMPLATES = [
    "must hold what the last ruler bled for",
    "must prove the succession was lawful",
    "must feed the towns before the next frost",
    "must avenge the defeats of the previous reign",
    "must keep the old claims from being forgotten",
    "must pay the war debts without selling the roads",
    "must quiet the councils that doubt the new reign",
  ];

  let nextId = 1000;
  function uid(prefix) { return prefix + "_" + (nextId++); }

  class Simulation {
    constructor(seed, rngSeed) {
      this.seed = seed;
      this.rng = new WG.Rng(rngSeed || 20260704);
      this.forge = WG.makeNameForge(seed, this.rng);
      this.day = 0;
      this.date = { day: 1, month: 1, year: seed.world.startYear };
      this.listeners = [];
      this.events = [];
      this.monthlyRecaps = [];
      this.wars = [];
      this.armies = [];
      this.adjacency = null;   // provided by map after ownership raster
      this.fx = [];            // transient visual effects for the UI to drain
      this.totals = { fallen: 0, warsEnded: 0 };
      this._monthStartEventIndex = 0;
      this._monthStartFallen = 0;
      this._monthStartWarsEnded = 0;
      this.mapVersion = 0;     // bumped when the political map must repaint

      this.factionState = {};
      this.provinceState = {};
      this.characters = seed.characters.map((c) => ({
        ...c, alive: true, isRuler: true, traits: this._rollTraits(),
        prestige: this.rng.int(10, 60), kills: 0, reignStart: 1,
      }));
      this.opinions = {};

      for (const f of seed.factions) {
        const ruler = this.characters.find((c) => c.faction === f.id);
        this.factionState[f.id] = {
          treasury: this.rng.int(400, 900),
          manpower: 0, maxManpower: 0,
          prestige: this.rng.int(20, 80),
          exhaustion: 0,
          rulerId: ruler ? ruler.id : null,
          truces: {}, tribute: {},
          warsWon: 0, warsLost: 0,
        };
      }
      for (const p of seed.provinces) {
        const pop = 6000 + p.value * 220 + this.rng.int(-1500, 1500);
        this.provinceState[p.id] = {
          controller: p.controller, occupier: null,
          pop, devastation: 0, garrison: Math.round(200 + p.fort * 180),
          siege: null,
        };
      }
      for (const f of seed.factions) this._refreshManpower(f.id, true);
      for (const r of seed.relations) this._setOpinion(r.a, r.b, r.score);
      this.claims = seed.claims.map((c) => ({ ...c }));
      this.mages = seed.mages.map((m) => ({ ...m, alive: true }));
    }

    /* ------------------------------------------------ helpers */

    onEvent(fn) { this.listeners.push(fn); }

    log(importance, type, text, refs) {
      const ev = {
        day: this.day, importance, type, text, refs: refs || {},
        date: this.formatDate(),
      };
      this.events.push(ev);
      if (this.events.length > 900) this.events.splice(0, 200);
      for (const fn of this.listeners) fn(ev);
    }

    formatDate() {
      return `${this.date.day} ${MONTH_NAMES[this.date.month - 1]}, ${this.date.year} AE`;
    }

    faction(id) { return this.seed.factions.find((f) => f.id === id); }
    province(id) { return this.seed.provinces.find((p) => p.id === id); }
    character(id) { return this.characters.find((c) => c.id === id); }
    rulerOf(fid) { return this.character(this.factionState[fid].rulerId); }

    ownedProvinces(fid) {
      return this.seed.provinces.filter((p) => this.provinceState[p.id].controller === fid);
    }

    capital(fid) {
      const owned = this.ownedProvinces(fid);
      if (!owned.length) return null;
      return owned.reduce((a, b) => (a.value >= b.value ? a : b));
    }

    _oKey(a, b) { return a < b ? a + "|" + b : b + "|" + a; }
    opinion(a, b) { const v = this.opinions[this._oKey(a, b)]; return v === undefined ? 0 : v; }
    _setOpinion(a, b, v) { this.opinions[this._oKey(a, b)] = Math.max(-100, Math.min(100, v)); }
    _bumpOpinion(a, b, dv) { this._setOpinion(a, b, this.opinion(a, b) + dv); }

    warBetween(a, b) {
      return this.wars.find((w) => !w.over &&
        ((w.atkSide.includes(a) && w.defSide.includes(b)) ||
         (w.atkSide.includes(b) && w.defSide.includes(a))));
    }
    warsOf(fid) {
      return this.wars.filter((w) => !w.over &&
        (w.atkSide.includes(fid) || w.defSide.includes(fid)));
    }
    atWar(a, b) { return !!this.warBetween(a, b); }

    _rollTraits() {
      const picks = [];
      while (picks.length < 2) {
        const t = this.rng.pick(TRAIT_POOL);
        if (!picks.includes(t)) picks.push(t);
      }
      return picks;
    }

    _traitFactor(fid, key) {
      const ruler = this.rulerOf(fid);
      if (!ruler) return 1;
      let f = 1;
      for (const t of ruler.traits) if (t[key]) f *= t[key];
      return f;
    }

    _refreshManpower(fid, initial) {
      const s = this.factionState[fid];
      let max = 0;
      for (const p of this.ownedProvinces(fid)) {
        max += this.provinceState[p.id].pop * 0.10 * (1 - this.provinceState[p.id].devastation / 150);
      }
      s.maxManpower = Math.round(max);
      if (initial) s.manpower = s.maxManpower;
      else s.manpower = Math.max(0, Math.min(s.manpower, s.maxManpower));
    }

    monthlyIncome(fid) {
      let income = 0;
      for (const p of this.ownedProvinces(fid)) {
        const st = this.provinceState[p.id];
        if (st.occupier) continue;                      // occupied land pays nothing
        income += (st.pop / 90) * (1 + p.roads * 0.15) * (1 - st.devastation / 120);
        income += p.port * 14;
      }
      return Math.round(income);
    }

    monthlyUpkeep(fid) {
      let upkeep = 0;
      for (const a of this.armies) if (a.faction === fid) upkeep += a.size * 0.045;
      return Math.round(upkeep);
    }

    armyStrength(fid) {
      let total = 0;
      for (const a of this.armies) if (a.faction === fid) total += a.size;
      return total;
    }

    occupiedProvinces(fid) {
      return this.seed.provinces.filter((p) => this.provinceState[p.id].occupier === fid);
    }

    contestedProvinces(fid) {
      return this.seed.provinces.filter((p) => {
        const st = this.provinceState[p.id];
        return st.controller === fid && (st.occupier || st.siege);
      });
    }

    /* ------------------------------------------------ main tick */

    tick() {
      this.day += 1;
      this.date.day += 1;
      let newMonth = false, newYear = false;
      if (this.date.day > DAYS_PER_MONTH) {
        this.date.day = 1; this.date.month += 1; newMonth = true;
        if (this.date.month > MONTHS_PER_YEAR) {
          this.date.month = 1; this.date.year += 1; newYear = true;
        }
      }
      this._tickArmies();
      if (newMonth) this._monthlyPulse();
      if (newYear) this._yearlyPulse();
    }

    /* ------------------------------------------------ armies & war */

    _pathNext(fromId, toId) {
      if (fromId === toId) return null;
      const queue = [[fromId]];
      const seen = new Set([fromId]);
      while (queue.length) {
        const path = queue.shift();
        const last = path[path.length - 1];
        for (const n of (this.adjacency[last] || [])) {
          if (seen.has(n)) continue;
          if (n === toId) return path.length === 1 ? n : path[1];
          seen.add(n);
          queue.push([...path, n]);
        }
      }
      return null;
    }

    _terrainFlags(prov) {
      const terrainId = prov ? prov.terrain : "";
      const terr = this.seed.terrains[terrainId] || {};
      const text = `${terrainId} ${terr.label || ""}`.toLowerCase();
      return {
        mountain: /mountain|highland|pass|hill|mine|iron/.test(text),
        marsh: /marsh|bog|fen|wetland/.test(text),
        dryland: /dryland|steppe|salt|oasis|waste/.test(text),
      };
    }

    _movementDays(army, nextId) {
      const from = this.province(army.loc);
      const to = this.province(nextId);
      const terr = this.seed.terrains[to && to.terrain] || {};
      const flags = this._terrainFlags(to);
      let days = terr.moveDays || 3;
      if (flags.mountain) days += 1.25;
      if (flags.marsh) days += 0.65;
      const roadLevel = ((from && from.roads) || 0) + ((to && to.roads) || 0);
      days -= Math.min(2.2, roadLevel * 0.24);
      const st = to && this.provinceState[to.id];
      if (st && st.controller !== army.faction && st.occupier !== army.faction) days += 1.1;
      return Math.max(1, Math.ceil(days));
    }

    _armyMaxSupply(size, province) {
      const roadBonus = province ? province.roads * 2 + province.port * 4 : 0;
      return Math.max(18, Math.round(size / 85 + 28 + roadBonus));
    }

    _supplyUseFor(army, province, posture) {
      const flags = this._terrainFlags(province);
      let cost = Math.max(1, army.size / 1250);
      if (posture === "march") cost += 0.65;
      if (posture === "siege") cost += 1.2 + ((province && province.fort) || 0) * 0.18;
      if (flags.marsh) cost *= 1.35;
      if (flags.dryland) cost *= 1.22;
      if (flags.mountain) cost *= 1.18;
      const st = province && this.provinceState[province.id];
      if (st && st.controller !== army.faction && st.occupier !== army.faction) cost *= 1.25;
      if (province && province.roads) cost *= Math.max(0.78, 1 - province.roads * 0.035);
      return Math.max(0.5, cost);
    }

    _resupplyArmy(army, province) {
      if (!province) return;
      const st = this.provinceState[province.id];
      if (!st || st.controller !== army.faction || st.occupier) return;
      const gain = 1.8 + province.roads * 0.45 + province.port * 0.8;
      army.supply = Math.min(army.maxSupply, army.supply + gain);
      if (army.supply > army.dailySupplyUse * 2) army.undersupplied = false;
    }

    _consumeArmySupply(army, war, posture) {
      const province = this.province(army.loc);
      army.maxSupply = this._armyMaxSupply(army.size, province);
      if (army.supply === undefined) army.supply = army.maxSupply;
      army.supply = Math.min(army.maxSupply, army.supply);
      this._resupplyArmy(army, province);
      const cost = this._supplyUseFor(army, province, posture);
      army.dailySupplyUse = Math.round(cost * 10) / 10;
      army.supply = Math.max(0, army.supply - cost);
      army.undersupplied = army.supply <= 0.1;
      if (!army.undersupplied) return;

      const loss = Math.max(3, Math.round(army.size * (posture === "siege" ? 0.006 : 0.0035)));
      army.size = Math.max(0, army.size - loss);
      army.morale = Math.max(8, army.morale - 2.5);
      this.factionState[army.faction].exhaustion += posture === "siege" ? 0.5 : 0.25;
      if (!army.lastSupplyEventDay || this.day - army.lastSupplyEventDay >= 18) {
        army.lastSupplyEventDay = this.day;
        const commander = this.character(army.commanderId);
        this.log(2, "muster",
          `${this.faction(army.faction).name} suffers supply failure at ${province.name}: ${loss.toLocaleString()} leave the ranks${commander ? " under " + commander.name : ""}.`,
          { faction: army.faction, province: army.loc, war: war && war.id, character: army.commanderId });
      }
    }

    _armyIntent(army, war) {
      const onAtkSide = war.atkSide.includes(army.faction);
      const mySide = onAtkSide ? war.atkSide : war.defSide;
      const enemySide = onAtkSide ? war.defSide : war.atkSide;
      const mainEnemy = onAtkSide ? war.defender : war.attacker;
      const invaders = this.armies.filter((a) =>
        enemySide.includes(a.faction) && this.provinceState[a.loc] &&
        mySide.includes(this.provinceState[a.loc].controller));
      if (invaders.length) {
        const target = invaders.reduce((x, y) => (x.size > y.size ? x : y));
        return { targetId: target.loc, reason: `intercepting ${this.faction(target.faction).shortName || this.faction(target.faction).name} army on friendly land` };
      }
      if (onAtkSide && war.goal.province &&
          this.provinceState[war.goal.province].controller === war.defender &&
          this.provinceState[war.goal.province].occupier !== army.faction) {
        return { targetId: war.goal.province, reason: `pressing the war goal at ${this.province(war.goal.province).name}` };
      }
      const enemyProvinces = [mainEnemy, ...enemySide]
        .flatMap((fid) => this.ownedProvinces(fid))
        .filter((p) => this.provinceState[p.id].occupier !== army.faction);
      if (enemyProvinces.length) {
        return { targetId: enemyProvinces[0].id, reason: `seeking pressure on ${this.faction(mainEnemy).shortName || this.faction(mainEnemy).name} holdings` };
      }
      const cap = this.capital(army.faction);
      return { targetId: cap ? cap.id : army.loc, reason: "holding the capital because no better war target remains" };
    }

    _raiseArmy(fid, war) {
      const cap = this.capital(fid);
      if (!cap) return;
      const s = this.factionState[fid];
      if (s.manpower < 120) return;
      const size = Math.max(120, Math.round(s.manpower * 0.65));
      s.manpower = Math.max(0, s.manpower - Math.min(s.manpower, size));
      let commander = this.rulerOf(fid);
      if (!commander || this.rng.chance(0.55)) {
        commander = this._spawnCharacter(fid, "war captain");
      }
      const maxSupply = this._armyMaxSupply(size, cap);
      this.armies.push({
        id: uid("army"),
        faction: fid, size, morale: 100,
        quality: 0.9 + this.rng.float(0, 0.35),
        commanderId: commander.id,
        loc: cap.id, moveLeft: 0, dest: null,
        warId: war.id, retreatUntil: 0,
        supply: maxSupply, maxSupply,
        dailySupplyUse: 0, undersupplied: false,
        intentReason: `mustering for ${war.name}`,
      });
      this.log(2, "muster",
        `${this.faction(fid).name} musters ${size.toLocaleString()} under ${commander.name} at ${cap.name}.`,
        { faction: fid, province: cap.id, character: commander.id });
    }

    _spawnCharacter(fid, role) {
      const f = this.faction(fid);
      const species = this.seed.species[f.species] ? f.species :
        (f.species.includes("orc") ? "orc" : "human");
      const c = {
        id: uid("char"),
        name: this.forge.given(f.culture) + " " + this.forge.epithet(),
        species, culture: f.culture, faction: fid, role,
        age: this.rng.int(22, 45), pressure: this.rng.pick(PRESSURE_TEMPLATES),
        alive: true, isRuler: false, traits: this._rollTraits(),
        prestige: this.rng.int(0, 25), kills: 0,
      };
      this.characters.push(c);
      return c;
    }

    _armyTargets(army, war) {
      return this._armyIntent(army, war).targetId;
    }

    _tickArmies() {
      // battles first: hostile armies sharing a province
      const byLoc = {};
      for (const a of this.armies) (byLoc[a.loc] = byLoc[a.loc] || []).push(a);
      for (const [loc, group] of Object.entries(byLoc)) {
        if (group.length < 2) continue;
        for (let i = 0; i < group.length; i++) {
          for (let j = i + 1; j < group.length; j++) {
            const A = group[i], B = group[j];
            if (A.faction === B.faction) continue;
            const war = this.warBetween(A.faction, B.faction);
            if (war) { this._battleRound(A, B, war, loc); }
          }
        }
      }

      for (const army of [...this.armies]) {
        if (army.size <= 0) continue;
        const war = this.wars.find((w) => w.id === army.warId);
        if (!war || war.over) { this._disband(army); continue; }
        if (army.inBattle) { army.inBattle = false; continue; } // fought this tick
        if (this.day < army.retreatUntil) continue;

        const decision = this._armyIntent(army, war);
        const targetId = decision.targetId;
        if (army.intentTarget !== targetId || army.intentReason !== decision.reason) {
          army.intentTarget = targetId;
          army.intentReason = decision.reason;
          if (!army.lastIntentEventDay || this.day - army.lastIntentEventDay >= 20) {
            army.lastIntentEventDay = this.day;
            this.log(1, "muster",
              `${this.faction(army.faction).name} redirects ${this.character(army.commanderId)?.name || "an army"}: ${decision.reason}.`,
              { faction: army.faction, province: army.loc, war: war.id, character: army.commanderId });
          }
        }
        if (targetId && targetId !== army.loc) {
          this._consumeArmySupply(army, war, "march");
          if (!army.dest || army.dest !== targetId) {
            army.dest = targetId; army.moveLeft = 0;
          }
          if (army.moveLeft <= 0) {
            const next = this._pathNext(army.loc, army.dest);
            if (next) {
              army.moveLeft = this._movementDays(army, next);
              army.nextLoc = next;
            }
          }
          if (army.nextLoc) {
            army.moveLeft -= 1;
            if (army.moveLeft <= 0) {
              army.loc = army.nextLoc; army.nextLoc = null;
            }
          }
        } else {
          const sieging = this._siegeTick(army, war);
          if (!sieging) this._consumeArmySupply(army, war, "camp");
        }
        army.morale = Math.min(100, army.morale + 0.4);
      }
      this.armies = this.armies.filter((a) => a.size > 30);
    }

    _mageFactor(fid, provinceId, war) {
      // A living mage whose patron fights here can swing the day.
      const mage = this.mages.find((m) => m.alive && m.patron === fid);
      if (!mage || !this.rng.chance(0.16)) return 1;
      const host = this.character(mage.character);
      const power = 1 + mage.capacity / 400;
      this.log(2, "magic",
        `${host ? host.name : "A mage"} works ${mage.specialization} over ${this.province(provinceId).name}; the lines of battle bend.`,
        { faction: fid, province: provinceId, character: mage.character });
      if (this.rng.chance(mage.risk / 400)) {
        mage.alive = false;
        this.log(3, "magic",
          `The strain is too great — ${host ? host.name : "the mage"} of ${this.faction(fid).name} is consumed by their own working.`,
          { faction: fid, character: mage.character });
      }
      return power;
    }

    _battleRound(A, B, war, loc) {
      A.inBattle = B.inBattle = true;
      const prov = this.province(loc);
      const provSt = this.provinceState[loc];
      const terr = this.seed.terrains[prov.terrain];
      if (!war.activeBattle || war.activeBattle.loc !== loc) {
        war.activeBattle = { loc, start: this.day, aStart: A.size, bStart: B.size };
        this.log(2, "battle",
          `Battle is joined at ${prov.name}: ${A.size.toLocaleString()} of ${this.faction(A.faction).name} against ${B.size.toLocaleString()} of ${this.faction(B.faction).name}.`,
          { province: loc, war: war.id, faction: A.faction });
      }
      const defFacId = provSt.controller;
      const defBonus = (fid) => (fid === defFacId ? 1 + (terr ? terr.defense : 0) * 0.06 : 1);
      const cmdBonus = (army) => {
        const c = this.character(army.commanderId);
        if (!c) return 1;
        let f = 1;
        for (const t of c.traits) if (t.battle) f *= t.battle;
        return f;
      };
      const magicA = this._mageFactor(A.faction, loc, war);
      const magicB = this._mageFactor(B.faction, loc, war);

      const dmgToB = A.size * 0.030 * A.quality * cmdBonus(A) * defBonus(A.faction) * magicA * this.rng.float(0.7, 1.3);
      const dmgToA = B.size * 0.030 * B.quality * cmdBonus(B) * defBonus(B.faction) * magicB * this.rng.float(0.7, 1.3);
      A.size = Math.max(0, Math.round(A.size - dmgToA));
      B.size = Math.max(0, Math.round(B.size - dmgToB));
      A.morale -= (dmgToA / Math.max(A.size, 1)) * 55 + this.rng.float(0.5, 2.5);
      B.morale -= (dmgToB / Math.max(B.size, 1)) * 55 + this.rng.float(0.5, 2.5);

      let loser = null, winner = null;
      if (A.morale <= 20 || A.size < 80) { loser = A; winner = B; }
      else if (B.morale <= 20 || B.size < 80) { loser = B; winner = A; }
      if (!loser) return;

      const battle = war.activeBattle;
      const lost = (loser === A ? battle.aStart - A.size : battle.bStart - B.size);
      const winLost = (winner === A ? battle.aStart - A.size : battle.bStart - B.size);
      war.activeBattle = null;

      // warscore swings toward the winner's side
      const swing = Math.min(28, 8 + lost / 120);
      war.score += (war.atkSide.includes(winner.faction) ? swing : -swing);
      this.totals.fallen += lost + winLost;
      this.fx.push({ kind: "loss", loc, amount: lost, color: this.faction(loser.faction).color });
      war.battles.push({
        name: `Battle of ${prov.name}`, day: this.day, date: this.formatDate(),
        winner: winner.faction, loser: loser.faction,
        winnerLosses: winLost, loserLosses: lost, loc,
      });

      const wc = this.character(winner.commanderId);
      if (wc) { wc.prestige += 12; wc.kills += lost; }
      this.factionState[winner.faction].prestige += 6;
      this.factionState[loser.faction].exhaustion += 7;
      this.factionState[winner.faction].exhaustion += 3;

      this.log(3, "battle",
        `${this.faction(winner.faction).name} wins the Battle of ${prov.name} — ${lost.toLocaleString()} of ${this.faction(loser.faction).name}'s soldiers fall${wc ? "; " + wc.name + " takes the field" : ""}.`,
        { province: loc, war: war.id, faction: winner.faction, character: winner.commanderId });

      // commander of the losing side may fall
      const lc = this.character(loser.commanderId);
      if (lc && this.rng.chance(0.10)) this._kill(lc, `slain in the Battle of ${prov.name}`);

      // rout: fall back toward home
      const home = this.capital(loser.faction);
      loser.loc = home ? home.id : loser.loc;
      loser.morale = 55; loser.retreatUntil = this.day + 6;
      loser.dest = null; loser.nextLoc = null;
    }

    _siegeTick(army, war) {
      const provSt = this.provinceState[army.loc];
      const prov = this.province(army.loc);
      const enemySide = war.atkSide.includes(army.faction) ? war.defSide : war.atkSide;
      if (!enemySide.includes(provSt.controller) || provSt.occupier === army.faction) return false;
      const enemy = provSt.controller;
      if (!provSt.siege || provSt.siege.by !== army.faction) {
        provSt.siege = { by: army.faction, progress: 0, startedDay: this.day, events: {} };
        this.mapVersion++;
        this.log(2, "siege",
          `${this.faction(army.faction).name} lays siege to ${prov.name}${prov.fort >= 4 ? ", whose great walls have never fallen" : ""}. Fort level ${prov.fort} sets the pace of the siege.`,
          { province: army.loc, war: war.id, faction: army.faction });
      }
      if (!provSt.siege.events) provSt.siege.events = {};
      this._consumeArmySupply(army, war, "siege");
      const fortDuration = 18 + prov.fort * 18 + provSt.garrison / 95;
      const pressure = Math.max(0.20, Math.sqrt(Math.max(army.size, 1)) / 56);
      const supplyMod = army.undersupplied ? 0.55 : 1;
      const moraleMod = Math.max(0.55, army.morale / 100);
      const rate = pressure * supplyMod * moraleMod / fortDuration;
      provSt.siege.progress += rate * this.rng.float(0.78, 1.22);
      if (provSt.siege.progress >= 0.35 && !provSt.siege.events.invested) {
        provSt.siege.events.invested = true;
        this.log(2, "siege",
          `${prov.name} is fully invested: roads are watched, gates are rationed, and ${this.faction(army.faction).name} tightens the ring.`,
          { province: army.loc, war: war.id, faction: army.faction });
      }
      if (provSt.siege.progress >= 0.70 && !provSt.siege.events.breach) {
        provSt.siege.events.breach = true;
        this.log(2, "siege",
          `A breach opens at ${prov.name}; the garrison spends its last strength while ${this.faction(army.faction).name} prepares the final assault.`,
          { province: army.loc, war: war.id, faction: army.faction });
      }
      if (provSt.siege.progress >= 1) {
        provSt.siege = null;
        provSt.occupier = army.faction;
        provSt.devastation = Math.min(100, provSt.devastation + 25);
        provSt.pop = Math.round(provSt.pop * 0.96);
        this.mapVersion++;
        this.fx.push({ kind: "flag", loc: army.loc, color: this.faction(army.faction).color });
        const isGoal = war.goal.province === army.loc;
        war.score += (war.atkSide.includes(army.faction) ? 1 : -1) * (isGoal ? 38 : 14);
        this.factionState[enemy].exhaustion += 12;
        this.log(3, "siege",
          `${prov.name} falls. ${this.faction(army.faction).name} banners rise over the ${prov.fort >= 3 ? "citadel" : "walls"}.`,
          { province: army.loc, war: war.id, faction: army.faction });
      }
      return true;
    }

    _disband(army) {
      const s = this.factionState[army.faction];
      s.manpower = Math.max(0, Math.min(s.maxManpower, s.manpower + Math.round(Math.max(0, army.size) * 0.7)));
      army.size = 0;
    }

    /* ------------------------------------------------ monthly pulse */

    _monthlyPulse() {
      // economy — court expenses grow with the hoard, so treasuries plateau
      for (const f of this.seed.factions) {
        const s = this.factionState[f.id];
        const court = Math.max(0, Math.round(s.treasury * 0.02));
        s.treasury += this.monthlyIncome(f.id) - this.monthlyUpkeep(f.id) - court;
        if (s.treasury < 0) {
          s.exhaustion += 4 + Math.min(6, Math.ceil(Math.abs(s.treasury) / 120));
          s.treasury = 0;
        }
        s.manpower = Math.max(0, Math.min(s.maxManpower, s.manpower + Math.round(s.maxManpower * 0.045)));
        s.exhaustion = Math.max(0, s.exhaustion - (this.warsOf(f.id).length ? 0 : 6));
        this._refreshManpower(f.id, false);
        // tribute payments
        for (const [to, remaining] of Object.entries(s.tribute)) {
          if (remaining <= 0) { delete s.tribute[to]; continue; }
          const pay = Math.min(40, remaining, s.treasury);
          s.treasury -= pay; this.factionState[to].treasury += pay;
          s.tribute[to] = remaining - pay;
        }
        s.treasury = Math.max(0, s.treasury);
        s.manpower = Math.max(0, s.manpower);
      }
      // devastation heals, occupation lifts if occupier no longer at war
      for (const p of this.seed.provinces) {
        const st = this.provinceState[p.id];
        st.devastation = Math.max(0, st.devastation - 2);
        st.pop = Math.round(st.pop * 1.002);
        if (st.occupier && !this.atWar(st.occupier, st.controller)) {
          st.occupier = null;
          this.mapVersion++;
        }
        // hunger riots when the land is bled white
        if (st.devastation > 45 && !st.riotLogged) {
          st.riotLogged = true;
          st.pop = Math.round(st.pop * 0.97);
          this.log(2, "death",
            `Hunger riots in ${p.name}: the granaries are bare and the ${this.faction(st.controller).name} tax men dare not enter.`,
            { province: p.id, faction: st.controller });
        }
        if (st.devastation < 25) st.riotLogged = false;
      }
      this.mapVersion++; // devastation drift matters in the Ruin map mode
      this._diplomacyPulse();
      this._peacePulse();
      this._restorationPulse();
      this._omenPulse();
      // reinforcements
      for (const army of this.armies) {
        const s = this.factionState[army.faction];
        const st = this.provinceState[army.loc];
        if (st && st.controller === army.faction && s.manpower > 200) {
          const add = Math.min(300, s.manpower - 100);
          army.size += add; s.manpower = Math.max(0, s.manpower - add);
          army.maxSupply = this._armyMaxSupply(army.size, this.province(army.loc));
        }
      }
      this._recordMonthlyRecap();
    }

    _recordMonthlyRecap() {
      const events = this.events.slice(this._monthStartEventIndex);
      const typeCounts = {};
      for (const ev of events) typeCounts[ev.type] = (typeCounts[ev.type] || 0) + 1;
      const activeWars = this.wars.filter((w) => !w.over);
      const activeSieges = this.seed.provinces
        .filter((p) => this.provinceState[p.id].siege)
        .map((p) => ({
          province: p.id,
          by: this.provinceState[p.id].siege.by,
          progress: this.provinceState[p.id].siege.progress,
        }));
      const troubledFactions = this.seed.factions
        .map((f) => {
          const st = this.factionState[f.id];
          const income = this.monthlyIncome(f.id);
          const upkeep = this.monthlyUpkeep(f.id);
          const pressure = income - upkeep - Math.max(0, Math.round(st.treasury * 0.02));
          const risks = [];
          if (pressure < 0) risks.push("deficit");
          if (st.exhaustion >= 25) risks.push("exhaustion");
          if (st.manpower < st.maxManpower * 0.25) risks.push("low manpower");
          if (!this.ownedProvinces(f.id).length) risks.push("landless");
          return { faction: f.id, pressure, exhaustion: st.exhaustion, risks };
        })
        .filter((r) => r.risks.length)
        .sort((a, b) => b.risks.length - a.risks.length || a.pressure - b.pressure)
        .slice(0, 6);

      this.monthlyRecaps.push({
        id: uid("recap"),
        day: this.day,
        date: this.formatDate(),
        events: events.length,
        typeCounts,
        activeWars: activeWars.map((w) => w.id),
        activeSieges,
        fallen: this.totals.fallen - this._monthStartFallen,
        warsEnded: this.totals.warsEnded - this._monthStartWarsEnded,
        troubledFactions,
        headlines: events.filter((ev) => ev.importance >= 3).slice(-5).map((ev) => ev.text),
      });
      if (this.monthlyRecaps.length > 72) this.monthlyRecaps.splice(0, this.monthlyRecaps.length - 72);
      this._monthStartEventIndex = this.events.length;
      this._monthStartFallen = this.totals.fallen;
      this._monthStartWarsEnded = this.totals.warsEnded;
    }

    _restorationPulse() {
      // A landless people is not a dead people: where a claim still burns and
      // the current holder is distracted, the banners rise again.
      for (const f of this.seed.factions) {
        if (this.ownedProvinces(f.id).length) continue;
        const claim = this.claims.find((c) => c.claimant === f.id && c.strength > 20);
        if (!claim) continue;
        const target = claim.target;
        const holder = this.provinceState[target].controller;
        if (holder === f.id) continue;
        const holderBusy = this.warsOf(holder).length > 0 ||
          this.provinceState[target].devastation > 15;
        const p = holderBusy ? 0.012 : 0.003;
        if (!this.rng.chance(p)) continue;
        this.provinceState[target].controller = f.id;
        this.provinceState[target].occupier = null;
        this.provinceState[target].siege = null;
        this.mapVersion++;
        this._refreshManpower(f.id, true);
        this.factionState[f.id].exhaustion = 0;
        let ruler = this.rulerOf(f.id);
        if (!ruler || !ruler.alive) {
          ruler = this._spawnCharacter(f.id, "restorer");
          ruler.isRuler = true; ruler.reignStart = this.date.year;
          this.factionState[f.id].rulerId = ruler.id;
        }
        this._bumpOpinion(f.id, holder, -40);
        this.log(3, "war",
          `The ${f.name} rises again: while ${this.faction(holder).name} looks elsewhere, ${ruler.name} raises the old banners over ${this.province(target).name}.`,
          { faction: f.id, province: target, character: ruler.id });
      }
    }

    _omenPulse() {
      // Ambient magecraft: rare workings at mana sites keep the world strange.
      for (const mage of this.mages) {
        if (!mage.alive || !this.rng.chance(0.015)) continue;
        const host = this.character(mage.character);
        const patron = this.faction(mage.patron);
        const site = this.ownedProvinces(mage.patron).find((p) => p.manaSite > 0) ||
          this.capital(mage.patron);
        if (!site || !patron) continue;
        const st = this.provinceState[site.id];
        st.devastation = Math.max(0, st.devastation - 6);
        this.log(2, "magic",
          `${host ? host.name : "A hooded figure"} performs a ${mage.specialization} working at ${site.name}; the ${patron.name} courts pretend not to watch.`,
          { faction: mage.patron, province: site.id, character: mage.character });
      }
    }

    _factionsBorder(a, b) {
      for (const p of this.ownedProvinces(a)) {
        for (const n of (this.adjacency[p.id] || [])) {
          if (this.provinceState[n].controller === b) return true;
        }
      }
      return false;
    }

    _diplomacyPulse() {
      // opinions drift toward their seeded baseline; shared faith warms
      const baseline = {};
      for (const r of this.seed.relations) baseline[this._oKey(r.a, r.b)] = r.score;
      for (const key of Object.keys(this.opinions)) {
        const target = baseline[key] !== undefined ? baseline[key] : 0;
        const cur = this.opinions[key];
        this.opinions[key] = cur + Math.sign(target - cur) * Math.min(1.5, Math.abs(target - cur));
      }
      // war declarations
      for (const rel of this.seed.relations) {
        const { a, b } = rel;
        if (this.atWar(a, b)) continue;
        const sa = this.factionState[a], sb = this.factionState[b];
        if ((sa.truces[b] || 0) > this.day) continue;
        if (!this.ownedProvinces(a).length || !this.ownedProvinces(b).length) continue;
        const op = this.opinion(a, b);
        if (op > -10) continue;

        for (const [agg, def] of [[a, b], [b, a]]) {
          if (this.warsOf(agg).length >= 1) continue;   // one war at a time
          if (this.factionState[agg].exhaustion > 30) continue;
          const claim = this.claims.find((c) => c.claimant === agg &&
            this.provinceState[c.target] && this.provinceState[c.target].controller === def);
          const isRaider = this.faction(agg).government === "seasonal_khan_ring";
          if (!claim && !isRaider && !this._factionsBorder(agg, def)) continue;

          let p = (rel.warRisk / 100) * 0.045 * this._traitFactor(agg, "war");
          if (claim) p *= 1 + claim.strength / 120;
          if (this.armyStrength(def) > 0) p *= 0.4;     // hesitant while target mobilized
          if (this.factionState[agg].treasury < 100) p *= 0.4;
          // sprawling realms draw wary coalitions of excuses — expansion slows
          p *= 1 / (1 + Math.max(0, this.ownedProvinces(agg).length - 2) * 0.8);
          if (this.rng.chance(Math.min(0.5, p))) {
            const intent = this._warIntentReason(agg, def, claim, isRaider && !claim, rel, p);
            this._declareWar(agg, def, claim, isRaider && !claim, intent);
            break;
          }
        }
      }
    }

    _warIntentReason(attacker, defender, claim, isRaid, relation, chance) {
      const attackerName = this.faction(attacker).shortName || this.faction(attacker).name;
      const defenderName = this.faction(defender).shortName || this.faction(defender).name;
      const risk = relation ? ` seeded risk ${relation.warRisk}` : "";
      const odds = chance !== undefined ? ` current chance ${(Math.min(0.5, chance) * 100).toFixed(1)}%` : "";
      if (claim) {
        return `${attackerName} sees a usable ${claim.type} claim on ${this.province(claim.target).name}; opinion with ${defenderName} is ${Math.round(this.opinion(attacker, defender))}.${risk}${odds}`;
      }
      if (isRaid) {
        return `${attackerName} chooses a raid because its government rewards plunder and ${defenderName} is reachable.${risk}${odds}`;
      }
      return `${attackerName} escalates a border quarrel with ${defenderName}; hostile opinion and adjacency make war plausible.${risk}${odds}`;
    }

    _declareWar(attacker, defender, claim, isRaid, intentReason) {
      const goal = claim
        ? { type: "conquest", province: claim.target, claim: claim.id }
        : isRaid
          ? { type: "raid", province: (this.capital(defender) || {}).id }
          : { type: "conquest", province: this._borderPrize(attacker, defender) };
      const prizeName = goal.province ? this.province(goal.province).name : "the frontier";
      const war = {
        id: uid("war"),
        name: goal.type === "raid"
          ? `The ${this.seed.cultures[this.faction(attacker).culture].name} Raid of ${this.date.year} AE`
          : `War of ${prizeName}`,
        attacker, defender, goal, score: 0, startDay: this.day,
        startDate: this.formatDate(), battles: [], over: false,
        atkSide: [attacker], defSide: [defender],
        intentReason: intentReason || this._warIntentReason(attacker, defender, claim, isRaid),
      };
      this.wars.push(war);
      const reason = claim
        ? `pressing its ${claim.type} claim (${claim.source})`
        : isRaid ? "riding for plunder and tribute"
          : "pressing a border quarrel into open war";
      this.log(3, "war",
        `${this.faction(attacker).name} declares war on ${this.faction(defender).name}, ${reason}. The prize: ${prizeName}. Intent: ${war.intentReason}.`,
        { war: war.id, faction: attacker, province: goal.province });
      this._bumpOpinion(attacker, defender, -25);
      this._raiseArmy(attacker, war);
      this._raiseArmy(defender, war);

      // friends of the defender may honour old oaths and join the defence
      const defFaith = this.faction(defender).religion;
      for (const f of this.seed.factions) {
        if (f.id === attacker || f.id === defender) continue;
        if (!this.ownedProvinces(f.id).length) continue;
        if (this.warsOf(f.id).length) continue;
        if ((this.factionState[f.id].truces[attacker] || 0) > this.day) continue;
        const sworn = f.religion === defFaith || this.opinion(f.id, defender) >= 30;
        if (!sworn || this.opinion(f.id, attacker) > 20) continue;
        if (!this.rng.chance(0.55)) continue;
        war.defSide.push(f.id);
        this._bumpOpinion(f.id, attacker, -15);
        this.log(3, "war",
          `${f.name} rides to the defence of ${this.faction(defender).name}, honouring ${f.religion === defFaith ? "shared faith" : "old friendship"}.`,
          { war: war.id, faction: f.id });
        this._raiseArmy(f.id, war);
      }
    }

    _borderPrize(attacker, defender) {
      for (const p of this.ownedProvinces(defender)) {
        for (const n of (this.adjacency[p.id] || [])) {
          if (this.provinceState[n].controller === attacker) return p.id;
        }
      }
      const owned = this.ownedProvinces(defender);
      return owned.length ? owned[0].id : null;
    }

    _peacePulse() {
      for (const war of this.wars) {
        if (war.over) continue;
        const sa = this.factionState[war.attacker], sd = this.factionState[war.defender];
        const years = (this.day - war.startDay) / 360;
        // exhaustion pushes both sides to the table
        if (war.score >= 55) { this._endWar(war, war.attacker, "attacker war score became decisive"); continue; }
        if (sd.exhaustion >= 65) { this._endWar(war, war.attacker, "defender exhaustion broke their bargaining position"); continue; }
        if (war.score <= -45) { this._endWar(war, war.defender, "defender war score held firm"); continue; }
        if (sa.exhaustion >= 65) { this._endWar(war, war.defender, "attacker exhaustion made the offensive collapse"); continue; }
        if (years > 4.5) { this._endWar(war, null, "neither side could force a decision after years of campaigning"); continue; }
      }
    }

    _endWar(war, victor, endReason) {
      war.over = true; war.endDate = this.formatDate();
      this.totals.warsEnded++;
      const att = this.faction(war.attacker), def = this.faction(war.defender);
      const sa = this.factionState[war.attacker], sd = this.factionState[war.defender];
      const changedHands = [];
      const prestige = [];
      const standingLosses = [];
      for (const atk of war.atkSide) {
        for (const dfd of war.defSide) {
          this.factionState[atk].truces[dfd] = this.day + 360 * 5;
          this.factionState[dfd].truces[atk] = this.day + 360 * 5;
        }
      }
      // allies remember who stood with them
      for (const ally of war.defSide) {
        if (ally !== war.defender) this._bumpOpinion(ally, war.defender, 12);
      }

      // lift occupations between the warring sides
      const parties = [...war.atkSide, ...war.defSide];
      for (const p of this.seed.provinces) {
        const st = this.provinceState[p.id];
        if (st.occupier && parties.includes(st.occupier) && parties.includes(st.controller)) {
          st.occupier = null;
          this.mapVersion++;
        }
        if (st.siege && parties.includes(st.siege.by)) { st.siege = null; this.mapVersion++; }
      }

      if (!victor) {
        war.peaceSummary = {
          victor: null,
          reason: endReason,
          changedHands,
          prestige,
          standingLosses,
          truce: "five-year truce between all war parties",
        };
        this.log(3, "peace",
          `${war.name} gutters out in white peace because ${endReason}. No land changes hands; no court can claim glory. A five-year truce is sworn between the war parties.`,
          { war: war.id, faction: war.attacker });
      } else if (victor === war.attacker) {
        sa.warsWon += 1; sd.warsLost += 1; sa.prestige += 25;
        prestige.push({ faction: war.attacker, amount: 25 });
        standingLosses.push({ faction: war.defender, reason: "lost the war" });
        // the prize can only change hands if the defender still holds it
        if (war.goal.type === "conquest" && war.goal.province &&
            this.provinceState[war.goal.province].controller === war.defender) {
          const prov = this.province(war.goal.province);
          this.provinceState[prov.id].controller = war.attacker;
          this.provinceState[prov.id].occupier = null;
          changedHands.push({ province: prov.id, from: war.defender, to: war.attacker });
          this.mapVersion++;
          const claim = this.claims.find((c) => c.id === war.goal.claim);
          if (claim) claim.strength = Math.min(100, claim.strength + 10);
          // the loser now remembers a grievance: a new claim is born
          this.claims.push({
            id: uid("claim"), claimant: war.defender, target: prov.id,
            type: "war grievance", source: `${war.name}, ${war.endDate}`,
            strength: 55, myth: "living memory", recognizedBy: def.religion,
          });
          war.peaceSummary = {
            victor,
            reason: endReason,
            changedHands,
            prestige,
            standingLosses,
            truce: "five-year truce between all war parties",
          };
          this.log(3, "peace",
            `${war.name} ends because ${endReason}: ${prov.name} is ceded to ${att.name}. ${att.shortName || att.name} gains 25 prestige; ${def.shortName || def.name} loses standing and receives a grievance claim. A five-year truce is sworn.`,
            { war: war.id, faction: war.attacker, province: prov.id });
        } else {
          const gold = Math.min(400, Math.max(0, Math.round(sd.treasury * 0.4)));
          sd.treasury -= gold; sa.treasury += gold;
          sd.tribute[war.attacker] = (sd.tribute[war.attacker] || 0) + 240;
          changedHands.push({ tributeFrom: war.defender, to: war.attacker, silver: gold, futureTribute: 240 });
          war.peaceSummary = {
            victor,
            reason: endReason,
            changedHands,
            prestige,
            standingLosses,
            truce: "five-year truce between all war parties",
          };
          this.log(3, "peace",
            `${war.name} ends because ${endReason}: ${def.name} buys peace with ${gold} silver and future tribute. ${att.shortName || att.name} gains 25 prestige; ${def.shortName || def.name} loses standing. A five-year truce is sworn.`,
            { war: war.id, faction: war.attacker });
        }
        const ruler = this.rulerOf(war.attacker);
        if (ruler) ruler.prestige += 20;
      } else {
        sd.warsWon += 1; sa.warsLost += 1; sd.prestige += 20;
        prestige.push({ faction: war.defender, amount: 20 });
        standingLosses.push({ faction: war.attacker, reason: "failed offensive" });
        const gold = Math.min(250, Math.max(0, Math.round(sa.treasury * 0.3)));
        sa.treasury -= gold; sd.treasury += gold;
        changedHands.push({ reparationsFrom: war.attacker, to: war.defender, silver: gold });
        war.peaceSummary = {
          victor,
          reason: endReason,
          changedHands,
          prestige,
          standingLosses,
          truce: "five-year truce between all war parties",
        };
        this.log(3, "peace",
          `${war.name} ends because ${endReason}: ${att.name} pays ${gold} silver to ${def.name}. ${def.shortName || def.name} gains 20 prestige; ${att.shortName || att.name} loses standing. A five-year truce is sworn.`,
          { war: war.id, faction: war.defender });
      }
      sa.treasury = Math.max(0, sa.treasury);
      sd.treasury = Math.max(0, sd.treasury);
      this._bumpOpinion(war.attacker, war.defender, -10);
      // armies march home and stand down
      for (const a of this.armies) if (a.warId === war.id) this._disband(a);
    }

    /* ------------------------------------------------ yearly pulse */

    childrenOf(cid) {
      return this.characters.filter((c) => c.parentId === cid);
    }

    heirOf(fid) {
      const ruler = this.rulerOf(fid);
      if (!ruler) return null;
      const kids = this.childrenOf(ruler.id).filter((c) => c.alive)
        .sort((a, b) => b.age - a.age);
      return kids[0] || null;
    }

    _fertility(species, age) {
      if (species === "elf") return age >= 60 && age <= 280 ? 0.04 : 0;
      if (species === "dwarf") return age >= 30 && age <= 100 ? 0.08 : 0;
      return age >= 18 && age <= 50 ? 0.16 : 0;
    }

    _yearlyPulse() {
      // children are born to ruling lines
      for (const f of this.seed.factions) {
        const ruler = this.rulerOf(f.id);
        if (!ruler || !ruler.alive) continue;
        const brood = this.childrenOf(ruler.id).filter((c) => c.alive);
        if (brood.length >= 4) continue;
        if (!this.rng.chance(this._fertility(ruler.species, ruler.age))) continue;
        const dynasty = ruler.name.split(" ").slice(1).join(" ");
        const child = {
          id: uid("char"),
          name: this.forge.given(ruler.culture) + (dynasty ? " " + dynasty : ""),
          species: ruler.species, culture: ruler.culture, faction: f.id,
          role: "scion of the ruling line", age: 0,
          pressure: "must grow into a name that is already spoken for",
          alive: true, isRuler: false, traits: this._rollTraits(),
          prestige: 0, kills: 0, parentId: ruler.id,
        };
        this.characters.push(child);
        this.log(2, "birth",
          `A child is born to ${ruler.name}: the ${f.name} court swears the oaths over ${child.name}.`,
          { faction: f.id, character: child.id });
      }

      for (const c of this.characters) {
        if (!c.alive) continue;
        c.age += 1;
        const sp = this.seed.species[c.species] || { oldAge: 55, maxAge: 95 };
        let deathChance = 0.006;
        if (c.age > sp.oldAge) {
          deathChance = 0.03 + 0.30 * (c.age - sp.oldAge) / Math.max(1, sp.maxAge - sp.oldAge);
        }
        if (this.rng.chance(deathChance)) {
          this._kill(c, c.age > sp.oldAge ? "dies full of years" : "is carried off by fever");
        }
      }
      // claims fade or fester
      for (const claim of this.claims) {
        claim.strength = Math.max(5, claim.strength - 0.5);
      }
    }

    _kill(character, causeText) {
      character.alive = false;
      const f = this.faction(character.faction);
      const wasRuler = this.factionState[character.faction] &&
        this.factionState[character.faction].rulerId === character.id;
      // a mage bound to this character dies with them
      const mage = this.mages.find((m) => m.character === character.id && m.alive);
      if (mage) mage.alive = false;

      if (!wasRuler) {
        this.log(2, "death", `${character.name}, ${character.role} of ${f.name}, ${causeText}.`,
          { faction: character.faction, character: character.id });
        return;
      }
      // succession: the eldest living child inherits; failing that, distant kin
      const children = this.childrenOf(character.id).filter((c) => c.alive)
        .sort((a, b) => b.age - a.age);
      let heir = children[0] || null;
      let regency = false;
      if (heir) {
        heir.isRuler = true;
        heir.role = character.role;
        heir.reignStart = this.date.year;
        heir.prestige += Math.round(character.prestige * 0.3);
        if (heir.age < 16) { regency = true; heir.pressure = "must survive the regents who rule in their name"; }
        else heir.pressure = this.rng.pick(PRESSURE_TEMPLATES);
      } else {
        const dynasty = character.name.split(" ").slice(1).join(" ");
        heir = {
          id: uid("char"),
          name: this.forge.given(f.culture) + (dynasty ? " " + dynasty : " " + this.forge.epithet()),
          species: character.species, culture: character.culture, faction: character.faction,
          role: character.role, age: Math.max(16, this.rng.int(17, 40)),
          pressure: this.rng.pick(PRESSURE_TEMPLATES),
          alive: true, isRuler: true, traits: this._rollTraits(),
          prestige: Math.round(character.prestige * 0.3), kills: 0,
          reignStart: this.date.year,
        };
        this.characters.push(heir);
      }
      this.factionState[character.faction].rulerId = heir.id;
      const line = children.length
        ? (regency
          ? `${heir.name} is but ${heir.age}; a regency council rules ${f.name} in their name.`
          : `${heir.name}, ${heir.age} years old, inherits rule of ${f.name}.`)
        : `The direct line is broken: ${heir.name}, a kin of the house, takes up rule of ${f.name}.`;
      this.log(3, "succession",
        `${character.name} ${causeText}. ${line}`,
        { faction: character.faction, character: heir.id });
    }
  }

  window.WG = window.WG || {};
  window.WG.Simulation = Simulation;
  window.WG.MONTH_NAMES = MONTH_NAMES;
})();

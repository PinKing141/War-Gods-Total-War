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
      this.wars = [];
      this.armies = [];
      this.adjacency = null;   // provided by map after ownership raster

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
        ((w.attacker === a && w.defender === b) || (w.attacker === b && w.defender === a)));
    }
    warsOf(fid) { return this.wars.filter((w) => !w.over && (w.attacker === fid || w.defender === fid)); }
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

    _raiseArmy(fid, war) {
      const cap = this.capital(fid);
      if (!cap) return;
      const s = this.factionState[fid];
      const size = Math.max(500, Math.round(s.manpower * 0.65));
      s.manpower -= Math.min(s.manpower, size);
      const culture = this.seed.cultures[this.faction(fid).culture];
      let commander = this.rulerOf(fid);
      if (!commander || this.rng.chance(0.55)) {
        commander = this._spawnCharacter(fid, "war captain");
      }
      this.armies.push({
        id: uid("army"),
        faction: fid, size, morale: 100,
        quality: 0.9 + this.rng.float(0, 0.35),
        commanderId: commander.id,
        loc: cap.id, moveLeft: 0, dest: null,
        warId: war.id, retreatUntil: 0,
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
      const enemy = war.attacker === army.faction ? war.defender : war.attacker;
      const isAttacker = war.attacker === army.faction;
      // 1. hostile army on our soil -> intercept
      const invaders = this.armies.filter((a) =>
        a.faction === enemy && this.provinceState[a.loc] &&
        this.provinceState[a.loc].controller === army.faction);
      if (invaders.length) {
        return invaders.reduce((x, y) => (x.size > y.size ? x : y)).loc;
      }
      // 2. attacker: take the war goal, then anything unoccupied of theirs
      const enemyProvinces = this.ownedProvinces(enemy)
        .filter((p) => this.provinceState[p.id].occupier !== army.faction);
      if (isAttacker && war.goal.province &&
          this.provinceState[war.goal.province].controller === enemy &&
          this.provinceState[war.goal.province].occupier !== army.faction) {
        return war.goal.province;
      }
      if (enemyProvinces.length) {
        // nearest by BFS depth — approximate with first found
        return enemyProvinces[0].id;
      }
      // 3. nothing to do: hold the capital
      const cap = this.capital(army.faction);
      return cap ? cap.id : army.loc;
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

        const targetId = this._armyTargets(army, war);
        if (targetId && targetId !== army.loc) {
          if (!army.dest || army.dest !== targetId) {
            army.dest = targetId; army.moveLeft = 0;
          }
          if (army.moveLeft <= 0) {
            const next = this._pathNext(army.loc, army.dest);
            if (next) {
              const terr = this.seed.terrains[this.province(next).terrain];
              army.moveLeft = terr ? terr.moveDays : 3;
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
          this._siegeTick(army, war);
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

      // warscore swings toward the winner
      const swing = Math.min(28, 8 + lost / 120);
      war.score += (winner.faction === war.attacker ? swing : -swing);
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
      const enemy = war.attacker === army.faction ? war.defender : war.attacker;
      if (provSt.controller !== enemy || provSt.occupier === army.faction) return;
      if (!provSt.siege || provSt.siege.by !== army.faction) {
        provSt.siege = { by: army.faction, progress: 0 };
        this.log(2, "siege",
          `${this.faction(army.faction).name} lays siege to ${prov.name}${prov.fort >= 4 ? ", whose great walls have never fallen" : ""}.`,
          { province: army.loc, war: war.id, faction: army.faction });
      }
      const rate = army.size / (900 + prov.fort * 950 + provSt.garrison * 2.2);
      provSt.siege.progress += rate * this.rng.float(0.7, 1.3);
      if (provSt.siege.progress >= 1) {
        provSt.siege = null;
        provSt.occupier = army.faction;
        provSt.devastation = Math.min(100, provSt.devastation + 25);
        provSt.pop = Math.round(provSt.pop * 0.96);
        const isGoal = war.goal.province === army.loc;
        war.score += (army.faction === war.attacker ? 1 : -1) * (isGoal ? 38 : 14);
        this.factionState[enemy].exhaustion += 12;
        this.log(3, "siege",
          `${prov.name} falls. ${this.faction(army.faction).name} banners rise over the ${prov.fort >= 3 ? "citadel" : "walls"}.`,
          { province: army.loc, war: war.id, faction: army.faction });
      }
    }

    _disband(army) {
      const s = this.factionState[army.faction];
      s.manpower = Math.min(s.maxManpower, s.manpower + Math.round(army.size * 0.7));
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
          s.exhaustion += 4;
          s.treasury = Math.max(s.treasury, -400);
        }
        s.manpower = Math.min(s.maxManpower, s.manpower + Math.round(s.maxManpower * 0.045));
        s.exhaustion = Math.max(0, s.exhaustion - (this.warsOf(f.id).length ? 0 : 6));
        this._refreshManpower(f.id, false);
        // tribute payments
        for (const [to, remaining] of Object.entries(s.tribute)) {
          if (remaining <= 0) { delete s.tribute[to]; continue; }
          const pay = Math.min(40, remaining);
          s.treasury -= pay; this.factionState[to].treasury += pay;
          s.tribute[to] = remaining - pay;
        }
      }
      // devastation heals, occupation lifts if occupier no longer at war
      for (const p of this.seed.provinces) {
        const st = this.provinceState[p.id];
        st.devastation = Math.max(0, st.devastation - 2);
        st.pop = Math.round(st.pop * 1.002);
        if (st.occupier && !this.atWar(st.occupier, st.controller)) st.occupier = null;
      }
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
          army.size += add; s.manpower -= add;
        }
      }
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
            this._declareWar(agg, def, claim, isRaider && !claim);
            break;
          }
        }
      }
    }

    _declareWar(attacker, defender, claim, isRaid) {
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
      };
      this.wars.push(war);
      const reason = claim
        ? `pressing its ${claim.type} claim (${claim.source})`
        : isRaid ? "riding for plunder and tribute"
          : "pressing a border quarrel into open war";
      this.log(3, "war",
        `${this.faction(attacker).name} declares war on ${this.faction(defender).name}, ${reason}. The prize: ${prizeName}.`,
        { war: war.id, faction: attacker, province: goal.province });
      this._bumpOpinion(attacker, defender, -25);
      this._raiseArmy(attacker, war);
      this._raiseArmy(defender, war);
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
        if (war.score >= 55 || sd.exhaustion >= 65) { this._endWar(war, war.attacker); continue; }
        if (war.score <= -45 || sa.exhaustion >= 65) { this._endWar(war, war.defender); continue; }
        if (years > 4.5) { this._endWar(war, null); continue; }
      }
    }

    _endWar(war, victor) {
      war.over = true; war.endDate = this.formatDate();
      const att = this.faction(war.attacker), def = this.faction(war.defender);
      const sa = this.factionState[war.attacker], sd = this.factionState[war.defender];
      sa.truces[war.defender] = this.day + 360 * 5;
      sd.truces[war.attacker] = this.day + 360 * 5;

      // lift occupations between the two parties
      for (const p of this.seed.provinces) {
        const st = this.provinceState[p.id];
        if (st.occupier === war.attacker || st.occupier === war.defender) {
          if (st.controller === war.attacker || st.controller === war.defender) st.occupier = null;
        }
        if (st.siege && (st.siege.by === war.attacker || st.siege.by === war.defender)) st.siege = null;
      }

      if (!victor) {
        this.log(3, "peace",
          `${war.name} gutters out after years of ruin — a white peace between ${att.name} and ${def.name}.`,
          { war: war.id, faction: war.attacker });
      } else if (victor === war.attacker) {
        sa.warsWon += 1; sd.warsLost += 1; sa.prestige += 25;
        // the prize can only change hands if the defender still holds it
        if (war.goal.type === "conquest" && war.goal.province &&
            this.provinceState[war.goal.province].controller === war.defender) {
          const prov = this.province(war.goal.province);
          this.provinceState[prov.id].controller = war.attacker;
          this.provinceState[prov.id].occupier = null;
          const claim = this.claims.find((c) => c.id === war.goal.claim);
          if (claim) claim.strength = Math.min(100, claim.strength + 10);
          // the loser now remembers a grievance: a new claim is born
          this.claims.push({
            id: uid("claim"), claimant: war.defender, target: prov.id,
            type: "war grievance", source: `${war.name}, ${war.endDate}`,
            strength: 55, myth: "living memory", recognizedBy: def.religion,
          });
          this.log(3, "peace",
            `${war.name} ends: ${prov.name} is ceded to ${att.name}. ${def.name} signs, and does not forget.`,
            { war: war.id, faction: war.attacker, province: prov.id });
        } else {
          const gold = Math.min(400, Math.max(120, Math.round(sd.treasury * 0.4)));
          sd.treasury -= gold; sa.treasury += gold;
          sd.tribute[war.attacker] = (sd.tribute[war.attacker] || 0) + 240;
          this.log(3, "peace",
            `${war.name} ends: ${def.name} buys off the riders with ${gold} silver and a promise of tribute.`,
            { war: war.id, faction: war.attacker });
        }
        const ruler = this.rulerOf(war.attacker);
        if (ruler) ruler.prestige += 20;
      } else {
        sd.warsWon += 1; sa.warsLost += 1; sd.prestige += 20;
        const gold = Math.min(250, Math.max(80, Math.round(sa.treasury * 0.3)));
        sa.treasury -= gold; sd.treasury += gold;
        this.log(3, "peace",
          `${war.name} ends in humiliation for ${att.name}: reparations of ${gold} silver flow to ${def.name}.`,
          { war: war.id, faction: war.defender });
      }
      this._bumpOpinion(war.attacker, war.defender, -10);
      // armies march home and stand down
      for (const a of this.armies) if (a.warId === war.id) this._disband(a);
    }

    /* ------------------------------------------------ yearly pulse */

    _yearlyPulse() {
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
      // succession
      const dynasty = character.name.split(" ").slice(1).join(" ");
      const heir = {
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
      this.factionState[character.faction].rulerId = heir.id;
      this.log(3, "succession",
        `${character.name} ${causeText}. ${heir.name}, ${heir.age} years old, takes up rule of ${f.name} — ${heir.pressure}.`,
        { faction: character.faction, character: heir.id });
    }
  }

  window.WG = window.WG || {};
  window.WG.Simulation = Simulation;
  window.WG.MONTH_NAMES = MONTH_NAMES;
})();

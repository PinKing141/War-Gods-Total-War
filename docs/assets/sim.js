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

  const AMBITION_TEMPLATES = [
    "become ruler", "protect dynasty", "win glory", "secure wealth",
    "defend faith", "restore old claims", "keep peace", "master the court",
  ];

  const FEAR_TEMPLATES = [
    "dying forgotten", "losing legitimacy", "court betrayal", "dynasty failure",
    "poverty", "magical scandal", "foreign conquest", "open revolt",
  ];
  const VALID_AMBITIONS = new Set(AMBITION_TEMPLATES);
  const VALID_FEARS = new Set(FEAR_TEMPLATES);

  const RELATIONSHIP_TYPES = [
    "parent", "child", "sibling", "spouse", "lover", "friend", "rival", "enemy",
    "mentor", "student", "commander", "vassal", "patron", "hostage", "betrayer", "rescuer",
  ];
  const VALID_RELATIONSHIP_TYPES = new Set(RELATIONSHIP_TYPES);
  const RECIPROCAL_RELATIONSHIP = {
    parent: "child",
    child: "parent",
    sibling: "sibling",
    spouse: "spouse",
    lover: "lover",
    friend: "friend",
    rival: "rival",
    enemy: "enemy",
    mentor: "student",
    student: "mentor",
    commander: "vassal",
    vassal: "commander",
    patron: "vassal",
    hostage: "hostage",
    betrayer: "enemy",
    rescuer: "friend",
  };
  const MEMORY_TYPES = [
    "family death", "battle victory", "battle defeat", "promotion", "betrayal",
    "humiliation", "wound", "lost province", "saved life", "first command", "exile",
  ];
  const VALID_MEMORY_TYPES = new Set(MEMORY_TYPES);
  const COURT_OFFICES = [
    "ruler", "heir", "chancellor", "marshal", "steward", "spymaster",
    "court_mage", "high_priest", "captain_of_guard", "governor", "regent",
  ];
  const VALID_COURT_OFFICES = new Set(COURT_OFFICES);
  const COURT_OFFICE_LABELS = {
    ruler: "Ruler",
    heir: "Heir",
    chancellor: "Chancellor",
    marshal: "Marshal",
    steward: "Steward",
    spymaster: "Spymaster",
    court_mage: "Court Mage",
    high_priest: "High Priest",
    captain_of_guard: "Captain of Guard",
    governor: "Governor",
    regent: "Regent",
  };
  const SOCIAL_GROUPS = [
    "nobles", "clergy", "merchants", "peasants", "craftsmen", "soldiers",
    "mages", "scholars", "minorities", "tribes", "foreign_settlers", "refugees", "urban_poor",
  ];
  const VALID_SOCIAL_GROUPS = new Set(SOCIAL_GROUPS);
  const SOCIAL_GROUP_LABELS = {
    nobles: "Nobles",
    clergy: "Clergy",
    merchants: "Merchants",
    peasants: "Peasants",
    craftsmen: "Craftsmen",
    soldiers: "Soldiers",
    mages: "Mages",
    scholars: "Scholars",
    minorities: "Minorities",
    tribes: "Tribes",
    foreign_settlers: "Foreign settlers",
    refugees: "Refugees",
    urban_poor: "Urban poor",
  };

  function emptyMilitaryRecord() {
    return {
      battlesFought: 0,
      battlesWon: 0,
      battlesLost: 0,
      siegesLed: 0,
      wounds: 0,
      notableVictories: [],
      notableDefeats: [],
    };
  }

  function emptyFamily() {
    return {
      father: null,
      mother: null,
      spouses: [],
      lovers: [],
      children: [],
      siblings: [],
      dynasty: "common line",
      house: "unhoused",
      branchType: "main",
      branchFounder: null,
      parentHouseId: null,
      cadetReason: null,
      bastard: false,
      legitimised: false,
      legitimacy: 50,
      inheritanceRank: null,
      claimStrength: 0,
    };
  }

  const AI_PRIORITY_INFO = {
    expand_territory: "Expand territory",
    protect_homeland: "Protect homeland",
    recover_old_claims: "Recover old claims",
    raid_for_wealth: "Raid for wealth",
    avoid_war: "Avoid war",
    secure_trade_routes: "Secure trade routes",
    hold_mountain_passes: "Hold mountain passes",
    control_ports: "Control ports",
    defend_faith: "Defend faith",
    destroy_rival: "Destroy rival",
    survive_economic_stress: "Survive economic stress",
  };

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
      this.revolts = [];
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
      this.characters = seed.characters.map((c) => this._hydrateCharacter(c, { isRuler: true, reignStart: 1 }));
      this.opinions = {};
      this.relationships = [];
      this.dynasties = [];
      this.houses = [];

      for (const f of seed.factions) {
        const ruler = this.characters.find((c) => c.faction === f.id);
        this.factionState[f.id] = {
          treasury: this.rng.int(400, 900),
          manpower: 0, maxManpower: 0,
          prestige: this.rng.int(20, 80),
          exhaustion: 0,
          internal: this._initialInternalState(f.id),
          succession: this._initialSuccessionState(f.id),
          economy: {
            warDebt: 0,
            foodStress: 0,
            tradeValue: 0,
            devastationLoss: 0,
            tributeDue: 0,
            lastDecision: null,
          },
          court: null,
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
          siege: null, instability: 0, revoltId: null, recentConquest: 0,
          society: this._initialProvinceSociety(p, pop),
        };
      }
      for (const f of seed.factions) this._refreshManpower(f.id, true);
      for (const r of seed.relations) this._setOpinion(r.a, r.b, r.score);
      this.claims = seed.claims.map((c) => ({ ...c }));
      this.mages = seed.mages.map((m) => ({ ...m, alive: true }));
      this._seedInitialRelationships(seed.relationships || []);
      this._syncFamilyLinks();
      this._refreshDynastyHouseRecords();
      this._refreshAllCourts();
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

    _characterAmbition(fid, role) {
      const f = this.faction(fid) || {};
      const text = `${role || ""} ${f.government || ""} ${f.goal || ""} ${f.pressure || ""}`.toLowerCase();
      if (/king|crown|ruler|speaker|queen|khan/.test(text)) return "protect dynasty";
      if (/captain|commander|war|banner|march|horse/.test(text)) return "win glory";
      if (/merchant|counting|ledger|trade|credit|sea/.test(text)) return "secure wealth";
      if (/priest|temple|faith|witness|hearth|sacred/.test(text)) return "defend faith";
      if (/charter|claim|restore|recognition/.test(text)) return "restore old claims";
      return this.rng.pick(AMBITION_TEMPLATES);
    }

    _characterFear(fid, role) {
      const f = this.faction(fid) || {};
      const text = `${role || ""} ${f.pressure || ""} ${f.identity || ""}`.toLowerCase();
      if (/debt|credit|ledger|merchant/.test(text)) return "poverty";
      if (/mage|magic/.test(text)) return "magical scandal";
      if (/succession|heir|dynasty|line/.test(text)) return "dynasty failure";
      if (/recognition|legitimacy|charter/.test(text)) return "losing legitimacy";
      if (/revolt|unrest|freehold/.test(text)) return "open revolt";
      return this.rng.pick(FEAR_TEMPLATES);
    }

    _hydrateCharacter(raw, opts) {
      const f = this.faction(raw.faction) || {};
      const age = raw.age || 0;
      const birthYear = raw.birthYear !== undefined ? raw.birthYear : this.seed.world.startYear - age;
      const traits = raw.traits || this._rollTraits();
      const ambition = raw.ambition || this._characterAmbition(raw.faction, raw.role);
      const fear = raw.fear || this._characterFear(raw.faction, raw.role);
      const family = this._normalizeFamily(raw, f, opts);
      const legitimacy = raw.legitimacy !== undefined
        ? raw.legitimacy
        : this._clampPolitics((opts && opts.isRuler ? 58 : 42) + (raw.prestige || 0) * 0.18 + (age >= 16 ? 8 : -10));
      return {
        ...raw,
        birthYear,
        deathYear: raw.deathYear || null,
        faith: raw.faith || f.religion || raw.religion || "",
        alive: raw.alive !== undefined ? raw.alive : true,
        isRuler: opts && opts.isRuler !== undefined ? opts.isRuler : !!raw.isRuler,
        traits,
        ambition,
        fear,
        loyalties: raw.loyalties || {
          faction: raw.faction,
          dynasty: family.dynasty,
          faith: f.religion || "",
        },
        family,
        father: family.father,
        mother: family.mother,
        dynasty: family.dynasty,
        house: family.house,
        stress: raw.stress !== undefined ? raw.stress : this._clampPolitics((raw.pressure || "").length / 3 + (opts && opts.isRuler ? 10 : 0)),
        health: raw.health !== undefined ? raw.health : this._clampPolitics(88 - Math.max(0, age - 45) * 1.2),
        wealth: raw.wealth !== undefined ? raw.wealth : this.rng.int(opts && opts.isRuler ? 120 : 20, opts && opts.isRuler ? 420 : 180),
        legitimacy,
        reputation: raw.reputation !== undefined ? raw.reputation : this._clampPolitics((raw.prestige || 0) + (opts && opts.isRuler ? 20 : 6)),
        prestige: raw.prestige !== undefined ? raw.prestige : this.rng.int(10, 60),
        kills: raw.kills || 0,
        reignStart: opts && opts.reignStart !== undefined ? opts.reignStart : raw.reignStart,
        memories: raw.memories || [],
        militaryRecord: {
          ...emptyMilitaryRecord(),
          ...(raw.militaryRecord || {}),
        },
      };
    }

    _houseName(faction) {
      const name = (faction && (faction.shortName || faction.name)) || "Unhoused";
      return name.replace(/^(Crown of|The|House of)\s+/i, "").trim() || name;
    }

    _slug(text) {
      return String(text || "unknown").toUpperCase().replace(/[^A-Z0-9]+/g, "_").replace(/^_+|_+$/g, "") || "UNKNOWN";
    }

    _dynastyId(name) { return `DYN_${this._slug(name)}`; }
    _houseId(name, dynastyName) { return `HOUSE_${this._slug(dynastyName)}_${this._slug(name)}`; }
    _cadetHouseName(character, reason) {
      const base = character.family?.house || character.house || this._dynastyName(character, this.faction(character.faction));
      const given = String(character.name || "").split(" ")[0] || "Cadet";
      const suffix = reason === "legitimised_bastard" ? "Legitimised" : reason === "exiled_prince" ? "Exile" : given;
      return `${base}-${suffix}`;
    }

    _dynastyName(raw, faction) {
      if (raw.dynasty) return raw.dynasty;
      if (raw.family && raw.family.dynasty) return raw.family.dynasty;
      const parts = (raw.name || "").split(" ").filter(Boolean);
      if (parts.length > 1) return parts.slice(1).join(" ");
      return this._houseName(faction);
    }

    _normalizeFamily(raw, faction, opts) {
      const base = { ...emptyFamily(), ...(raw.family || {}) };
      const father = raw.father !== undefined ? raw.father : base.father;
      const mother = raw.mother !== undefined ? raw.mother : base.mother;
      const parent = raw.parentId || father || mother || null;
      const dynasty = this._dynastyName(raw, faction);
      const house = raw.house || base.house || dynasty || this._houseName(faction);
      const dynastyId = raw.dynastyId || base.dynastyId || this._dynastyId(dynasty);
      const houseId = raw.houseId || base.houseId || this._houseId(house, dynasty);
      return {
        ...base,
        father: father || (parent && !mother ? parent : null),
        mother: mother || null,
        spouses: [...new Set([...(base.spouses || []), ...(raw.spouses || [])].filter(Boolean))],
        lovers: [...new Set([...(base.lovers || []), ...(raw.lovers || [])].filter(Boolean))],
        children: [...new Set([...(base.children || []), ...(raw.children || [])].filter(Boolean))],
        siblings: [...new Set([...(base.siblings || []), ...(raw.siblings || [])].filter(Boolean))],
        dynasty,
        dynastyId,
        house,
        houseId,
        branchType: raw.branchType || base.branchType || "main",
        branchFounder: raw.branchFounder !== undefined ? raw.branchFounder : (base.branchFounder || null),
        parentHouseId: raw.parentHouseId !== undefined ? raw.parentHouseId : (base.parentHouseId || null),
        cadetReason: raw.cadetReason || base.cadetReason || null,
        bastard: raw.bastard !== undefined ? !!raw.bastard : !!base.bastard,
        legitimised: raw.legitimised !== undefined ? !!raw.legitimised : !!base.legitimised,
        legitimacy: this._clampPolitics(raw.familyLegitimacy !== undefined ? raw.familyLegitimacy : base.legitimacy),
        inheritanceRank: raw.inheritanceRank !== undefined ? raw.inheritanceRank : base.inheritanceRank,
        claimStrength: this._clampPolitics(raw.claimStrength !== undefined ? raw.claimStrength : base.claimStrength),
      };
    }

    _legitimacyScore(character) {
      if (!character) return 0;
      const family = character.family || {};
      let score = character.legitimacy !== undefined ? character.legitimacy : 50;
      score += (family.legitimacy !== undefined ? family.legitimacy : 50) * 0.55 - 25;
      score += (family.claimStrength || 0) * 0.22;
      if (family.bastard && !family.legitimised) score -= 38;
      if (family.legitimised) score += 13;
      if (family.branchType === "cadet") score -= 4;
      return this._clampPolitics(score);
    }

    inheritanceScore(character) {
      if (!character) return -9999;
      const family = character.family || {};
      const rank = family.inheritanceRank !== null && family.inheritanceRank !== undefined
        ? family.inheritanceRank
        : 99;
      return (120 - rank * 16) +
        this._legitimacyScore(character) * 0.72 +
        Math.min(18, character.age || 0) +
        Math.min(24, (character.prestige || 0) / 4);
    }

    factionSupportForCharacter(character) {
      if (!character) return 0;
      const st = this.factionState[character.faction] || {};
      const internal = st.internal || {};
      const family = character.family || {};
      let support = this._legitimacyScore(character) * 0.62 +
        (character.reputation || 0) * 0.18 +
        (character.prestige || 0) * 0.12 +
        Math.max(0, 100 - (internal.courtTension || 0)) * 0.08 +
        Math.max(0, internal.nobleLoyalty || 0) * 0.12;
      if (family.bastard && !family.legitimised) support -= 20;
      if (family.branchType === "cadet") support -= 3;
      return this._clampPolitics(support);
    }

    legitimizeBastard(characterId, reason) {
      const c = this.character(characterId);
      if (!c || !c.family) return null;
      c.family.bastard = true;
      c.family.legitimised = true;
      c.family.legitimacy = Math.max(c.family.legitimacy || 0, 52);
      c.legitimacy = Math.max(c.legitimacy || 0, 48);
      c.family.claimStrength = Math.max(c.family.claimStrength || 0, 48);
      const branch = this.formCadetBranch(c.id, reason || "legitimised_bastard");
      this.log(2, "succession",
        `${c.name} is legitimised; the court now treats their branch as a lawful cadet line.`,
        { faction: c.faction, character: c.id });
      return branch;
    }

    formCadetBranch(characterId, reason) {
      const founder = this.character(characterId);
      if (!founder || !founder.family) return null;
      const oldHouseId = founder.family.houseId || this._houseId(founder.family.house, founder.family.dynasty);
      const dynastyName = founder.family.dynasty || founder.dynasty || this._dynastyName(founder, this.faction(founder.faction));
      const newHouse = this._cadetHouseName(founder, reason || "cadet_branch");
      const newHouseId = this._houseId(newHouse, dynastyName);
      const descendants = new Set([founder.id]);
      const collect = (id) => {
        for (const child of this.childrenOf(id)) {
          if (descendants.has(child.id)) continue;
          descendants.add(child.id);
          collect(child.id);
        }
      };
      collect(founder.id);
      for (const id of descendants) {
        const c = this.character(id);
        if (!c || !c.family) continue;
        c.family.dynasty = dynastyName;
        c.family.dynastyId = this._dynastyId(dynastyName);
        c.family.house = newHouse;
        c.family.houseId = newHouseId;
        c.family.branchType = "cadet";
        c.family.branchFounder = founder.id;
        c.family.parentHouseId = oldHouseId;
        c.family.cadetReason = reason || "cadet_branch";
        c.house = newHouse;
        c.dynasty = dynastyName;
      }
      this._refreshDynastyHouseRecords();
      return {
        id: newHouseId,
        name: newHouse,
        dynasty: this._dynastyId(dynastyName),
        founder: founder.id,
        parentHouseId: oldHouseId,
        reason: reason || "cadet_branch",
        members: [...descendants],
      };
    }

    _ensureCharacterState(character, opts) {
      if (!character) return null;
      const hydrated = this._hydrateCharacter(character, opts || {});
      Object.assign(character, hydrated);
      return character;
    }

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

    _relationshipKey(from, to, type) { return `${from}|${to}|${type}`; }

    _addRelationship(from, to, type, strength, source, opts) {
      if (!from || !to || from === to || !VALID_RELATIONSHIP_TYPES.has(type)) return null;
      if (!this.character(from) || !this.character(to)) return null;
      const clamped = Math.max(1, Math.min(100, Math.round(strength || 50)));
      let rel = this.relationships.find((r) => r.from === from && r.to === to && r.type === type);
      if (rel) {
        rel.strength = Math.max(rel.strength || 0, clamped);
        if (source && !rel.source) rel.source = source;
      } else {
        rel = {
          id: uid("rel"),
          from,
          to,
          type,
          strength: clamped,
          source: source || "emergent relationship",
          started: this.formatDate(),
        };
        this.relationships.push(rel);
      }
      if (!opts || opts.reciprocal !== false) {
        const reciprocal = (opts && opts.reciprocalType) || RECIPROCAL_RELATIONSHIP[type];
        if (reciprocal) this._addRelationship(to, from, reciprocal, clamped, source, { reciprocal: false });
      }
      if ((!opts || opts.refresh !== false) && !this._syncingFamilies && this.dynasties && this.houses) {
        this._refreshDynastyHouseRecords();
      }
      return rel;
    }

    _seedInitialRelationships(seedRelationships) {
      for (const rel of seedRelationships) {
        this._addRelationship(rel.from, rel.to, rel.type, rel.strength || 50, rel.source || "seed data", {
          reciprocal: rel.reciprocal !== false,
          reciprocalType: rel.reciprocalType,
        });
      }
      for (const c of this.characters) {
        if (c.parentId) this._addRelationship(c.parentId, c.id, "parent", 90, "family line");
      }
      for (const r of this.seed.relations) {
        const a = this.rulerOf(r.a), b = this.rulerOf(r.b);
        if (!a || !b) continue;
        if (r.score <= -55) this._addRelationship(a.id, b.id, "enemy", Math.min(100, Math.abs(r.score) + 25), r.tension || "realm enmity");
        else if (r.score <= -25) this._addRelationship(a.id, b.id, "rival", Math.min(100, Math.abs(r.score) + 20), r.tension || "realm rivalry");
        else if (r.score >= 30) this._addRelationship(a.id, b.id, "friend", Math.min(100, r.score + 20), r.tension || "realm friendship");
      }
    }

    _parentIds(character) {
      const family = character.family || {};
      return [...new Set([character.parentId, family.father, family.mother].filter(Boolean))];
    }

    _syncFamilyLinks() {
      this._syncingFamilies = true;
      for (const c of this.characters) {
        c.family = { ...emptyFamily(), ...(c.family || {}) };
        c.family.children = [...new Set(c.family.children || [])].filter((id) => this.character(id));
        c.family.siblings = [...new Set(c.family.siblings || [])].filter((id) => this.character(id));
        c.family.spouses = [...new Set(c.family.spouses || [])].filter((id) => this.character(id));
        c.family.lovers = [...new Set(c.family.lovers || [])].filter((id) => this.character(id));
      }
      for (const child of this.characters) {
        for (const parentId of this._parentIds(child)) {
          const parent = this.character(parentId);
          if (!parent) continue;
          parent.family = { ...emptyFamily(), ...(parent.family || {}) };
          if (!parent.family.children.includes(child.id)) parent.family.children.push(child.id);
          if (!this.relationshipBetween(parent.id, child.id, "parent")) {
            this._addRelationship(parent.id, child.id, "parent", 90, "family line");
          }
        }
      }
      for (const c of this.characters) {
        const siblings = this.characters
          .filter((other) => other.id !== c.id && this._parentIds(c).some((id) => this._parentIds(other).includes(id)))
          .map((other) => other.id);
        c.family.siblings = [...new Set([...(c.family.siblings || []), ...siblings])];
      }
      this._syncingFamilies = false;
    }

    _selectHouseHead(members) {
      const living = members.filter((c) => c.alive);
      const pool = living.length ? living : members;
      return pool
        .slice()
        .sort((a, b) =>
          (b.isRuler ? 10000 : 0) + (b.prestige || 0) + (b.reputation || 0) -
          ((a.isRuler ? 10000 : 0) + (a.prestige || 0) + (a.reputation || 0)))[0] || null;
    }

    _homeProvinceForMembers(members) {
      const ruler = members.find((c) => c.isRuler && this.capital(c.faction));
      if (ruler) return this.capital(ruler.faction).id;
      const member = members.find((c) => this.capital(c.faction));
      return member ? this.capital(member.faction).id : null;
    }

    _refreshDynastyHouseRecords() {
      this._syncFamilyLinks();
      const dynasties = new Map();
      const houses = new Map();
      for (const c of this.characters) {
        c.family = { ...emptyFamily(), ...(c.family || {}) };
        const dynastyName = c.family.dynasty || c.dynasty || "common line";
        const houseName = c.family.house || c.house || dynastyName;
        const dynastyId = this._dynastyId(dynastyName);
        const houseId = this._houseId(houseName, dynastyName);
        c.family.dynastyId = dynastyId;
        c.family.houseId = houseId;
        c.dynasty = dynastyName;
        c.house = houseName;
        if (!dynasties.has(dynastyId)) {
          dynasties.set(dynastyId, {
            id: dynastyId,
            name: dynastyName,
            founder: c.id,
            culture: c.culture,
            faith: c.faith,
            homeProvince: null,
            prestige: 0,
            renown: 0,
            famousAncestors: [],
            rivals: [],
            alliances: [],
            bloodlineTraits: [],
            cadetBranches: [],
            houses: [],
            members: [],
          });
        }
        if (!houses.has(houseId)) {
          houses.set(houseId, {
            id: houseId,
            dynasty: dynastyId,
            name: houseName,
            founder: c.id,
            head: c.id,
            homeProvince: null,
            branchType: c.family.branchType || "main",
            branchFounder: c.family.branchFounder || null,
            parentHouseId: c.family.parentHouseId || null,
            cadetReason: c.family.cadetReason || null,
            legitimacy: 50,
            prestige: 0,
            livingMembers: [],
            members: [],
          });
        }
        dynasties.get(dynastyId).members.push(c.id);
        houses.get(houseId).members.push(c.id);
      }

      for (const dynasty of dynasties.values()) {
        const members = dynasty.members.map((id) => this.character(id)).filter(Boolean);
        const founder = members.slice().sort((a, b) => b.age - a.age)[0];
        const head = this._selectHouseHead(members);
        dynasty.founder = founder ? founder.id : dynasty.founder;
        dynasty.head = head ? head.id : dynasty.founder;
        dynasty.homeProvince = this._homeProvinceForMembers(members);
        dynasty.prestige = Math.round(members.reduce((sum, c) => sum + (c.prestige || 0), 0));
        dynasty.renown = Math.round(dynasty.prestige / 4 + members.filter((c) => c.isRuler).length * 12);
        dynasty.famousAncestors = members
          .filter((c) => !c.alive || (c.prestige || 0) >= 80 || (c.kills || 0) >= 500)
          .sort((a, b) => (b.prestige || 0) + (b.kills || 0) * 0.01 - ((a.prestige || 0) + (a.kills || 0) * 0.01))
          .slice(0, 6)
          .map((c) => c.id);
        dynasty.houses = [...new Set(members.map((c) => c.family.houseId).filter(Boolean))];
        dynasty.cadetBranches = dynasty.houses
          .map((houseId) => houses.get(houseId))
          .filter((house) => house && house.branchType === "cadet")
          .map((house) => ({
            house: house.id,
            name: house.name,
            founder: house.branchFounder || house.founder,
            parentHouseId: house.parentHouseId || null,
            reason: house.cadetReason || "cadet_branch",
          }));
        dynasty.bloodlineTraits = [...new Set(members.flatMap((c) => (c.traits || []).map((t) => t.label)).slice(0, 6))];
        const headChar = this.character(dynasty.head);
        dynasty.rivals = [];
        dynasty.alliances = [];
        if (headChar) {
          for (const rel of this.relationships.filter((r) => r.from === headChar.id)) {
            const other = this.character(rel.to);
            if (!other || !other.family || other.family.dynastyId === dynasty.id) continue;
            if (["rival", "enemy", "betrayer"].includes(rel.type)) dynasty.rivals.push(other.family.dynastyId);
            if (["friend", "rescuer", "spouse", "lover"].includes(rel.type)) dynasty.alliances.push(other.family.dynastyId);
          }
        }
        dynasty.rivals = [...new Set(dynasty.rivals)].slice(0, 6);
        dynasty.alliances = [...new Set(dynasty.alliances)].slice(0, 6);
      }

      for (const house of houses.values()) {
        const members = house.members.map((id) => this.character(id)).filter(Boolean);
        const founder = members.slice().sort((a, b) => b.age - a.age)[0];
        const head = this._selectHouseHead(members);
        house.founder = founder ? founder.id : house.founder;
        house.head = head ? head.id : house.founder;
        house.homeProvince = this._homeProvinceForMembers(members);
        const branchSource = members.find((c) => c.family?.branchType === "cadet");
        house.branchType = branchSource ? "cadet" : "main";
        house.branchFounder = branchSource ? (branchSource.family.branchFounder || branchSource.id) : null;
        house.parentHouseId = branchSource ? (branchSource.family.parentHouseId || null) : null;
        house.cadetReason = branchSource ? (branchSource.family.cadetReason || "cadet_branch") : null;
        house.livingMembers = members.filter((c) => c.alive).map((c) => c.id);
        house.legitimacy = this._clampPolitics(members.reduce((sum, c) => sum + (c.family?.legitimacy || 0), 0) / Math.max(1, members.length));
        house.prestige = Math.round(members.reduce((sum, c) => sum + (c.prestige || 0), 0));
      }

      this.dynasties = [...dynasties.values()];
      this.houses = [...houses.values()];
    }

    dynasty(id) { return this.dynasties.find((d) => d.id === id); }
    house(id) { return this.houses.find((h) => h.id === id); }

    dynastySummaryForFaction(fid) {
      this._refreshDynastyHouseRecords();
      const ruler = this.rulerOf(fid);
      if (!ruler || !ruler.family) return null;
      const dynasty = this.dynasty(ruler.family.dynastyId);
      const house = this.house(ruler.family.houseId);
      if (!dynasty || !house) return null;
      const claims = this.claims
        .filter((claim) => this.characters.some((c) => c.family?.dynastyId === dynasty.id && c.faction === claim.claimant))
        .slice(0, 8);
      return {
        dynasty,
        house,
        founder: this.character(dynasty.founder),
        head: this.character(house.head),
        members: dynasty.members.map((id) => this.character(id)).filter(Boolean),
        claims,
        rivals: dynasty.rivals.map((id) => this.dynasty(id)).filter(Boolean),
      };
    }

    closeFamilyOf(characterId) {
      const c = this.character(characterId);
      if (!c) return { parents: [], children: [], siblings: [], spouses: [], lovers: [] };
      const pick = (ids) => [...new Set(ids || [])].map((id) => this.character(id)).filter(Boolean);
      return {
        parents: pick(this._parentIds(c)),
        children: pick(c.family.children),
        siblings: pick(c.family.siblings),
        spouses: pick(c.family.spouses),
        lovers: pick(c.family.lovers),
      };
    }

    relationshipsOf(characterId, opts) {
      const options = opts || {};
      return this.relationships
        .filter((r) => r.from === characterId || (!options.outgoingOnly && r.to === characterId))
        .sort((a, b) => (b.strength || 0) - (a.strength || 0));
    }

    relationshipBetween(from, to, type) {
      return this.relationships.find((r) => r.from === from && r.to === to && (!type || r.type === type));
    }

    _relationshipDiplomacyBias(a, b) {
      const ar = this.rulerOf(a), br = this.rulerOf(b);
      if (!ar || !br) return 0;
      let bias = 0;
      for (const rel of this.relationships) {
        if (rel.from !== ar.id || rel.to !== br.id) continue;
        if (rel.type === "friend" || rel.type === "rescuer") bias += Math.round((rel.strength || 50) / 8);
        if (rel.type === "rival" || rel.type === "betrayer") bias -= Math.round((rel.strength || 50) / 7);
        if (rel.type === "enemy") bias -= Math.round((rel.strength || 50) / 5);
      }
      return Math.max(-28, Math.min(20, bias));
    }

    relationshipPressure(characterId) {
      let loyalty = 0, succession = 0, diplomacy = 0;
      for (const rel of this.relationships.filter((r) => r.from === characterId)) {
        const s = rel.strength || 50;
        if (["parent", "child", "friend", "mentor", "patron", "rescuer"].includes(rel.type)) loyalty += s / 20;
        if (["rival", "enemy", "betrayer", "hostage"].includes(rel.type)) loyalty -= s / 18;
        if (["parent", "child", "spouse"].includes(rel.type)) succession += s / 18;
        if (["rival", "enemy", "betrayer"].includes(rel.type)) succession -= s / 22;
        if (["friend", "rival", "enemy", "rescuer", "betrayer"].includes(rel.type)) diplomacy += rel.type === "friend" || rel.type === "rescuer" ? s / 18 : -s / 18;
      }
      return {
        loyalty: Math.round(loyalty),
        succession: Math.round(succession),
        diplomacy: Math.round(diplomacy),
      };
    }

    _ensureMilitaryRecord(character) {
      if (!character) return emptyMilitaryRecord();
      character.militaryRecord = {
        ...emptyMilitaryRecord(),
        ...(character.militaryRecord || {}),
      };
      for (const field of ["notableVictories", "notableDefeats"]) {
        if (!Array.isArray(character.militaryRecord[field])) character.militaryRecord[field] = [];
      }
      return character.militaryRecord;
    }

    _addMemory(characterId, type, text, refs, impact) {
      const c = this.character(characterId);
      if (!c || !VALID_MEMORY_TYPES.has(type)) return null;
      if (!Array.isArray(c.memories)) c.memories = [];
      const memory = {
        id: uid("mem"),
        type,
        text,
        date: this.formatDate(),
        day: this.day,
        refs: refs || {},
      };
      c.memories.unshift(memory);
      if (c.memories.length > 16) c.memories.length = 16;

      const effect = impact || {};
      if (effect.reputation) c.reputation = this._clampPolitics((c.reputation || 0) + effect.reputation);
      if (effect.prestige) c.prestige = Math.max(0, (c.prestige || 0) + effect.prestige);
      if (effect.stress) c.stress = this._clampPolitics((c.stress || 0) + effect.stress);
      if (effect.health) c.health = this._clampPolitics((c.health || 0) + effect.health);
      if (effect.grudgeAgainst && this.character(effect.grudgeAgainst)) {
        this._addRelationship(c.id, effect.grudgeAgainst, effect.grudgeType || "rival", effect.grudgeStrength || 45, text);
      }
      return memory;
    }

    _recordBattleMemory(army, outcome, battleName, losses, enemyCommanderId, refs) {
      const c = this.character(army.commanderId);
      if (!c) return;
      const record = this._ensureMilitaryRecord(c);
      record.battlesFought += 1;
      if (outcome === "win") {
        record.battlesWon += 1;
        record.notableVictories.unshift({ name: battleName, date: this.formatDate(), losses });
        record.notableVictories = record.notableVictories.slice(0, 5);
        this._addMemory(c.id, "battle victory", `${battleName}: victory with ${losses.toLocaleString()} enemy casualties.`, refs, {
          reputation: 4, prestige: 6, stress: 2,
        });
      } else {
        record.battlesLost += 1;
        record.notableDefeats.unshift({ name: battleName, date: this.formatDate(), losses });
        record.notableDefeats = record.notableDefeats.slice(0, 5);
        this._addMemory(c.id, "battle defeat", `${battleName}: defeat after losing ${losses.toLocaleString()} soldiers.`, refs, {
          reputation: -3, stress: 7, grudgeAgainst: enemyCommanderId, grudgeType: "rival", grudgeStrength: 48,
        });
      }
    }

    _recordWound(characterId, text, refs) {
      const c = this.character(characterId);
      if (!c) return;
      const record = this._ensureMilitaryRecord(c);
      record.wounds += 1;
      this._addMemory(characterId, "wound", text, refs, { health: -8, stress: 5, reputation: 1 });
    }

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

    officeLabel(office) {
      return COURT_OFFICE_LABELS[office] || String(office || "").replace(/_/g, " ");
    }

    courtOf(fid) {
      const st = this.factionState[fid];
      if (!st) return null;
      if (!st.court) this._refreshCourt(fid);
      return st.court;
    }

    characterOffices(characterId) {
      const offices = [];
      for (const [fid, st] of Object.entries(this.factionState)) {
        const court = st.court || this._refreshCourt(fid);
        for (const [office, assignment] of Object.entries(court.offices || {})) {
          if (assignment && assignment.character === characterId) {
            offices.push({ faction: fid, office, label: this.officeLabel(office), effectiveness: assignment.effectiveness || 0 });
          }
        }
      }
      return offices;
    }

    _officeCandidateScore(character, office, fid) {
      if (!character || !character.alive || character.faction !== fid) return -9999;
      let score = (character.prestige || 0) * 0.35 + (character.reputation || 0) * 0.45 +
        (character.legitimacy || 0) * 0.12 + Math.min(30, character.age || 0);
      const traits = new Set((character.traits || []).map((t) => t.id));
      const role = String(character.role || "").toLowerCase();
      if (character.isRuler) score += office === "ruler" ? 10000 : -25;
      if (office === "heir") score += this.inheritanceScore(character) * 0.35;
      if (office === "marshal" || office === "captain_of_guard") score += (character.kills || 0) * 0.018 + (traits.has("bold") ? 14 : 0) + (traits.has("ironhanded") ? 12 : 0);
      if (office === "steward") score += (traits.has("greedy") ? 12 : 0) + (/merchant|steward|ledger|trade|governor/.test(role) ? 14 : 0);
      if (office === "chancellor") score += (traits.has("just") ? 12 : 0) + (traits.has("patient") ? 10 : 0);
      if (office === "spymaster") score += (traits.has("cunning") ? 18 : 0) + (traits.has("patient") ? 5 : 0);
      if (office === "high_priest") score += (traits.has("pious") ? 18 : 0) + (/priest|faith|temple/.test(role) ? 20 : 0);
      if (office === "court_mage") score += this.mages.some((m) => m.alive && m.character === character.id) ? 100 : -20;
      if (office === "governor") score += (/governor|lord|captain|ruler/.test(role) ? 12 : 0) + (traits.has("just") ? 7 : 0);
      if (office === "regent") score += (character.age >= 30 ? 12 : -6) + (traits.has("patient") ? 10 : 0) + (traits.has("just") ? 8 : 0);
      return score;
    }

    _officeEffectiveness(character, office, fid) {
      if (!character) return 0;
      const base = 35 + (character.reputation || 0) * 0.25 + (character.prestige || 0) * 0.18 + (character.legitimacy || 0) * 0.12;
      return this._clampPolitics(base + Math.max(0, this._officeCandidateScore(character, office, fid)) * 0.12);
    }

    _assignOffice(fid, office, used) {
      const st = this.factionState[fid];
      if (!st) return null;
      let holder = null;
      if (office === "ruler") holder = this.rulerOf(fid);
      else if (office === "heir") holder = this.heirOf(fid);
      else if (office === "court_mage") {
        const mage = this.mages.find((m) => m.alive && m.patron === fid && this.character(m.character));
        holder = mage ? this.character(mage.character) : null;
      } else {
        const pool = this.characters
          .filter((c) => c.alive && c.faction === fid && !used.has(c.id))
          .sort((a, b) => this._officeCandidateScore(b, office, fid) - this._officeCandidateScore(a, office, fid));
        holder = pool[0] || null;
      }
      if (!holder) return null;
      used.add(holder.id);
      return {
        office,
        label: this.officeLabel(office),
        character: holder.id,
        effectiveness: this._officeEffectiveness(holder, office, fid),
      };
    }

    _refreshCourt(fid) {
      const st = this.factionState[fid];
      if (!st) return null;
      const f = this.faction(fid) || {};
      const used = new Set();
      const offices = {};
      for (const office of COURT_OFFICES) offices[office] = this._assignOffice(fid, office, used);
      const filled = Object.values(offices).filter(Boolean);
      st.court = {
        faction: fid,
        name: `${f.shortName || f.name || fid} Court`,
        offices,
        filled: filled.length,
        stability: this._clampPolitics(
          42 + filled.reduce((sum, office) => sum + (office.effectiveness || 0), 0) / Math.max(1, filled.length) * 0.34 -
          ((st.internal && st.internal.courtTension) || 0) * 0.18
        ),
        lastRefresh: this.formatDate(),
      };
      return st.court;
    }

    _refreshAllCourts() {
      for (const f of this.seed.factions) this._refreshCourt(f.id);
    }

    courtEffects(fid) {
      const court = this.courtOf(fid);
      const office = (id) => court && court.offices && court.offices[id] ? court.offices[id].effectiveness || 0 : 0;
      return {
        diplomacy: office("chancellor"),
        war: Math.max(office("marshal"), office("captain_of_guard") * 0.72),
        economy: Math.max(office("steward"), office("governor") * 0.65),
        intrigue: office("spymaster"),
        faith: office("high_priest"),
        magic: office("court_mage"),
        guard: office("captain_of_guard"),
        governance: office("governor"),
        regency: office("regent"),
        stability: court ? court.stability || 0 : 0,
      };
    }

    _clampPolitics(value) {
      return Math.max(0, Math.min(100, Math.round(value)));
    }

    socialGroupLabel(group) {
      return SOCIAL_GROUP_LABELS[group] || String(group || "").replace(/_/g, " ");
    }

    _initialProvinceSociety(province, pop) {
      const text = `${province.terrain || ""} ${province.terrainFeature || ""} ${province.resource || ""}`.toLowerCase();
      const shares = {
        nobles: 0.035,
        clergy: /temple|sacred|faith|oath/.test(text) ? 0.055 : 0.03,
        merchants: (province.port || province.roads >= 3 || /market|canal|road|port|salt/.test(text)) ? 0.085 : 0.035,
        peasants: /farmland|grain|fertile|lowland/.test(text) ? 0.58 : 0.44,
        craftsmen: /city|charter|mine|iron|canal|port/.test(text) ? 0.105 : 0.055,
        soldiers: 0.035 + (province.fort || 0) * 0.012,
        mages: province.manaSite ? 0.012 + province.manaSite * 0.004 : 0.003,
        scholars: /charter|city|temple|ledger/.test(text) ? 0.035 : 0.012,
        minorities: /mixed|frontier|port|city/.test(text) ? 0.07 : 0.035,
        tribes: /steppe|dryland|oasis|frontier|marsh|forest/.test(text) ? 0.09 : 0.018,
        foreign_settlers: /port|road|canal|frontier|city/.test(text) ? 0.045 : 0.018,
        refugees: province.value < 45 ? 0.035 : 0.014,
        urban_poor: /city|port|charter|canal/.test(text) ? 0.075 : 0.025,
      };
      const totalShare = Object.values(shares).reduce((sum, n) => sum + n, 0);
      const society = {};
      for (const group of SOCIAL_GROUPS) {
        const size = Math.max(0, Math.round(pop * shares[group] / totalShare));
        const elite = ["nobles", "clergy", "merchants", "scholars", "mages"].includes(group);
        const vulnerable = ["peasants", "refugees", "urban_poor", "minorities", "foreign_settlers"].includes(group);
        society[group] = {
          size,
          loyalty: this._clampPolitics(58 + (elite ? 6 : 0) - (vulnerable ? 5 : 0) + (province.value - 55) * 0.08),
          unrest: this._clampPolitics(18 + (vulnerable ? 10 : 0) + (/dryland|marsh|steppe/.test(text) ? 5 : 0)),
          needs: this._societyNeedsFor(group, province),
          wealth: this._clampPolitics((elite ? 62 : 32) + province.value * 0.18 + (group === "refugees" || group === "urban_poor" ? -18 : 0)),
          influence: this._clampPolitics((elite ? 42 : 18) + size / Math.max(1, pop) * 90 + (group === "soldiers" ? province.fort * 4 : 0)),
        };
      }
      return society;
    }

    _societyNeedsFor(group, province) {
      const needs = {
        nobles: "privilege and security",
        clergy: "temple standing and orthodoxy",
        merchants: "safe roads and fair tolls",
        peasants: "food, seed and low taxes",
        craftsmen: "markets and materials",
        soldiers: "pay and honour",
        mages: "legal protection and sites",
        scholars: "patrons and archives",
        minorities: "protection from assimilation",
        tribes: "autonomy and grazing rights",
        foreign_settlers: "charters and protection",
        refugees: "food and shelter",
        urban_poor: "bread and work",
      };
      return needs[group] || "stability";
    }

    societyOf(pid) {
      const st = this.provinceState[pid];
      if (!st) return null;
      if (!st.society) st.society = this._initialProvinceSociety(this.province(pid), st.pop || 0);
      return st.society;
    }

    societyEffects(pid) {
      const society = this.societyOf(pid);
      const st = this.provinceState[pid];
      if (!society || !st) return { tax: 1, recruitment: 1, unrest: 0, cultureTension: 0, faithTension: 0 };
      let taxWeight = 0, taxBase = 0, unrest = 0, recruitment = 0, cultureTension = 0, faithTension = 0;
      const total = Math.max(1, Object.values(society).reduce((sum, g) => sum + Math.max(0, g.size || 0), 0));
      for (const [group, g] of Object.entries(society)) {
        const share = Math.max(0, g.size || 0) / total;
        taxBase += share * (0.75 + (g.wealth || 0) / 115) * (0.72 + (g.loyalty || 0) / 175);
        unrest += share * (g.unrest || 0) * (1.2 - (g.loyalty || 0) / 120);
        if (["soldiers", "nobles", "tribes"].includes(group)) recruitment += share * (0.8 + (g.loyalty || 0) / 95 + (g.influence || 0) / 140);
        if (["minorities", "tribes", "foreign_settlers", "refugees"].includes(group)) cultureTension += share * (g.unrest || 0) * 0.75;
        if (["clergy", "mages", "minorities", "foreign_settlers"].includes(group)) faithTension += share * (100 - (g.loyalty || 0)) * 0.45;
        if (["merchants", "craftsmen"].includes(group)) taxWeight += share * (g.wealth || 0) / 100;
      }
      return {
        tax: Math.max(0.65, Math.min(1.35, taxBase + taxWeight * 0.12)),
        recruitment: Math.max(0.70, Math.min(1.35, 0.85 + recruitment)),
        unrest: this._clampPolitics(unrest + st.devastation * 0.12),
        cultureTension: this._clampPolitics(cultureTension),
        faithTension: this._clampPolitics(faithTension),
      };
    }

    provinceSocietySummary(pid) {
      const society = this.societyOf(pid);
      if (!society) return null;
      const effects = this.societyEffects(pid);
      const groups = Object.entries(society)
        .sort((a, b) => (b[1].influence || 0) + (b[1].size || 0) / 500 - ((a[1].influence || 0) + (a[1].size || 0) / 500));
      const dominant = groups.slice(0, 4).map(([id, g]) => ({
        id,
        label: this.socialGroupLabel(id),
        size: g.size,
        loyalty: g.loyalty,
        unrest: g.unrest,
        needs: g.needs,
        wealth: g.wealth,
        influence: g.influence,
      }));
      const mostRestive = groups.slice().sort((a, b) => (b[1].unrest || 0) - (a[1].unrest || 0))[0];
      return {
        dominant,
        effects,
        mostRestive: mostRestive ? { id: mostRestive[0], label: this.socialGroupLabel(mostRestive[0]), ...mostRestive[1] } : null,
      };
    }

    _initialInternalState(fid) {
      const f = this.faction(fid) || {};
      const text = `${f.government || ""} ${f.identity || ""} ${f.pressure || ""}`.toLowerCase();
      return {
        courtTension: /council|charter|league|confederation|board/.test(text) ? 24 : 16,
        successionTension: /crown|monarchy|khan|ring|hearth/.test(text) ? 22 : 14,
        armyInfluence: /khan|horse|banner|war|march|pass/.test(text) ? 36 : 20,
        taxBurden: /tax|debt|credit|toll|ledger|salt|canal/.test(text) ? 32 : 22,
        faithTension: /temple|faith|sacred|protector|witness|hearth|banner/.test(text) ? 14 : 22,
        cultureTension: f.species === "mixed" || f.species === "human_orc_mixed" ? 28 : 16,
        regionalAutonomy: /confederation|league|freehold|compact|forest/.test(text) ? 38 : 22,
        nobleLoyalty: /crown|duchy|court|khan|ring/.test(text) ? 58 : 50,
        merchantLoyalty: /merchant|trade|credit|ledger|sea|canal|road|salt/.test(text) ? 64 : 46,
        revoltRisk: 0,
        successionPressure: 0,
      };
    }

    _initialSuccessionState(fid) {
      const f = this.faction(fid) || {};
      const text = `${f.government || ""} ${f.identity || ""}`.toLowerCase();
      const law = /council|league|republic|confederation|board/.test(text)
        ? "council election"
        : /khan|ring|horse/.test(text)
          ? "acclaimed war heir"
          : /charter|compact|ledger|contract/.test(text)
            ? "charter succession"
            : "blood inheritance";
      return {
        law,
        heirLegitimacy: 55,
        regency: false,
        crisis: null,
        pretenders: [],
        lastTransition: null,
      };
    }

    _tierWeight(fid) {
      const faction = this.faction(fid);
      return Math.max(0.45, Math.min(1.5, faction && faction.tierWeight ? faction.tierWeight : 0.88));
    }

    _priorityBaseProfile(fid) {
      const f = this.faction(fid) || {};
      const text = `${f.government || ""} ${f.identity || ""} ${f.goal || ""} ${f.pressure || ""}`.toLowerCase();
      const weights = {
        expand_territory: 1.0,
        protect_homeland: 1.0,
        recover_old_claims: 1.0,
        raid_for_wealth: 0.65,
        avoid_war: 0.9,
        secure_trade_routes: 0.8,
        hold_mountain_passes: 0.65,
        control_ports: 0.55,
        defend_faith: 0.7,
        destroy_rival: 0.75,
        survive_economic_stress: 0.8,
      };
      const boost = (key, amount) => { weights[key] = (weights[key] || 0) + amount; };
      if (/merchant|trade|counting|credit|admiralty|naval|sea|convoy/.test(text)) {
        boost("secure_trade_routes", 1.15); boost("control_ports", 0.8); boost("survive_economic_stress", 0.35);
      }
      if (/canal|road|route|salt|well|caravan|toll/.test(text)) {
        boost("secure_trade_routes", 0.75); boost("expand_territory", 0.2);
      }
      if (/pass|mountain|highland|stone|vault|gear|hold/.test(text)) {
        boost("hold_mountain_passes", 1.2); boost("protect_homeland", 0.45);
      }
      if (/khan|horse|raid|pasture|ring|nomad/.test(text)) {
        boost("raid_for_wealth", 1.4); boost("avoid_war", -0.35); boost("expand_territory", 0.3);
      }
      if (/temple|faith|sacred|protector|witness|hearth|oath|banner/.test(text)) {
        boost("defend_faith", 1.0); boost("recover_old_claims", 0.25);
      }
      if (/charter|claim|legitimacy|restore|recognition|grievance/.test(text)) {
        boost("recover_old_claims", 0.9); boost("destroy_rival", 0.25);
      }
      if (/forest|refuge|freehold|council/.test(text)) {
        boost("protect_homeland", 0.7); boost("avoid_war", 0.25);
      }
      return weights;
    }

    aiPriorityScores(fid, opponentId) {
      const f = this.faction(fid);
      const st = this.factionState[fid];
      if (!f || !st) return [];
      const owned = this.ownedProvinces(fid);
      const wars = this.warsOf(fid);
      const claims = this.claims.filter((c) => c.claimant === fid && this.provinceState[c.target]);
      const ownedClaims = claims.filter((c) => this.provinceState[c.target].controller === fid);
      const externalClaims = claims.filter((c) => this.provinceState[c.target].controller !== fid);
      const contested = this.contestedProvinces(fid);
      const ports = owned.filter((p) => p.port > 0).length;
      const passes = owned.filter((p) => this._terrainFlags(p).mountain || /pass|gear|mountain|highland/i.test(p.terrain || "")).length;
      const tradeValue = owned.reduce((sum, p) => sum + p.roads + p.port * 2 + (p.value >= 80 ? 1 : 0), 0);
      const highValue = owned.reduce((sum, p) => sum + (p.value >= 85 ? 1 : 0), 0);
      const strongestNeighbour = opponentId
        ? opponentId
        : this.seed.factions
          .map((other) => other.id)
          .filter((other) => other !== fid)
          .sort((a, b) => this.armyStrength(b) + this.ownedProvinces(b).length * 500 - (this.armyStrength(a) + this.ownedProvinces(a).length * 500))[0];
      const op = strongestNeighbour ? this.opinion(fid, strongestNeighbour) : 0;
      const manpowerRatio = st.maxManpower ? st.manpower / st.maxManpower : 0;
      const deficit = this.monthlyIncome(fid) - this.monthlyUpkeep(fid) - Math.max(0, Math.round(st.treasury * 0.02));
      const internal = st.internal || this._initialInternalState(fid);
      const stress = Math.max(internal.courtTension || 0, internal.successionTension || 0, internal.regionalAutonomy || 0, internal.taxBurden || 0);
      const ruler = this.rulerOf(fid);
      const traitWar = this._traitFactor(fid, "war");
      const court = this.courtEffects(fid);
      const base = this._priorityBaseProfile(fid);
      const score = {
        expand_territory: base.expand_territory * 12 + highValue * 1.5 + Math.max(0, manpowerRatio - 0.45) * 12 - wars.length * 5 - st.exhaustion * 0.15,
        protect_homeland: base.protect_homeland * 12 + contested.length * 9 + Math.max(0, 0.45 - manpowerRatio) * 12 + st.exhaustion * 0.18 + owned.length * 0.8,
        recover_old_claims: base.recover_old_claims * 12 + externalClaims.length * 9 + externalClaims.reduce((sum, c) => sum + c.strength / 18, 0),
        raid_for_wealth: base.raid_for_wealth * 12 + Math.max(0, 180 - st.treasury) / 18 + (deficit < 0 ? 8 : 0) + Math.max(0, traitWar - 1) * 8,
        avoid_war: base.avoid_war * 12 + st.exhaustion * 0.35 + wars.length * 8 + Math.max(0, 0.35 - manpowerRatio) * 18 + (st.treasury < 120 ? 5 : 0),
        secure_trade_routes: base.secure_trade_routes * 12 + tradeValue * 1.4 + (deficit < 0 ? 3 : 0),
        hold_mountain_passes: base.hold_mountain_passes * 12 + passes * 8,
        control_ports: base.control_ports * 12 + ports * 10,
        defend_faith: base.defend_faith * 12 + this.seed.factions.filter((other) => other.id !== fid && other.religion === f.religion).length * 0.8,
        destroy_rival: base.destroy_rival * 12 + Math.max(0, -op) * 0.28 + Math.max(0, traitWar - 1) * 7,
        survive_economic_stress: base.survive_economic_stress * 12 + Math.max(0, 250 - st.treasury) / 16 + (deficit < 0 ? Math.min(14, -deficit / 12) : 0),
      };
      score.avoid_war += stress * 0.16;
      score.protect_homeland += (internal.regionalAutonomy || 0) * 0.08;
      score.survive_economic_stress += (internal.taxBurden || 0) * 0.12;
      score.raid_for_wealth += Math.max(0, 45 - (internal.merchantLoyalty || 50)) * 0.12;
      score.secure_trade_routes += (court.economy || 0) * 0.08;
      score.protect_homeland += (court.guard || 0) * 0.06;
      score.avoid_war += (court.diplomacy || 0) * 0.04;
      score.destroy_rival += (court.intrigue || 0) * 0.035;
      score.defend_faith += (court.faith || 0) * 0.06;
      score.expand_territory += (court.war || 0) * 0.035;
      if (ruler && ruler.traits.some((t) => t.id === "cautious" || t.id === "patient")) {
        score.avoid_war += 5; score.protect_homeland += 3;
      }
      if (ruler && ruler.traits.some((t) => t.id === "bold" || t.id === "vengeful" || t.id === "ironhanded")) {
        score.expand_territory += 4; score.destroy_rival += 4;
      }
      if (ownedClaims.length) score.protect_homeland += ownedClaims.length * 3;

      const reason = {
        expand_territory: owned.length ? `${owned.length} held province${owned.length === 1 ? "" : "s"} and usable manpower` : "needs land before it can expand",
        protect_homeland: contested.length ? `${contested.length} contested holding${contested.length === 1 ? "" : "s"}` : "holding the core together",
        recover_old_claims: externalClaims.length ? `${externalClaims.length} active external claim${externalClaims.length === 1 ? "" : "s"}` : "few active claims to press",
        raid_for_wealth: deficit < 0 ? "monthly costs outrun income" : "wealth can be taken faster than taxed",
        avoid_war: st.exhaustion > 10 ? `war exhaustion ${Math.round(st.exhaustion)}` : "avoiding unnecessary losses",
        secure_trade_routes: tradeValue ? `roads, ports and valuable provinces matter` : "trade network is thin",
        hold_mountain_passes: passes ? `${passes} pass or highland holding${passes === 1 ? "" : "s"}` : "few pass holdings",
        control_ports: ports ? `${ports} port holding${ports === 1 ? "" : "s"}` : "no controlled port",
        defend_faith: `faith ties through ${this.seed.religions[f.religion]?.name || f.religion}`,
        destroy_rival: strongestNeighbour ? `${this.faction(strongestNeighbour).shortName || this.faction(strongestNeighbour).name} is the sharpest rival` : "no clear rival",
        survive_economic_stress: st.treasury < 250 || deficit < 0 ? "treasury pressure is visible" : "keeping reserves healthy",
      };
      return Object.keys(AI_PRIORITY_INFO)
        .map((id) => ({ id, label: AI_PRIORITY_INFO[id], score: Math.max(0, Math.round(score[id])), reason: reason[id] }))
        .sort((a, b) => b.score - a.score || a.label.localeCompare(b.label));
    }

    aiPrioritySummary(fid, opponentId, count) {
      return this.aiPriorityScores(fid, opponentId)
        .slice(0, count || 3)
        .map((p) => `${p.label} (${p.reason})`)
        .join("; ");
    }

    _priorityWarMultiplier(attacker, defender, claim, isRaid) {
      const priorities = Object.fromEntries(this.aiPriorityScores(attacker, defender).map((p) => [p.id, p.score]));
      const internal = this.factionState[attacker] && this.factionState[attacker].internal;
      let m = 1;
      if (claim) m *= 1 + Math.min(0.55, (priorities.recover_old_claims || 0) / 80);
      if (isRaid) m *= 1 + Math.min(0.45, (priorities.raid_for_wealth || 0) / 90);
      m *= 1 + Math.min(0.25, (priorities.expand_territory || 0) / 180);
      m *= 1 + Math.min(0.2, (priorities.destroy_rival || 0) / 200);
      m *= 1 - Math.min(0.55, (priorities.avoid_war || 0) / 110);
      if (internal) {
        m *= 1 - Math.min(0.25, this.internalInstability(attacker) / 260);
        if ((internal.armyInfluence || 0) > 55) m *= 1.08;
      }
      return Math.max(0.35, Math.min(1.65, m));
    }

    characterDriveProfile(character, context) {
      if (!character) {
        return {
          war: 1, caution: 1, economy: 1, court: 1,
          summary: "No clear personal drive is shaping decisions.",
        };
      }
      const ctx = context || {};
      let war = 1, caution = 1, economy = 1, court = 1;
      const reasons = [];
      const push = (text) => { if (text) reasons.push(text); };

      switch (character.ambition) {
        case "become ruler":
          war *= 1.08; court *= 1.18; push("ambition to rule raises court pressure"); break;
        case "protect dynasty":
          caution *= 1.12; court *= 1.08; push("dynastic duty favors caution"); break;
        case "win glory":
          war *= 1.24; caution *= 0.88; push("glory hunger favors bold war"); break;
        case "secure wealth":
          economy *= 1.22; if (ctx.isRaid) war *= 1.15; push("wealth ambition favors raids and reserves"); break;
        case "defend faith":
          if (ctx.faithConflict) war *= 1.16;
          court *= 1.06; push(ctx.faithConflict ? "faith rivalry sharpens war appetite" : "faith duty weighs on the court"); break;
        case "restore old claims":
          if (ctx.claim) war *= 1.28;
          else war *= 1.08;
          push(ctx.claim ? "old claims make war more tempting" : "old claims keep grievance alive"); break;
        case "keep peace":
          war *= 0.68; caution *= 1.24; push("peacekeeping restrains war"); break;
        case "master the court":
          court *= 1.22; caution *= 1.08; push("court mastery turns inward"); break;
      }

      switch (character.fear) {
        case "dying forgotten":
          war *= 1.10; push("fear of being forgotten rewards public victories"); break;
        case "losing legitimacy":
          court *= 1.16; if (ctx.claim) war *= 1.06; push("legitimacy fear makes claims politically useful"); break;
        case "court betrayal":
          caution *= 1.14; court *= 1.12; push("betrayal fear makes the court brittle"); break;
        case "dynasty failure":
          caution *= 1.12; court *= 1.16; push("dynasty fear protects heirs and succession"); break;
        case "poverty":
          economy *= 1.2; if (ctx.treasuryLow || ctx.isRaid) war *= 1.08; push("poverty fear prizes money and plunder"); break;
        case "magical scandal":
          caution *= 1.08; court *= 1.08; push("magical scandal fear avoids risky displays"); break;
        case "foreign conquest":
          caution *= 1.2; war *= 0.9; push("fear of conquest makes offensive war harder to justify"); break;
        case "open revolt":
          caution *= 1.18; if (ctx.revoltRiskHigh) war *= 0.78; push("revolt fear pulls attention home"); break;
      }

      if ((character.stress || 0) >= 70) { war *= 0.9; caution *= 1.12; push("high stress encourages caution"); }
      if ((character.reputation || 0) < 30 && character.ambition === "win glory") {
        war *= 1.08; push("poor reputation makes glory urgent");
      }

      return {
        war: Math.max(0.45, Math.min(1.55, war)),
        caution: Math.max(0.65, Math.min(1.45, caution)),
        economy: Math.max(0.75, Math.min(1.45, economy)),
        court: Math.max(0.75, Math.min(1.45, court)),
        summary: reasons.slice(0, 2).join("; ") || "ambition and fear are steady for now",
      };
    }

    _rulerWarDriveMultiplier(attacker, defender, claim, isRaid) {
      const ruler = this.rulerOf(attacker);
      const st = this.factionState[attacker];
      const defenderFaction = this.faction(defender);
      const attackerFaction = this.faction(attacker);
      const profile = this.characterDriveProfile(ruler, {
        claim,
        isRaid,
        treasuryLow: st && st.treasury < 160,
        revoltRiskHigh: st && st.internal && st.internal.revoltRisk >= 45,
        faithConflict: attackerFaction && defenderFaction && attackerFaction.religion !== defenderFaction.religion,
      });
      const cautionDrag = 1 - Math.min(0.32, Math.max(0, profile.caution - 1) * 0.55);
      const economyPush = isRaid ? 1 + Math.min(0.22, Math.max(0, profile.economy - 1) * 0.5) : 1;
      return Math.max(0.45, Math.min(1.5, profile.war * cautionDrag * economyPush));
    }

    _warDriveText(attacker, defender, claim, isRaid) {
      const ruler = this.rulerOf(attacker);
      if (!ruler) return "";
      const st = this.factionState[attacker];
      const attackerFaction = this.faction(attacker);
      const defenderFaction = this.faction(defender);
      const profile = this.characterDriveProfile(ruler, {
        claim,
        isRaid,
        treasuryLow: st && st.treasury < 160,
        revoltRiskHigh: st && st.internal && st.internal.revoltRisk >= 45,
        faithConflict: attackerFaction && defenderFaction && attackerFaction.religion !== defenderFaction.religion,
      });
      return ` ${ruler.name}'s ambition (${ruler.ambition}) and fear (${ruler.fear}) matter here: ${profile.summary}.`;
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
      let baseBeforeDevastation = 0;
      for (const p of this.ownedProvinces(fid)) {
        const st = this.provinceState[p.id];
        if (st.occupier) continue;                      // occupied land pays nothing
        const base = (st.pop / 90) * (1 + p.roads * 0.15);
        baseBeforeDevastation += base;
        income += base * (1 - st.devastation / 120);
        income += p.port * 14;
      }
      const internal = this.factionState[fid] && this.factionState[fid].internal;
      if (internal) {
        const taxMod = 1 + (internal.taxBurden - 25) / 190;
        const loyaltyMod = 1 - Math.max(0, 45 - internal.merchantLoyalty) / 95;
        income *= Math.max(0.68, Math.min(1.28, taxMod * loyaltyMod));
      }
      const court = this.courtEffects(fid);
      income *= 1 + Math.min(0.14, (court.economy || 0) / 760);
      return Math.round(income);
    }

    tradeValue(fid) {
      return this.ownedProvinces(fid).reduce((sum, p) => {
        const river = (this.seed.riverFeatures || {})[p.id];
        const riverTrade = river && river.riverTradeValue ? river.riverTradeValue : 0;
        return sum + p.roads * 8 + p.port * 18 + p.value * 0.12 + riverTrade;
      }, 0);
    }

    devastationLoss(fid) {
      let loss = 0;
      for (const p of this.ownedProvinces(fid)) {
        const st = this.provinceState[p.id];
        if (!st || st.occupier) continue;
        const base = (st.pop / 90) * (1 + p.roads * 0.15);
        loss += base * Math.min(0.75, st.devastation / 120);
      }
      return Math.round(loss);
    }

    tributeDue(fid) {
      const st = this.factionState[fid];
      return st ? Object.values(st.tribute || {}).reduce((sum, n) => sum + Math.max(0, n), 0) : 0;
    }

    economySnapshot(fid) {
      const st = this.factionState[fid];
      if (!st) return null;
      const income = this.monthlyIncome(fid);
      const upkeep = this.monthlyUpkeep(fid);
      const court = Math.max(0, Math.round(st.treasury * 0.02));
      const debtService = Math.min(st.treasury + income, Math.ceil((st.economy?.warDebt || 0) * 0.025));
      const tributeDue = this.tributeDue(fid);
      const devastationLoss = this.devastationLoss(fid);
      const tradeValue = Math.round(this.tradeValue(fid));
      const foodStress = this._foodStress(fid);
      return {
        treasury: Math.round(st.treasury),
        income,
        upkeep,
        court,
        debtService,
        net: income - upkeep - court - debtService,
        warDebt: st.economy ? st.economy.warDebt : 0,
        taxBurden: st.internal ? st.internal.taxBurden : 0,
        foodStress,
        tradeValue,
        devastationLoss,
        tributeDue,
        lastDecision: st.economy ? st.economy.lastDecision : null,
      };
    }

    _foodStress(fid) {
      const owned = this.ownedProvinces(fid);
      if (!owned.length) return 0;
      const dry = owned.filter((p) => this._terrainFlags(p).dryland || /dry|steppe|salt|oasis/i.test(`${p.terrain} ${p.terrainFeature || ""}`)).length;
      const ruined = owned.reduce((sum, p) => sum + (this.provinceState[p.id]?.devastation || 0), 0) / owned.length;
      const occupied = owned.filter((p) => this.provinceState[p.id].occupier).length;
      return this._clampPolitics(ruined * 0.45 + dry * 7 + occupied * 12);
    }

    internalPoliticsSummary(fid) {
      const st = this.factionState[fid];
      const internal = st && st.internal;
      if (!internal) return [];
      const rows = [
        ["Court tension", internal.courtTension, "court factions strain central rule"],
        ["Succession tension", internal.successionTension, "the line of rule feels disputed"],
        ["Army influence", internal.armyInfluence, "captains and musters shape policy"],
        ["Tax burden", internal.taxBurden, "tax pressure strains towns and estates"],
        ["Faith tension", internal.faithTension, "temples and law disagree"],
        ["Culture tension", internal.cultureTension, "peoples inside the realm pull apart"],
        ["Regional autonomy", internal.regionalAutonomy, "local powers resist the center"],
        ["Noble loyalty", 100 - internal.nobleLoyalty, "nobles are losing confidence"],
        ["Merchant loyalty", 100 - internal.merchantLoyalty, "merchants are losing confidence"],
      ];
      return rows
        .sort((a, b) => b[1] - a[1])
        .slice(0, 4)
        .map(([label, value, reason]) => ({ label, value: this._clampPolitics(value), reason }));
    }

    internalInstability(fid) {
      const st = this.factionState[fid];
      const internal = st && st.internal;
      if (!internal) return 0;
      return this._clampPolitics(
        (internal.courtTension * 0.14) +
        (internal.successionTension * 0.15) +
        (internal.armyInfluence * 0.08) +
        (internal.taxBurden * 0.12) +
        (internal.faithTension * 0.10) +
        (internal.cultureTension * 0.10) +
        (internal.regionalAutonomy * 0.13) +
        ((100 - internal.nobleLoyalty) * 0.10) +
        ((100 - internal.merchantLoyalty) * 0.08)
      );
    }

    heirLegitimacy(fid, heir) {
      const st = this.factionState[fid];
      const internal = st && st.internal;
      const ruler = this.rulerOf(fid);
      if (!st || !heir) return 0;
      let score = 48;
      score += this._legitimacyScore(heir) * 0.38 - 18;
      score += this.factionSupportForCharacter(heir) * 0.14 - 7;
      if (ruler && heir.parentId === ruler.id) score += 26;
      if (heir.family?.bastard && !heir.family?.legitimised) score -= 22;
      if (heir.family?.legitimised) score += 8;
      if (heir.family?.branchType === "cadet") score -= 3;
      if (ruler) {
        const bond = this.relationshipPressure(heir.id);
        const rulerParent = this.relationshipBetween(ruler.id, heir.id, "parent");
        score += bond.succession * 0.7;
        if (rulerParent) score += Math.min(10, (rulerParent.strength || 50) / 10);
      }
      if (heir.age >= 16) score += 10;
      else score -= 12;
      score += Math.min(18, (heir.prestige || 0) / 3);
      if (internal) {
        score -= internal.successionTension * 0.22;
        score -= internal.courtTension * 0.08;
        score += Math.max(0, internal.nobleLoyalty - 45) * 0.10;
      }
      if (st.succession && st.succession.law === "acclaimed war heir") score += (heir.kills || 0) > 0 ? 8 : -4;
      if (st.succession && st.succession.law === "council election") score += heir.traits && heir.traits.some((t) => t.id === "just" || t.id === "patient") ? 6 : 0;
      return this._clampPolitics(score);
    }

    successionStatus(fid) {
      const st = this.factionState[fid];
      if (!st) return null;
      if (!st.succession) st.succession = this._initialSuccessionState(fid);
      const heir = this.heirOf(fid);
      const legitimacy = this.heirLegitimacy(fid, heir);
      const internal = st.internal || {};
      const crisisRisk = this._clampPolitics(
        (100 - legitimacy) * 0.42 +
        (internal.successionPressure || 0) * 0.38 +
        (internal.courtTension || 0) * 0.12 +
        (st.regency ? 8 : 0)
      );
      st.succession.heirLegitimacy = legitimacy;
      return {
        law: st.succession.law,
        heir,
        legitimacy,
        regency: !!st.succession.regency,
        crisis: st.succession.crisis,
        crisisRisk,
        pretenders: st.succession.pretenders || [],
        lastTransition: st.succession.lastTransition,
      };
    }

    _updateInternalPolitics(fid) {
      const f = this.faction(fid);
      const st = this.factionState[fid];
      if (!f || !st) return;
      if (!st.internal) st.internal = this._initialInternalState(fid);
      const internal = st.internal;
      const owned = this.ownedProvinces(fid);
      const wars = this.warsOf(fid);
      const occupied = owned.filter((p) => this.provinceState[p.id].occupier).length;
      const sieged = owned.filter((p) => this.provinceState[p.id].siege).length;
      const claimsHeldByOthers = this.claims.filter((c) => c.claimant === fid &&
        this.provinceState[c.target] && this.provinceState[c.target].controller !== fid).length;
      const activeArmies = this.armies.filter((a) => a.faction === fid).length;
      const heir = this.heirOf(fid);
      const ruler = this.rulerOf(fid);
      const income = this.monthlyIncome(fid);
      const net = income - this.monthlyUpkeep(fid) - Math.max(0, Math.round(st.treasury * 0.02));
      const rulerWar = ruler ? this._traitFactor(fid, "war") : 1;
      const court = this.courtEffects(fid);
      const drift = (value, target, step) => value + Math.sign(target - value) * Math.min(step, Math.abs(target - value));

      internal.courtTension = drift(internal.courtTension, 12 + owned.length * 2 + wars.length * 4 + Math.max(0, -net) / 18 - (court.diplomacy || 0) * 0.08 - (court.intrigue || 0) * 0.05, 4);
      internal.successionTension = drift(internal.successionTension, (heir ? 14 : 48) + (ruler && ruler.age > 55 ? 12 : 0) + st.exhaustion * 0.10 - (court.regency || 0) * 0.09, 5);
      if (heir) {
        internal.successionTension = drift(internal.successionTension, internal.successionTension + Math.max(0, 45 - this.factionSupportForCharacter(heir)) * 0.16, 4);
      }
      internal.armyInfluence = drift(internal.armyInfluence, 16 + activeArmies * 14 + wars.length * 16 + Math.max(0, rulerWar - 1) * 18 - (court.war || 0) * 0.05, 6);
      internal.taxBurden = drift(internal.taxBurden, 22 + Math.max(0, -net) / 7 + Math.max(0, 250 - st.treasury) / 15 + st.exhaustion * 0.08 - (court.economy || 0) * 0.06, 5);
      internal.faithTension = drift(internal.faithTension, 14 + wars.length * 2 - (court.faith || 0) * 0.07, 3);
      internal.cultureTension = drift(internal.cultureTension, (f.species === "mixed" || f.species === "human_orc_mixed" ? 24 : 14) + owned.length * 1.5 + occupied * 7, 3);
      internal.regionalAutonomy = drift(internal.regionalAutonomy, 18 + Math.max(0, owned.length - 1) * 8 + occupied * 10 + claimsHeldByOthers * 3 - (court.governance || 0) * 0.07, 4);
      internal.nobleLoyalty = drift(internal.nobleLoyalty, 68 - internal.courtTension * 0.28 - internal.taxBurden * 0.18 - st.exhaustion * 0.18 + st.prestige * 0.04 + (court.diplomacy || 0) * 0.04, 5);
      internal.merchantLoyalty = drift(internal.merchantLoyalty, 68 - internal.taxBurden * 0.35 - occupied * 8 + Math.max(0, net) * 0.04, 5);
      internal.revoltRisk = this._clampPolitics(
        occupied * 10 + sieged * 8 + internal.taxBurden * 0.22 + internal.regionalAutonomy * 0.18 +
        internal.cultureTension * 0.14 + internal.faithTension * 0.12 + Math.max(0, 45 - internal.nobleLoyalty) * 0.26
      );
      internal.courtTension -= ((court.diplomacy || 0) + (court.intrigue || 0)) * 0.025;
      internal.taxBurden -= (court.economy || 0) * 0.022;
      internal.faithTension -= (court.faith || 0) * 0.018;
      internal.regionalAutonomy -= (court.governance || 0) * 0.018;
      internal.armyInfluence -= (court.war || 0) * 0.012;
      internal.successionPressure = this._clampPolitics(
        internal.successionTension * 0.75 +
        (heir ? Math.max(0, 45 - this.factionSupportForCharacter(heir)) * 0.18 : 18) +
        (ruler && ruler.age > 60 ? 12 : 0)
      );
      for (const key of Object.keys(internal)) internal[key] = this._clampPolitics(internal[key]);

      if (this.day > 0 && internal.revoltRisk >= 55 && this.rng.chance(0.08)) {
        this.log(2, "politics",
          `${f.name} faces dangerous internal unrest: tax strain, autonomy and court distrust are now feeding revolt talk.`,
          { faction: fid });
      }
      if (this.day > 0 && internal.successionPressure >= 60 && this.rng.chance(0.06)) {
        this.log(2, "politics",
          `${f.name} whispers over succession grow louder; every council now asks who can hold the realm together.`,
          { faction: fid, character: st.rulerId });
      }
    }

    _setEconomyDecision(fid, type, text, refs) {
      const st = this.factionState[fid];
      if (!st || !st.economy) return;
      st.economy.lastDecision = {
        type,
        text,
        date: this.formatDate(),
        day: this.day,
      };
      this.log(2, "economy", text, { faction: fid, ...(refs || {}) });
    }

    _dismissSmallestArmy(fid, reason) {
      const army = this.armies
        .filter((a) => a.faction === fid)
        .sort((a, b) => a.size - b.size)[0];
      if (!army) return false;
      this._setEconomyDecision(fid, "dismiss armies",
        `${this.faction(fid).name} dismisses ${Math.round(army.size).toLocaleString()} soldiers because ${reason}.`,
        { province: army.loc, character: army.commanderId });
      this._disband(army);
      return true;
    }

    _survivalEconomyDecision(fid, snapshot) {
      const f = this.faction(fid);
      const st = this.factionState[fid];
      const internal = st.internal;
      if (!f || !st || !st.economy || !snapshot) return;
      const last = st.economy.lastDecision;
      if (last && this.day - last.day < 90) return;
      const atWar = this.warsOf(fid).length > 0;

      if (snapshot.foodStress >= 62 && internal.taxBurden > 24) {
        internal.taxBurden = Math.max(0, internal.taxBurden - 8);
        internal.merchantLoyalty = Math.min(100, internal.merchantLoyalty + 5);
        this._setEconomyDecision(fid, "lower taxes",
          `${f.name} lowers taxes to ease food stress before the granaries break.`,
          {});
        return;
      }

      if (snapshot.net < -90 && internal.taxBurden < 78 && snapshot.foodStress < 55) {
        internal.taxBurden = Math.min(100, internal.taxBurden + 9);
        internal.nobleLoyalty = Math.max(0, internal.nobleLoyalty - 4);
        internal.merchantLoyalty = Math.max(0, internal.merchantLoyalty - 5);
        this._setEconomyDecision(fid, "raise taxes",
          `${f.name} raises taxes to cover a ${Math.abs(snapshot.net).toLocaleString()} silver monthly shortfall.`,
          {});
        return;
      }

      if (snapshot.treasury < 65 && atWar && snapshot.warDebt < 900) {
        const borrowed = 260;
        st.treasury += borrowed;
        st.economy.warDebt += borrowed;
        internal.merchantLoyalty = Math.max(0, internal.merchantLoyalty - 6);
        this._setEconomyDecision(fid, "borrow money",
          `${f.name} borrows ${borrowed} silver to keep the war chest alive.`,
          {});
        return;
      }

      if (snapshot.net < -140 && this.armyStrength(fid) > 0 && !atWar) {
        if (this._dismissSmallestArmy(fid, "the treasury cannot carry idle troops")) return;
      }

      if (snapshot.warDebt > 700 && internal.nobleLoyalty > 20) {
        const relief = Math.min(snapshot.warDebt, 180);
        st.economy.warDebt -= relief;
        st.treasury += Math.round(relief * 0.35);
        internal.nobleLoyalty = Math.max(0, internal.nobleLoyalty - 9);
        internal.regionalAutonomy = Math.min(100, internal.regionalAutonomy + 7);
        this._setEconomyDecision(fid, "sell privileges",
          `${f.name} sells privileges to powerful houses, easing ${relief} silver of war debt at the cost of loyalty.`,
          {});
        return;
      }

      const conquered = this.ownedProvinces(fid)
        .filter((p) => (this.provinceState[p.id].recentConquest || 0) > 0)
        .sort((a, b) => (this.provinceState[b.id].recentConquest || 0) - (this.provinceState[a.id].recentConquest || 0))[0];
      if (conquered && snapshot.treasury < 130 && internal.revoltRisk < 80) {
        const stp = this.provinceState[conquered.id];
        const squeezed = Math.round(80 + conquered.value * 1.2);
        st.treasury += squeezed;
        stp.devastation = Math.min(100, stp.devastation + 10);
        stp.instability = Math.min(100, (stp.instability || 0) + 12);
        internal.revoltRisk = Math.min(100, internal.revoltRisk + 7);
        this._setEconomyDecision(fid, "squeeze conquered land",
          `${f.name} squeezes ${conquered.name} for ${squeezed} silver, risking unrest in conquered land.`,
          { province: conquered.id });
        return;
      }
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

    provinceInstability(pid) {
      const p = this.province(pid);
      const st = this.provinceState[pid];
      if (!p || !st) return { score: 0, causes: [] };
      const controller = this.factionState[st.controller];
      const internal = controller && controller.internal;
      const causes = [];
      let score = 0;
      const add = (amount, cause) => {
        if (amount <= 0) return;
        score += amount;
        causes.push(cause);
      };
      add(st.devastation * 0.45, "devastation");
      add(st.occupier ? 22 : 0, "occupation");
      add(st.recentConquest || 0, "recent conquest");
      add(st.garrison < 160 ? 18 : st.garrison < 300 ? 8 : 0, "low garrison");
      if (internal) {
        add(internal.cultureTension * 0.16, "culture tension");
        add(internal.faithTension * 0.15, "faith tension");
        add(internal.taxBurden * 0.18, "high taxes");
        add(internal.regionalAutonomy * 0.14, "regional autonomy");
        add(Math.max(0, 45 - internal.nobleLoyalty) * 0.22, "weak noble loyalty");
      }
      add(st.riotLogged ? 16 : 0, "famine");
      const ruler = controller && this.rulerOf(st.controller);
      add(!ruler || !ruler.alive ? 16 : 0, "weak ruler");
      add(this.claims.some((c) => c.target === pid && c.claimant !== st.controller && c.strength >= 60) ? 12 : 0, "foreign support");
      return { score: this._clampPolitics(score), causes };
    }

    _revoltTypeFor(pid, causes) {
      const p = this.province(pid);
      const st = this.provinceState[pid];
      const internal = this.factionState[st.controller] && this.factionState[st.controller].internal;
      if (internal && internal.successionPressure >= 65) return "pretender_revolt";
      if (causes.includes("regional autonomy") || causes.includes("foreign support")) return "separatist_revolt";
      if (causes.includes("faith tension")) return "religious_uprising";
      if (internal && internal.armyInfluence >= 62) return "military_coup";
      if (causes.includes("weak noble loyalty")) return "noble_revolt";
      if (p && /frontier|pass|steppe|oasis|dryland/i.test(`${p.terrain} ${p.terrainFeature || ""}`)) return "frontier_independence";
      return "peasant_revolt";
    }

    _startRevolt(pid, forcedType) {
      const p = this.province(pid);
      const st = this.provinceState[pid];
      if (!p || !st || st.revoltId) return null;
      const instability = this.provinceInstability(pid);
      const type = forcedType || this._revoltTypeFor(pid, instability.causes);
      const revolt = {
        id: uid("revolt"),
        type,
        province: pid,
        against: st.controller,
        causes: instability.causes,
        strength: Math.max(120, Math.round(st.pop * (0.035 + instability.score / 2200))),
        progress: 0.25,
        startedDay: this.day,
        startDate: this.formatDate(),
        status: "active",
      };
      this.revolts.push(revolt);
      st.revoltId = revolt.id;
      st.instability = Math.max(st.instability || 0, instability.score);
      this.log(3, "revolt",
        `${p.name} erupts in ${type.replace(/_/g, " ")} against ${this.faction(st.controller).name}; causes: ${instability.causes.join(", ") || "local anger"}.`,
        { province: pid, faction: st.controller, revolt: revolt.id });
      return revolt;
    }

    _revoltPulse() {
      for (const p of this.seed.provinces) {
        const st = this.provinceState[p.id];
        const instability = this.provinceInstability(p.id);
        st.instability = instability.score;
        if (st.recentConquest) st.recentConquest = Math.max(0, st.recentConquest - 2);
        if (st.revoltId) continue;
        const internal = this.factionState[st.controller] && this.factionState[st.controller].internal;
        const realmRisk = internal ? internal.revoltRisk : 0;
        if (instability.score < 55 && realmRisk < 60) continue;
        const chance = Math.min(0.10, Math.max(0.01, (instability.score + realmRisk - 85) / 700));
        if (this.rng.chance(chance)) this._startRevolt(p.id);
      }

      for (const revolt of this.revolts) {
        if (revolt.status !== "active") continue;
        const p = this.province(revolt.province);
        const st = this.provinceState[revolt.province];
        if (!p || !st) { revolt.status = "invalid"; continue; }
        const controllerState = this.factionState[revolt.against];
        const suppression = (st.garrison / Math.max(revolt.strength, 1)) * 0.13 +
          (controllerState ? controllerState.manpower / Math.max(controllerState.maxManpower, 1) * 0.08 : 0);
        const pressure = 0.07 + st.instability / 900 + st.devastation / 1300;
        revolt.progress += pressure - suppression + this.rng.float(-0.025, 0.035);
        revolt.progress = Math.max(0, Math.min(1, revolt.progress));
        st.devastation = Math.min(100, st.devastation + 1.2);
        st.garrison = Math.max(30, Math.round(st.garrison - revolt.strength * 0.01));
        if (revolt.progress >= 0.55 && !revolt.clashLogged) {
          revolt.clashLogged = true;
          this.log(2, "revolt",
            `${p.name}'s ${revolt.type.replace(/_/g, " ")} spreads into open fighting; the garrison is bleeding authority.`,
            { province: p.id, faction: revolt.against, revolt: revolt.id });
        }
        if (revolt.progress >= 1) {
          this._endRevolt(revolt, true, "rebel pressure overwhelmed the local garrison");
        } else if (revolt.progress <= 0.02) {
          this._endRevolt(revolt, false, "the garrison broke the revolt before it could spread");
        }
      }
    }

    _endRevolt(revolt, rebelsWin, reason) {
      const p = this.province(revolt.province);
      const st = this.provinceState[revolt.province];
      if (!p || !st) return;
      revolt.status = rebelsWin ? "won" : "suppressed";
      revolt.endedDay = this.day;
      revolt.endDate = this.formatDate();
      revolt.outcome = reason;
      st.revoltId = null;
      if (rebelsWin) {
        const claimant = this.claims
          .filter((c) => c.target === p.id && c.claimant !== revolt.against)
          .sort((a, b) => b.strength - a.strength)[0];
        const oldController = st.controller;
        if (claimant && this.factionState[claimant.claimant]) {
          st.controller = claimant.claimant;
          this._refreshManpower(claimant.claimant, true);
        }
        st.occupier = null;
        st.siege = null;
        st.devastation = Math.min(100, st.devastation + 14);
        st.recentConquest = 22;
        this.factionState[oldController].exhaustion += 10;
        if (this.factionState[oldController].internal) {
          this.factionState[oldController].internal.revoltRisk = Math.min(100, this.factionState[oldController].internal.revoltRisk + 8);
        }
        this.mapVersion++;
        this.log(3, "revolt",
          `${p.name}'s ${revolt.type.replace(/_/g, " ")} wins because ${reason}. ${st.controller !== oldController ? this.faction(st.controller).name + " takes control." : "The old order survives only in name."}`,
          { province: p.id, faction: st.controller, revolt: revolt.id });
      } else {
        st.instability = Math.max(0, st.instability - 22);
        st.garrison = Math.max(50, Math.round(st.garrison * 0.82));
        if (this.factionState[revolt.against] && this.factionState[revolt.against].internal) {
          this.factionState[revolt.against].internal.nobleLoyalty = Math.max(0, this.factionState[revolt.against].internal.nobleLoyalty - 3);
          this.factionState[revolt.against].internal.taxBurden = Math.max(0, this.factionState[revolt.against].internal.taxBurden - 5);
        }
        this.log(3, "revolt",
          `${p.name}'s ${revolt.type.replace(/_/g, " ")} is suppressed because ${reason}. The province is quiet, not healed.`,
          { province: p.id, faction: revolt.against, revolt: revolt.id });
      }
    }

    validateState() {
      const issues = [];
      const add = (severity, code, location, message) => issues.push({ severity, code, location, message });
      const factions = new Set(this.seed.factions.map((f) => f.id));
      const provinces = new Set(this.seed.provinces.map((p) => p.id));
      const cultures = new Set(Object.keys(this.seed.cultures || {}));
      const species = new Set(Object.keys(this.seed.species || {}));
      const validTiers = new Set(["tier_1", "tier_2", "tier_3", "tier_4"]);
      const characterIds = new Set(this.characters.map((c) => c.id));
      const dynastyIds = new Set((this.dynasties || []).map((d) => d.id));
      const houseIds = new Set((this.houses || []).map((h) => h.id));
      const activeWarIds = new Set(this.wars.filter((w) => !w.over).map((w) => w.id));
      const seen = { factions: new Set(), provinces: new Set(), characters: new Set() };
      const hasParentLoop = (characterId, path) => {
        if (path.has(characterId)) return true;
        const c = this.character(characterId);
        if (!c) return false;
        const next = this._parentIds(c);
        if (!next.length) return false;
        const nextPath = new Set(path);
        nextPath.add(characterId);
        return next.some((parentId) => hasParentLoop(parentId, nextPath));
      };

      for (const f of this.seed.factions) {
        if (seen.factions.has(f.id)) add("error", "duplicate_faction_id", `faction:${f.id}`, "Faction IDs must be unique.");
        seen.factions.add(f.id);
        if (!this.factionState[f.id]) add("error", "missing_faction_state", `faction:${f.id}`, "Faction has no runtime state.");
        if (f.culture && !cultures.has(f.culture)) add("error", "unknown_faction_culture", `faction:${f.id}`, f.culture);
        if (f.species && !species.has(f.species)) add("error", "unknown_faction_species", `faction:${f.id}`, f.species);
        if (!validTiers.has(f.tier)) add("error", "invalid_faction_tier", `faction:${f.id}.tier`, String(f.tier));
        if ((f.tierWeight || 0) <= 0) add("error", "invalid_faction_tier_weight", `faction:${f.id}.tierWeight`, String(f.tierWeight));
      }

      for (const p of this.seed.provinces) {
        if (seen.provinces.has(p.id)) add("error", "duplicate_province_id", `province:${p.id}`, "Province IDs must be unique.");
        seen.provinces.add(p.id);
        if (!factions.has(p.controller)) add("error", "unknown_seed_controller", `province:${p.id}`, p.controller);
        if (!this.provinceState[p.id]) add("error", "missing_province_state", `province:${p.id}`, "Province has no runtime state.");
        for (const field of ["value", "fort", "roads"]) {
          if ((p[field] || 0) < 0) add("error", "negative_seed_province_number", `province:${p.id}.${field}`, String(p[field]));
        }
      }

      for (const c of this.characters) {
        if (seen.characters.has(c.id)) add("error", "duplicate_character_id", `character:${c.id}`, "Character IDs must be unique.");
        seen.characters.add(c.id);
        if (!factions.has(c.faction)) add("error", "unknown_character_faction", `character:${c.id}`, c.faction);
        if (c.culture && !cultures.has(c.culture)) add("error", "unknown_character_culture", `character:${c.id}`, c.culture);
        if (c.species && !species.has(c.species)) add("error", "unknown_character_species", `character:${c.id}`, c.species);
        if ((c.age || 0) < 0) add("error", "negative_character_age", `character:${c.id}.age`, String(c.age));
        if (c.faith && !this.seed.religions[c.faith]) add("error", "unknown_character_faith", `character:${c.id}.faith`, c.faith);
        if (typeof c.birthYear !== "number") add("error", "missing_character_birth_year", `character:${c.id}.birthYear`, String(c.birthYear));
        if (c.deathYear !== null && c.deathYear !== undefined && typeof c.deathYear !== "number") add("error", "invalid_character_death_year", `character:${c.id}.deathYear`, String(c.deathYear));
        for (const field of ["stress", "health", "wealth", "legitimacy", "reputation"]) {
          if (typeof c[field] !== "number") add("error", "invalid_character_state_number", `character:${c.id}.${field}`, String(c[field]));
          else if (c[field] < 0) add("error", "negative_character_state_number", `character:${c.id}.${field}`, String(c[field]));
        }
        for (const field of ["health", "legitimacy", "reputation", "stress"]) {
          if (typeof c[field] === "number" && c[field] > 100) add("error", "character_state_out_of_range", `character:${c.id}.${field}`, String(c[field]));
        }
        if (!c.ambition) add("error", "missing_character_ambition", `character:${c.id}.ambition`, "Character needs an ambition.");
        else if (!VALID_AMBITIONS.has(c.ambition)) add("error", "invalid_character_ambition", `character:${c.id}.ambition`, String(c.ambition));
        if (!c.fear) add("error", "missing_character_fear", `character:${c.id}.fear`, "Character needs a fear.");
        else if (!VALID_FEARS.has(c.fear)) add("error", "invalid_character_fear", `character:${c.id}.fear`, String(c.fear));
        if (!c.loyalties || !c.loyalties.faction) add("error", "missing_character_loyalties", `character:${c.id}.loyalties`, "Character needs loyalties.");
        if (!Array.isArray(c.memories)) add("error", "invalid_character_memories", `character:${c.id}.memories`, "Character memories must be an array.");
        for (const memory of Array.isArray(c.memories) ? c.memories : []) {
          const loc = `character:${c.id}.memory:${memory.id || "missing"}`;
          if (!memory.id) add("error", "missing_memory_id", loc, "Memory needs an ID.");
          if (!VALID_MEMORY_TYPES.has(memory.type)) add("error", "invalid_memory_type", `${loc}.type`, String(memory.type));
          if (!memory.text) add("error", "missing_memory_text", `${loc}.text`, "Memory needs readable text.");
          if (typeof memory.day !== "number" || memory.day < 0) add("error", "invalid_memory_day", `${loc}.day`, String(memory.day));
          const refs = memory.refs || {};
          if (refs.character && !characterIds.has(refs.character)) add("error", "unknown_memory_character", `${loc}.refs.character`, refs.character);
          if (refs.faction && !factions.has(refs.faction)) add("error", "unknown_memory_faction", `${loc}.refs.faction`, refs.faction);
          if (refs.province && !provinces.has(refs.province)) add("error", "unknown_memory_province", `${loc}.refs.province`, refs.province);
          if (refs.war && !activeWarIds.has(refs.war) && !this.wars.some((w) => w.id === refs.war)) add("error", "unknown_memory_war", `${loc}.refs.war`, refs.war);
        }
        const record = c.militaryRecord;
        if (!record) add("error", "missing_military_record", `character:${c.id}.militaryRecord`, "Character needs a military record.");
        if (record) {
          for (const field of ["battlesFought", "battlesWon", "battlesLost", "siegesLed", "wounds"]) {
            if (typeof record[field] !== "number") add("error", "invalid_military_record_number", `character:${c.id}.militaryRecord.${field}`, String(record[field]));
            else if (record[field] < 0) add("error", "negative_military_record_number", `character:${c.id}.militaryRecord.${field}`, String(record[field]));
          }
          if ((record.battlesWon || 0) + (record.battlesLost || 0) > (record.battlesFought || 0)) {
            add("error", "invalid_military_record_totals", `character:${c.id}.militaryRecord`, "Wins and losses cannot exceed battles fought.");
          }
          for (const field of ["notableVictories", "notableDefeats"]) {
            if (!Array.isArray(record[field])) add("error", "invalid_military_record_list", `character:${c.id}.militaryRecord.${field}`, "Notable records must be arrays.");
          }
        }
        const family = c.family;
        if (!family) add("error", "missing_family_state", `character:${c.id}.family`, "Character needs family state.");
        if (family) {
          for (const field of ["father", "mother"]) {
            if (family[field] && !characterIds.has(family[field])) add("error", "unknown_family_parent", `character:${c.id}.family.${field}`, family[field]);
            if (family[field] === c.id) add("error", "self_family_parent", `character:${c.id}.family.${field}`, "Character cannot be their own parent.");
          }
          for (const field of ["spouses", "lovers", "children", "siblings"]) {
            if (!Array.isArray(family[field])) add("error", "invalid_family_list", `character:${c.id}.family.${field}`, "Family links must be arrays.");
            for (const id of Array.isArray(family[field]) ? family[field] : []) {
              if (!characterIds.has(id)) add("error", "unknown_family_link", `character:${c.id}.family.${field}`, id);
              if (id === c.id) add("error", "self_family_link", `character:${c.id}.family.${field}`, "Character cannot link to themselves.");
            }
          }
          if (!family.dynasty) add("error", "missing_family_dynasty", `character:${c.id}.family.dynasty`, "Dynasty is required.");
          if (!family.house) add("error", "missing_family_house", `character:${c.id}.family.house`, "House is required.");
          if (family.dynastyId && !dynastyIds.has(family.dynastyId)) add("error", "unknown_character_dynasty", `character:${c.id}.family.dynastyId`, family.dynastyId);
          if (family.houseId && !houseIds.has(family.houseId)) add("error", "unknown_character_house", `character:${c.id}.family.houseId`, family.houseId);
          if (!["main", "cadet"].includes(family.branchType || "main")) {
            add("error", "invalid_family_branch_type", `character:${c.id}.family.branchType`, String(family.branchType));
          }
          if (family.branchFounder && !characterIds.has(family.branchFounder)) {
            add("error", "unknown_family_branch_founder", `character:${c.id}.family.branchFounder`, String(family.branchFounder));
          }
          if (family.parentHouseId && !houseIds.has(family.parentHouseId)) {
            add("error", "unknown_family_parent_house", `character:${c.id}.family.parentHouseId`, String(family.parentHouseId));
          }
          if (typeof family.bastard !== "boolean") {
            add("error", "invalid_family_bastard", `character:${c.id}.family.bastard`, String(family.bastard));
          }
          if (typeof family.legitimised !== "boolean") {
            add("error", "invalid_family_legitimised", `character:${c.id}.family.legitimised`, String(family.legitimised));
          }
          if (family.legitimised && !family.bastard) {
            add("error", "legitimised_without_bastard", `character:${c.id}.family.legitimised`, "Only bastards can be marked legitimised.");
          }
          if (typeof family.legitimacy !== "number" || family.legitimacy < 0 || family.legitimacy > 100) {
            add("error", "invalid_family_legitimacy", `character:${c.id}.family.legitimacy`, String(family.legitimacy));
          }
          if (family.inheritanceRank !== null && family.inheritanceRank !== undefined &&
              (typeof family.inheritanceRank !== "number" || family.inheritanceRank < 1)) {
            add("error", "invalid_inheritance_rank", `character:${c.id}.family.inheritanceRank`, String(family.inheritanceRank));
          }
          if (typeof family.claimStrength !== "number" || family.claimStrength < 0 || family.claimStrength > 100) {
            add("error", "invalid_family_claim_strength", `character:${c.id}.family.claimStrength`, String(family.claimStrength));
          }
          if (hasParentLoop(c.id, new Set())) add("error", "family_parent_loop", `character:${c.id}.family`, "Family parent links contain a loop.");
        }
      }

      for (const dynasty of this.dynasties || []) {
        const loc = `dynasty:${dynasty.id}`;
        if (!dynasty.id) add("error", "missing_dynasty_id", loc, "Dynasty needs an ID.");
        if (!dynasty.name) add("error", "missing_dynasty_name", `${loc}.name`, "Dynasty needs a name.");
        if (!characterIds.has(dynasty.founder)) add("error", "unknown_dynasty_founder", `${loc}.founder`, String(dynasty.founder));
        if (dynasty.head && !characterIds.has(dynasty.head)) add("error", "unknown_dynasty_head", `${loc}.head`, String(dynasty.head));
        if (dynasty.homeProvince && !provinces.has(dynasty.homeProvince)) add("error", "unknown_dynasty_home_province", `${loc}.homeProvince`, dynasty.homeProvince);
        for (const member of dynasty.members || []) {
          if (!characterIds.has(member)) add("error", "unknown_dynasty_member", `${loc}.members`, String(member));
        }
        for (const houseId of dynasty.houses || []) {
          if (!houseIds.has(houseId)) add("error", "unknown_dynasty_house", `${loc}.houses`, String(houseId));
        }
        for (const branch of dynasty.cadetBranches || []) {
          if (!branch.house || !houseIds.has(branch.house)) add("error", "unknown_dynasty_cadet_house", `${loc}.cadetBranches.house`, String(branch.house));
          if (branch.founder && !characterIds.has(branch.founder)) add("error", "unknown_dynasty_cadet_founder", `${loc}.cadetBranches.founder`, String(branch.founder));
          if (branch.parentHouseId && !houseIds.has(branch.parentHouseId)) add("error", "unknown_dynasty_cadet_parent_house", `${loc}.cadetBranches.parentHouseId`, String(branch.parentHouseId));
        }
        for (const rival of dynasty.rivals || []) {
          if (!dynastyIds.has(rival)) add("error", "unknown_dynasty_rival", `${loc}.rivals`, String(rival));
        }
        for (const alliance of dynasty.alliances || []) {
          if (!dynastyIds.has(alliance)) add("error", "unknown_dynasty_alliance", `${loc}.alliances`, String(alliance));
        }
        if ((dynasty.prestige || 0) < 0 || (dynasty.renown || 0) < 0) add("error", "negative_dynasty_number", loc, "Dynasty prestige and renown must be non-negative.");
      }

      for (const house of this.houses || []) {
        const loc = `house:${house.id}`;
        if (!house.id) add("error", "missing_house_id", loc, "House needs an ID.");
        if (!house.name) add("error", "missing_house_name", `${loc}.name`, "House needs a name.");
        if (!dynastyIds.has(house.dynasty)) add("error", "unknown_house_dynasty", `${loc}.dynasty`, String(house.dynasty));
        if (!characterIds.has(house.founder)) add("error", "unknown_house_founder", `${loc}.founder`, String(house.founder));
        if (!characterIds.has(house.head)) add("error", "unknown_house_head", `${loc}.head`, String(house.head));
        if (house.homeProvince && !provinces.has(house.homeProvince)) add("error", "unknown_house_home_province", `${loc}.homeProvince`, house.homeProvince);
        if (!["main", "cadet"].includes(house.branchType || "main")) add("error", "invalid_house_branch_type", `${loc}.branchType`, String(house.branchType));
        if (house.branchFounder && !characterIds.has(house.branchFounder)) add("error", "unknown_house_branch_founder", `${loc}.branchFounder`, String(house.branchFounder));
        if (house.parentHouseId && !houseIds.has(house.parentHouseId)) add("error", "unknown_house_parent_house", `${loc}.parentHouseId`, String(house.parentHouseId));
        for (const member of house.members || []) {
          if (!characterIds.has(member)) add("error", "unknown_house_member", `${loc}.members`, String(member));
        }
        if (house.head && Array.isArray(house.members) && !house.members.includes(house.head)) {
          add("error", "house_head_not_member", `${loc}.head`, "House head must be a member.");
        }
        if (typeof house.legitimacy !== "number" || house.legitimacy < 0 || house.legitimacy > 100) add("error", "invalid_house_legitimacy", `${loc}.legitimacy`, String(house.legitimacy));
        if ((house.prestige || 0) < 0) add("error", "negative_house_prestige", `${loc}.prestige`, String(house.prestige));
      }

      const relationshipKeys = new Set();
      for (const rel of this.relationships || []) {
        const loc = `relationship:${rel.id || `${rel.from}-${rel.to}-${rel.type}`}`;
        if (relationshipKeys.has(rel.id)) add("error", "duplicate_relationship_id", loc, "Relationship IDs must be unique.");
        if (rel.id) relationshipKeys.add(rel.id);
        if (!characterIds.has(rel.from)) add("error", "unknown_relationship_from", `${loc}.from`, String(rel.from));
        if (!characterIds.has(rel.to)) add("error", "unknown_relationship_to", `${loc}.to`, String(rel.to));
        if (rel.from === rel.to) add("error", "self_relationship", loc, "Character cannot have a relationship to themselves.");
        if (!VALID_RELATIONSHIP_TYPES.has(rel.type)) add("error", "invalid_relationship_type", `${loc}.type`, String(rel.type));
        if (typeof rel.strength !== "number" || rel.strength < 1 || rel.strength > 100) {
          add("error", "invalid_relationship_strength", `${loc}.strength`, String(rel.strength));
        }
        const reciprocal = RECIPROCAL_RELATIONSHIP[rel.type];
        if (reciprocal && characterIds.has(rel.from) && characterIds.has(rel.to) && VALID_RELATIONSHIP_TYPES.has(rel.type)) {
          const hasBack = (this.relationships || []).some((back) =>
            back.from === rel.to && back.to === rel.from && back.type === reciprocal);
          if (!hasBack) add("error", "missing_reciprocal_relationship", loc, `${rel.type} needs ${reciprocal} back.`);
        }
      }

      for (const mage of this.mages) {
        const loc = `mage:${mage.id}`;
        if (!characterIds.has(mage.character)) add("error", "unknown_mage_character", loc, mage.character);
        if (!factions.has(mage.patron)) add("error", "unknown_mage_patron", loc, mage.patron);
        if (mage.species && !species.has(mage.species)) add("error", "unknown_mage_species", loc, mage.species);
        for (const field of ["capacity", "control", "strain", "risk"]) {
          if ((mage[field] || 0) < 0) add("error", "negative_mage_number", `${loc}.${field}`, String(mage[field]));
        }
      }

      for (const [fid, st] of Object.entries(this.factionState)) {
        const loc = `faction_state:${fid}`;
        if (!factions.has(fid)) add("error", "unknown_faction_state", loc, "Runtime state belongs to no seed faction.");
        if (st.rulerId && !characterIds.has(st.rulerId)) add("error", "unknown_ruler", `${loc}.rulerId`, st.rulerId);
        for (const field of ["treasury", "manpower", "maxManpower", "prestige", "exhaustion"]) {
          if ((st[field] || 0) < 0) add("error", "negative_faction_number", `${loc}.${field}`, String(st[field]));
        }
        if (!st.internal) add("error", "missing_internal_politics", `${loc}.internal`, "Faction has no internal politics state.");
        if (st.internal) {
          for (const field of [
            "courtTension", "successionTension", "armyInfluence", "taxBurden", "faithTension",
            "cultureTension", "regionalAutonomy", "nobleLoyalty", "merchantLoyalty",
            "revoltRisk", "successionPressure",
          ]) {
            if (typeof st.internal[field] !== "number") add("error", "invalid_internal_politics_number", `${loc}.internal.${field}`, String(st.internal[field]));
            else if (st.internal[field] < 0 || st.internal[field] > 100) add("error", "internal_politics_out_of_range", `${loc}.internal.${field}`, String(st.internal[field]));
          }
        }
        if (!st.succession) add("error", "missing_succession_state", `${loc}.succession`, "Faction has no succession state.");
        if (st.succession) {
          if (!st.succession.law) add("error", "missing_succession_law", `${loc}.succession.law`, "Succession law is required.");
          if (typeof st.succession.heirLegitimacy !== "number" || st.succession.heirLegitimacy < 0 || st.succession.heirLegitimacy > 100) {
            add("error", "invalid_heir_legitimacy", `${loc}.succession.heirLegitimacy`, String(st.succession.heirLegitimacy));
          }
          for (const pretender of st.succession.pretenders || []) {
            if (!characterIds.has(pretender.character)) add("error", "unknown_pretender_character", `${loc}.succession.pretenders`, String(pretender.character));
            if ((pretender.claimStrength || 0) < 0 || (pretender.claimStrength || 0) > 100) {
              add("error", "invalid_pretender_claim_strength", `${loc}.succession.pretenders.claimStrength`, String(pretender.claimStrength));
            }
          }
        }
        if (!st.economy) add("error", "missing_economy_state", `${loc}.economy`, "Faction has no economy state.");
        if (st.economy) {
          for (const field of ["warDebt", "foodStress", "tradeValue", "devastationLoss", "tributeDue"]) {
            if (typeof st.economy[field] !== "number") add("error", "invalid_economy_number", `${loc}.economy.${field}`, String(st.economy[field]));
            else if (st.economy[field] < 0) add("error", "negative_economy_number", `${loc}.economy.${field}`, String(st.economy[field]));
          }
          if (st.economy.foodStress > 100) add("error", "economy_food_stress_out_of_range", `${loc}.economy.foodStress`, String(st.economy.foodStress));
          if (st.economy.lastDecision && (!st.economy.lastDecision.type || !st.economy.lastDecision.text)) {
            add("error", "invalid_economy_decision", `${loc}.economy.lastDecision`, "Economy decision needs type and text.");
          }
        }
        if (!st.court) add("error", "missing_court_state", `${loc}.court`, "Faction has no court state.");
        if (st.court) {
          if (st.court.faction !== fid) add("error", "invalid_court_faction", `${loc}.court.faction`, String(st.court.faction));
          if (typeof st.court.stability !== "number" || st.court.stability < 0 || st.court.stability > 100) {
            add("error", "invalid_court_stability", `${loc}.court.stability`, String(st.court.stability));
          }
          const offices = st.court.offices || {};
          for (const office of COURT_OFFICES) {
            if (!(office in offices)) add("error", "missing_court_office", `${loc}.court.offices.${office}`, "Office slot is missing.");
          }
          for (const [office, assignment] of Object.entries(offices)) {
            const officeLoc = `${loc}.court.offices.${office}`;
            if (!VALID_COURT_OFFICES.has(office)) add("error", "invalid_court_office", officeLoc, office);
            if (assignment === null) continue;
            if (!assignment || typeof assignment !== "object") {
              add("error", "invalid_court_assignment", officeLoc, "Office assignment must be null or an object.");
              continue;
            }
            if (assignment.office !== office) add("error", "court_office_mismatch", `${officeLoc}.office`, String(assignment.office));
            const holder = this.character(assignment.character);
            if (!holder) add("error", "unknown_court_office_holder", `${officeLoc}.character`, String(assignment.character));
            else {
              if (holder.faction !== fid) add("error", "wrong_faction_court_office_holder", `${officeLoc}.character`, String(assignment.character));
              if (!holder.alive) add("error", "dead_court_office_holder", `${officeLoc}.character`, String(assignment.character));
            }
            if (typeof assignment.effectiveness !== "number" || assignment.effectiveness < 0 || assignment.effectiveness > 100) {
              add("error", "invalid_court_office_effectiveness", `${officeLoc}.effectiveness`, String(assignment.effectiveness));
            }
          }
        }
      }

      for (const [pid, st] of Object.entries(this.provinceState)) {
        const loc = `province_state:${pid}`;
        if (!provinces.has(pid)) add("error", "unknown_runtime_province", loc, "Runtime state belongs to no seed province.");
        if (!factions.has(st.controller)) add("error", "unknown_runtime_controller", `${loc}.controller`, st.controller);
        if (st.occupier && !factions.has(st.occupier)) add("error", "unknown_occupier", `${loc}.occupier`, st.occupier);
        if (st.siege && !factions.has(st.siege.by)) add("error", "unknown_sieger", `${loc}.siege.by`, st.siege.by);
        if (st.revoltId && !this.revolts.some((r) => r.id === st.revoltId)) add("error", "unknown_province_revolt", `${loc}.revoltId`, st.revoltId);
        for (const field of ["pop", "garrison", "devastation", "instability", "recentConquest"]) {
          if ((st[field] || 0) < 0) add("error", "negative_province_state_number", `${loc}.${field}`, String(st[field]));
        }
      }

      for (const claim of this.claims) {
        const loc = `claim:${claim.id}`;
        if (!factions.has(claim.claimant)) add("error", "unknown_claimant", loc, claim.claimant);
        if (!provinces.has(claim.target)) add("error", "unknown_claim_target", loc, claim.target);
        if ((claim.strength || 0) < 0) add("error", "negative_claim_strength", `${loc}.strength`, String(claim.strength));
      }

      for (const war of this.wars) {
        const loc = `war:${war.id}`;
        if (!factions.has(war.attacker)) add("error", "unknown_war_attacker", loc, war.attacker);
        if (!factions.has(war.defender)) add("error", "unknown_war_defender", loc, war.defender);
        if (war.goal && war.goal.province && !provinces.has(war.goal.province)) add("error", "unknown_war_goal", `${loc}.goal`, war.goal.province);
        for (const sideName of ["atkSide", "defSide"]) {
          for (const fid of (war[sideName] || [])) if (!factions.has(fid)) add("error", "unknown_war_side", `${loc}.${sideName}`, fid);
        }
      }

      for (const revolt of this.revolts) {
        const loc = `revolt:${revolt.id}`;
        if (!provinces.has(revolt.province)) add("error", "unknown_revolt_province", loc, revolt.province);
        if (!factions.has(revolt.against)) add("error", "unknown_revolt_target", loc, revolt.against);
        if (!["active", "won", "suppressed", "invalid"].includes(revolt.status)) add("error", "invalid_revolt_status", loc, String(revolt.status));
        if ((revolt.strength || 0) < 0) add("error", "negative_revolt_strength", `${loc}.strength`, String(revolt.strength));
        if (typeof revolt.progress !== "number" || revolt.progress < 0 || revolt.progress > 1) add("error", "invalid_revolt_progress", `${loc}.progress`, String(revolt.progress));
      }

      for (const army of this.armies) {
        const loc = `army:${army.id}`;
        if (!factions.has(army.faction)) add("error", "unknown_army_faction", loc, army.faction);
        if (!provinces.has(army.loc)) add("error", "unknown_army_location", `${loc}.loc`, army.loc);
        if (army.nextLoc && !provinces.has(army.nextLoc)) add("error", "unknown_army_next_location", `${loc}.nextLoc`, army.nextLoc);
        if (army.dest && !provinces.has(army.dest)) add("error", "unknown_army_destination", `${loc}.dest`, army.dest);
        if (!characterIds.has(army.commanderId)) add("error", "unknown_army_commander", `${loc}.commanderId`, army.commanderId);
        if (!army.warId || !activeWarIds.has(army.warId)) add("warning", "army_without_active_war", `${loc}.warId`, army.warId || "none");
        for (const field of ["size", "morale", "supply", "maxSupply", "dailySupplyUse"]) {
          if ((army[field] || 0) < 0) add("error", "negative_army_number", `${loc}.${field}`, String(army[field]));
        }
        if ((army.supply || 0) > (army.maxSupply || 0) + 0.1) add("warning", "army_supply_over_cap", loc, `${Math.round(army.supply)} / ${Math.round(army.maxSupply || 0)}`);
      }

      if (this.adjacency) {
        for (const [pid, links] of Object.entries(this.adjacency)) {
          if (!provinces.has(pid)) add("error", "unknown_adjacency_source", `adjacency:${pid}`, "Adjacency source is not a seed province.");
          for (const other of links || []) {
            if (!provinces.has(other)) add("error", "unknown_adjacency_target", `adjacency:${pid}`, other);
            if (other === pid) add("error", "self_adjacency", `adjacency:${pid}`, "A province cannot be adjacent to itself.");
            if (this.adjacency[other] && !this.adjacency[other].includes(pid)) {
              add("warning", "asymmetric_adjacency", `adjacency:${pid}->${other}`, "Reverse link is missing.");
            }
          }
        }
      }

      return {
        ok: !issues.some((issue) => issue.severity === "error"),
        checkedAt: this.formatDate(),
        issues,
        counts: {
          factions: this.seed.factions.length,
          provinces: this.seed.provinces.length,
          characters: this.characters.length,
          armies: this.armies.length,
          activeWars: this.wars.filter((w) => !w.over).length,
        },
      };
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
      const ruler = this.rulerOf(fid);
      if (ruler && commander && ruler.id !== commander.id) {
        this._addRelationship(ruler.id, commander.id, "commander", 55, `mustered for ${war.name}`);
      }
      const record = this._ensureMilitaryRecord(commander);
      if (!record.firstCommand) {
        record.firstCommand = { war: war.id, date: this.formatDate(), province: cap.id };
        this._addMemory(commander.id, "first command", `First command: mustered for ${war.name} at ${cap.name}.`, {
          war: war.id, province: cap.id, faction: fid,
        }, { reputation: 2, stress: 2 });
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
      const c = this._hydrateCharacter({
        id: uid("char"),
        name: this.forge.given(f.culture) + " " + this.forge.epithet(),
        species, culture: f.culture, faction: fid, role,
        age: this.rng.int(22, 45), pressure: this.rng.pick(PRESSURE_TEMPLATES),
        prestige: this.rng.int(0, 25), kills: 0,
      }, { isRuler: false });
      this.characters.push(c);
      this._refreshDynastyHouseRecords();
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
      const lc = this.character(loser.commanderId);
      const battleName = `Battle of ${prov.name}`;
      this._recordBattleMemory(winner, "win", battleName, lost, loser.commanderId, {
        province: loc, war: war.id, faction: winner.faction, character: winner.commanderId,
      });
      this._recordBattleMemory(loser, "loss", battleName, lost, winner.commanderId, {
        province: loc, war: war.id, faction: loser.faction, character: loser.commanderId,
      });
      if (wc) {
        wc.prestige += 12; wc.kills += lost;
        wc.reputation = this._clampPolitics((wc.reputation || 0) + 6);
        wc.stress = this._clampPolitics((wc.stress || 0) + 3);
        wc.wealth += 15;
      }
      this.factionState[winner.faction].prestige += 6;
      this.factionState[loser.faction].exhaustion += 7;
      this.factionState[winner.faction].exhaustion += 3;

      this.log(3, "battle",
        `${this.faction(winner.faction).name} wins the Battle of ${prov.name} — ${lost.toLocaleString()} of ${this.faction(loser.faction).name}'s soldiers fall${wc ? "; " + wc.name + " takes the field" : ""}.`,
        { province: loc, war: war.id, faction: winner.faction, character: winner.commanderId });

      // commander of the losing side may fall
      if (lc) {
        lc.stress = this._clampPolitics((lc.stress || 0) + 9);
        lc.health = this._clampPolitics((lc.health || 0) - 4);
      }
      if (lc && this.rng.chance(0.18)) {
        this._recordWound(lc.id, `${lc.name} is wounded in the ${battleName}.`, {
          province: loc, war: war.id, character: lc.id,
        });
      }
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
        const commander = this.character(army.commanderId);
        if (commander) this._ensureMilitaryRecord(commander).siegesLed += 1;
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
        this._addMemory(army.commanderId, "promotion", `${this.character(army.commanderId)?.name || "The commander"} led the fall of ${prov.name}.`, {
          province: army.loc, war: war.id, faction: army.faction, character: army.commanderId,
        }, { reputation: 3, prestige: 4 });
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
        this._refreshCourt(f.id);
        this._updateInternalPolitics(f.id);
        const s = this.factionState[f.id];
        if (!s.economy) s.economy = { warDebt: 0, foodStress: 0, tradeValue: 0, devastationLoss: 0, tributeDue: 0, lastDecision: null };
        const before = this.economySnapshot(f.id);
        this._survivalEconomyDecision(f.id, before);
        const economy = this.economySnapshot(f.id);
        const court = Math.max(0, Math.round(s.treasury * 0.02));
        const debtPay = Math.min(s.treasury + economy.income, economy.debtService);
        s.economy.warDebt = Math.max(0, s.economy.warDebt - debtPay);
        s.economy.foodStress = economy.foodStress;
        s.economy.tradeValue = economy.tradeValue;
        s.economy.devastationLoss = economy.devastationLoss;
        s.economy.tributeDue = economy.tributeDue;
        s.treasury += economy.income - economy.upkeep - court - debtPay;
        if (s.treasury < 0) {
          s.exhaustion += 4 + Math.min(6, Math.ceil(Math.abs(s.treasury) / 120));
          s.economy.warDebt += Math.ceil(Math.abs(s.treasury) * 0.65);
          s.treasury = 0;
        }
        if (s.economy.foodStress >= 58) s.exhaustion += 1.5;
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
      this._revoltPulse();
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
      if (!this.adjacency) return false;
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
        const op = this.opinion(a, b) + this._relationshipDiplomacyBias(a, b);
        if (op > -10) continue;

        for (const [agg, def] of [[a, b], [b, a]]) {
          if (this.warsOf(agg).length >= 1) continue;   // one war at a time
          if (this.factionState[agg].exhaustion > 30) continue;
          const claim = this.claims.find((c) => c.claimant === agg &&
            this.provinceState[c.target] && this.provinceState[c.target].controller === def);
          const isRaider = this.faction(agg).government === "seasonal_khan_ring";
          if (!claim && !isRaider && !this._factionsBorder(agg, def)) continue;

          let p = (rel.warRisk / 100) * 0.052 * this._traitFactor(agg, "war") * this._tierWeight(agg);
          if (claim) p *= 1 + claim.strength / 120;
          if (this.armyStrength(def) > 0) p *= 0.4;     // hesitant while target mobilized
          if (this.factionState[agg].treasury < 100) p *= 0.4;
          p *= this._priorityWarMultiplier(agg, def, claim, isRaider && !claim);
          p *= this._rulerWarDriveMultiplier(agg, def, claim, isRaider && !claim);
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
      const priority = this.aiPriorityScores(attacker, defender)[0];
      const motive = priority ? ` The court priority is ${priority.label.toLowerCase()}: ${priority.reason}.` : "";
      const drive = this._warDriveText(attacker, defender, claim, isRaid);
      if (claim) {
        return `${attackerName} goes to war to press a ${claim.type} claim on ${this.province(claim.target).name}.${motive}${drive}`;
      }
      if (isRaid) {
        return `${attackerName} rides for plunder because ${defenderName} is close enough to raid.${motive}${drive}`;
      }
      return `${attackerName} escalates a frontier quarrel with ${defenderName}.${motive}${drive}`;
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
        `${this.faction(attacker).name} declares war on ${this.faction(defender).name}, ${reason}. The prize: ${prizeName}. Cause: ${war.intentReason}.`,
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
        const ea = this.economySnapshot(war.attacker), ed = this.economySnapshot(war.defender);
        // exhaustion pushes both sides to the table
        if (war.score >= 55) { this._endWar(war, war.attacker, "attacker war score became decisive"); continue; }
        if (sd.exhaustion >= 65) { this._endWar(war, war.attacker, "defender exhaustion broke their bargaining position"); continue; }
        if (war.score <= -45) { this._endWar(war, war.defender, "defender war score held firm"); continue; }
        if (sa.exhaustion >= 65) { this._endWar(war, war.defender, "attacker exhaustion made the offensive collapse"); continue; }
        if (ea && ea.net < -180 && ea.warDebt > 850) { this._endWar(war, war.defender, "attacker war debt made the offensive unaffordable"); continue; }
        if (ed && ed.net < -180 && ed.warDebt > 850) { this._endWar(war, war.attacker, "defender war debt broke their ability to resist"); continue; }
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
          const losingRuler = this.rulerOf(war.defender);
          const winningRuler = this.rulerOf(war.attacker);
          if (losingRuler) {
            this._addMemory(losingRuler.id, "lost province", `${prov.name} was ceded to ${att.name} after ${war.name}.`, {
              province: prov.id, war: war.id, faction: war.defender,
            }, {
              reputation: -4, stress: 8,
              grudgeAgainst: winningRuler && winningRuler.id,
              grudgeType: "rival",
              grudgeStrength: 58,
            });
          }
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
      const parent = this.character(cid);
      const explicit = parent && parent.family ? parent.family.children : [];
      return this.characters.filter((c) =>
        c.parentId === cid ||
        (c.family && (c.family.father === cid || c.family.mother === cid)) ||
        explicit.includes(c.id));
    }

    heirOf(fid) {
      const ruler = this.rulerOf(fid);
      if (!ruler) return null;
      const kids = this.childrenOf(ruler.id).filter((c) => c.alive)
        .sort((a, b) => {
          const score = this.inheritanceScore(b) - this.inheritanceScore(a);
          if (Math.abs(score) > 0.01) return score;
          const ar = a.family && a.family.inheritanceRank !== null ? a.family.inheritanceRank : 999;
          const br = b.family && b.family.inheritanceRank !== null ? b.family.inheritanceRank : 999;
          return ar - br || b.age - a.age;
        });
      return kids[0] || null;
    }

    _fertility(species, age) {
      if (species === "elf") return age >= 60 && age <= 280 ? 0.04 : 0;
      if (species === "dwarf") return age >= 30 && age <= 100 ? 0.08 : 0;
      return age >= 18 && age <= 50 ? 0.16 : 0;
    }

    _maybeFormCadetBranches() {
      for (const f of this.seed.factions) {
        const ruler = this.rulerOf(f.id);
        if (!ruler || !ruler.alive) continue;
        const owned = this.ownedProvinces(f.id);
        if (owned.length < 2) continue;
        const heir = this.heirOf(f.id);
        const candidates = this.childrenOf(ruler.id)
          .filter((c) => c.alive && c.age >= 16 && c.id !== (heir && heir.id))
          .filter((c) => c.family && c.family.branchType !== "cadet")
          .sort((a, b) => this.inheritanceScore(b) - this.inheritanceScore(a));
        const chosen = candidates[0];
        if (!chosen) continue;
        const pressure = this.factionState[f.id]?.internal?.regionalAutonomy || 0;
        const rank = chosen.family.inheritanceRank || 99;
        const shouldBranch = rank > 1 && (owned.length >= 3 || pressure >= 45 || chosen.family.legitimised);
        if (!shouldBranch) continue;
        const branch = this.formCadetBranch(chosen.id, chosen.family.legitimised ? "legitimised_bastard" : "younger_child_landed");
        if (!branch) continue;
        chosen.prestige = Math.round((chosen.prestige || 0) + 8);
        chosen.family.claimStrength = this._clampPolitics((chosen.family.claimStrength || 0) + 8);
        this.log(2, "succession",
          `${chosen.name} founds ${branch.name}, a cadet branch of ${chosen.family.dynasty}, after receiving lands away from the main inheritance.`,
          { faction: f.id, character: chosen.id });
      }
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
        const child = this._hydrateCharacter({
          id: uid("char"),
          name: this.forge.given(ruler.culture) + (dynasty ? " " + dynasty : ""),
          species: ruler.species, culture: ruler.culture, faction: f.id,
          role: "scion of the ruling line", age: 0,
          pressure: "must grow into a name that is already spoken for",
          prestige: 0, kills: 0, parentId: ruler.id,
          family: {
            father: ruler.id,
            dynasty: ruler.family?.dynasty || dynasty || this._houseName(f),
            house: ruler.family?.house || this._houseName(f),
            inheritanceRank: brood.length + 1,
            claimStrength: 35,
            legitimacy: 58,
          },
        }, { isRuler: false });
        this.characters.push(child);
        this._syncFamilyLinks();
        this._refreshDynastyHouseRecords();
        this._addRelationship(ruler.id, child.id, "parent", 92, "born into the ruling line");
        this.log(2, "birth",
          `A child is born to ${ruler.name}: the ${f.name} court swears the oaths over ${child.name}.`,
          { faction: f.id, character: child.id });
      }

      for (const c of this.characters) {
        if (!c.alive) continue;
        c.age += 1;
        c.stress = this._clampPolitics((c.stress || 0) + (c.isRuler && this.warsOf(c.faction).length ? 4 : -2));
        c.health = this._clampPolitics((c.health || 0) - Math.max(0, c.stress - 70) * 0.03);
        const sp = this.seed.species[c.species] || { oldAge: 55, maxAge: 95 };
        let deathChance = 0.006;
        if (c.age > sp.oldAge) {
          deathChance = 0.03 + 0.30 * (c.age - sp.oldAge) / Math.max(1, sp.maxAge - sp.oldAge);
        }
        deathChance += Math.max(0, 35 - (c.health || 70)) / 450;
        if (this.rng.chance(deathChance)) {
          this._kill(c, c.age > sp.oldAge ? "dies full of years" : "is carried off by fever");
        }
      }
      this._maybeFormCadetBranches();
      // claims fade or fester
      for (const claim of this.claims) {
        claim.strength = Math.max(5, claim.strength - 0.5);
      }
    }

    _kill(character, causeText) {
      character.alive = false;
      character.deathYear = this.date.year;
      character.health = 0;
      const f = this.faction(character.faction);
      const state = this.factionState[character.faction];
      const wasRuler = this.factionState[character.faction] &&
        this.factionState[character.faction].rulerId === character.id;
      // a mage bound to this character dies with them
      const mage = this.mages.find((m) => m.character === character.id && m.alive);
      if (mage) mage.alive = false;
      const family = [
        ...this.childrenOf(character.id),
        ...this.closeFamilyOf(character.id).parents,
        ...this.closeFamilyOf(character.id).siblings,
      ].filter(Boolean);
      for (const kin of family) {
        this._addMemory(kin.id, "family death", `${character.name} ${causeText}.`, {
          character: character.id, faction: character.faction,
        }, { stress: 6 });
      }

      if (!wasRuler) {
        this.log(2, "death", `${character.name}, ${character.role} of ${f.name}, ${causeText}.`,
          { faction: character.faction, character: character.id });
        this._refreshCourt(character.faction);
        return;
      }
      // succession: legitimacy, regency and crisis all matter now.
      const children = this.childrenOf(character.id).filter((c) => c.alive)
        .sort((a, b) => {
          const score = this.inheritanceScore(b) - this.inheritanceScore(a);
          if (Math.abs(score) > 0.01) return score;
          const ar = a.family && a.family.inheritanceRank !== null ? a.family.inheritanceRank : 999;
          const br = b.family && b.family.inheritanceRank !== null ? b.family.inheritanceRank : 999;
          return ar - br || b.age - a.age;
        });
      let heir = children[0] || null;
      if (!heir) {
        const dynasty = character.name.split(" ").slice(1).join(" ");
        heir = this._hydrateCharacter({
          id: uid("char"),
          name: this.forge.given(f.culture) + (dynasty ? " " + dynasty : " " + this.forge.epithet()),
          species: character.species, culture: character.culture, faction: character.faction,
          role: character.role, age: Math.max(16, this.rng.int(17, 40)),
          pressure: this.rng.pick(PRESSURE_TEMPLATES),
          prestige: Math.round(character.prestige * 0.3), kills: 0,
          family: {
            dynasty: character.family?.dynasty || dynasty || this._houseName(f),
            house: character.family?.house || this._houseName(f),
            inheritanceRank: 1,
            claimStrength: 58,
            legitimacy: 42,
          },
        }, { isRuler: true, reignStart: this.date.year });
        this.characters.push(heir);
        this._refreshDynastyHouseRecords();
      } else {
        this._ensureCharacterState(heir, { isRuler: true, reignStart: this.date.year });
      }
      heir.isRuler = true;
      heir.role = character.role;
      heir.reignStart = this.date.year;
      heir.prestige += Math.round(character.prestige * 0.3);
      heir.reputation = this._clampPolitics((heir.reputation || 0) + Math.round(character.reputation || 0) * 0.2);
      const regency = heir.age < 16;
      heir.pressure = regency
        ? "must survive the regents who rule in their name"
        : this.rng.pick(PRESSURE_TEMPLATES);
      if (!state.succession) state.succession = this._initialSuccessionState(character.faction);
      const legitimacy = this.heirLegitimacy(character.faction, heir);
      const crisisRisk = this._clampPolitics((100 - legitimacy) * 0.45 + (state.internal ? state.internal.successionPressure * 0.40 : 0));
      const crisis = legitimacy < 38 || crisisRisk >= 58;
      const captain = this.characters
        .filter((c) => c.alive && c.faction === character.faction && c.id !== heir.id)
        .sort((a, b) => (b.prestige || 0) + (b.kills || 0) * 0.02 - ((a.prestige || 0) + (a.kills || 0) * 0.02))[0];
      const backing = captain
        ? `${captain.name} and the army captains`
        : (state.internal && state.internal.nobleLoyalty < 40 ? "restless nobles" : "court factions");
      state.rulerId = heir.id;
      this._refreshDynastyHouseRecords();
      state.succession.regency = regency;
      state.succession.heirLegitimacy = legitimacy;
      state.succession.lastTransition = {
        day: this.day,
        date: this.formatDate(),
        from: character.id,
        to: heir.id,
        outcome: crisis ? "crisis" : regency ? "regency" : "stable",
        legitimacy,
      };
      const line = children.length
        ? (regency
          ? `${heir.name} is but ${heir.age}; a regency council rules ${f.name} in their name.`
          : `${heir.name}, ${heir.age} years old, inherits rule of ${f.name}.`)
        : `The direct line is broken: ${heir.name}, a kin of the house, takes up rule of ${f.name}.`;
      if (crisis) {
        const pretender = captain && captain.id !== heir.id
          ? captain
          : this._spawnCharacter(character.faction, "pretender claimant");
        const cap = this.capital(character.faction);
        const pretenderRecord = {
          character: pretender.id,
          backing,
          claimStrength: this._clampPolitics(62 + (state.internal ? state.internal.successionPressure * 0.25 : 0)),
          started: this.formatDate(),
        };
        state.succession.crisis = {
          started: this.formatDate(),
          reason: `heir legitimacy ${legitimacy} and succession pressure ${state.internal ? state.internal.successionPressure : 0}`,
          backing,
        };
        state.succession.pretenders = [pretenderRecord, ...(state.succession.pretenders || [])].slice(0, 4);
        state.exhaustion += 8;
        if (state.internal) {
          state.internal.courtTension = Math.min(100, state.internal.courtTension + 14);
          state.internal.successionTension = Math.min(100, state.internal.successionTension + 18);
          state.internal.revoltRisk = Math.min(100, state.internal.revoltRisk + 10);
        }
        if (cap) {
          this.claims.push({
            id: uid("claim"), claimant: character.faction, target: cap.id,
            type: "pretender claim", source: `${pretender.name}'s succession challenge, ${this.formatDate()}`,
            strength: pretenderRecord.claimStrength, myth: "living memory", recognizedBy: f.religion,
          });
          if (state.internal && state.internal.successionPressure >= 70) this._startRevolt(cap.id, "pretender_revolt");
        }
      } else {
        state.succession.crisis = null;
        state.succession.pretenders = [];
        if (state.internal) {
          state.internal.successionTension = Math.max(0, state.internal.successionTension - 12);
          state.internal.successionPressure = Math.max(0, state.internal.successionPressure - 16);
        }
      }
      this.log(3, "succession",
        `${character.name} ${causeText}. ${line} ${crisis ? `Succession crisis follows: ${backing} back a rival claim.` : regency ? "The regency must prove it can keep the realm together." : "The succession is accepted without open crisis."}`,
        { faction: character.faction, character: heir.id });
      this._refreshCourt(character.faction);
    }
  }

  window.WG = window.WG || {};
  window.WG.Simulation = Simulation;
  window.WG.MONTH_NAMES = MONTH_NAMES;
})();

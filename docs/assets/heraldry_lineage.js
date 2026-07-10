/* Hierarchical heraldry (v2 layer): arms for provinces, dynasties, houses
   and individual characters, layered over the realm engine in heraldry.js.

   Conventions, the way CK2 does them:
   - Province arms are "arms of dominion, differenced": the ruling realm's
     field colour, a chief of allegiance in the realm's contrast tincture,
     and a local charge drawn from the province's terrain feature or
     resource. Watery terrain takes wavy lines and often a wavy blue
     terrace in base. When a province changes hands its arms re-render in
     the new realm's colours.
   - Dynasty arms are independent of any realm (a dynasty can outlive or
     migrate between realms), seeded from the dynasty id and obeying the
     rule of tincture (metal on colour, colour on metal).
   - House arms are the dynasty arms with systematic cadency: 1st cadet
     line a label, 2nd a bordure, 3rd a canton, later branches marks in
     chief. A house founded by a legitimised bastard bears the bend
     sinister over all (driven by the sim's `cadetReason`).
   - Character arms: rulers and house heads bear the house arms
     undifferenced; everyone else takes a small personal cadency mark in
     chief keyed to `family.inheritanceRank`. An unlegitimised bastard
     bears a personal bend sinister.

   Everything is deterministic (FNV-1a -> mulberry32) and renders through
   the bundled Armoria, so the same entity always bears the same arms.

   API:
     WG.provinceShield(province, realmFaction, size)
     WG.dynastyShield(dynasty, size)
     WG.houseShield(house, dynasty, size)
     WG.characterShield(character, house, dynasty, size)
     WG.coaFor(entity, ctx)  -> { coa, colors } for anything */
(function () {
  "use strict";

  const H = window.WG.heraldryHelpers;
  const ARMORIA_BASE_PATH = "assets/armoria/index.html";

  const METALS = ["or", "argent"];
  const COLOURS = ["gules", "azure", "vert", "sable", "purpure"];
  const DIVISIONS = ["perPale", "perFess", "perBend", "perCross", "perSaltire"];
  const ORDINARIES = ["pale", "fess", "bend", "chevron", "cross", "saltire"];
  const NOBLE_CHARGES = [
    "lionRampant", "lionPassant", "eagle", "stagPassant", "bearRampant",
    "wolfRampant", "boarRampant", "horseRampant", "unicornRampant",
    "griffinRampant", "dragonRampant", "falcon", "raven", "swan", "owl",
    "wyvern",
  ];
  /* the classic cadency series, used for personal marks in chief */
  const CADENCY_MARKS = [
    "label", "crescent", "mullet", "annulet", "rose",
    "fleurDeLis", "crossMoline", "lozenge",
  ];
  /* local charges of dominion: terrain feature first, then resource */
  const TERRAIN_CHARGES = {
    mountain_pass: ["tower"],
    river_city: ["bridge", "lymphad", "anchor"],
    river_port: ["bridge", "lymphad", "anchor"],
    canal_farmland: ["garb", "tree", "wheel"],
    frontier_farms: ["garb", "tree", "wheel"],
    bog_forest: ["tree", "oak"],
    charter_city: ["scrollClosed", "castle"],
    steppe_market: ["horseshoe", "wheel"],
    sacred_battlefield: ["crossMoline", "sword"],
  };
  const RESOURCE_CHARGES = {
    GRAIN: ["garb"],
    HORSES: ["horseshoe"],
    IRON: ["sword", "axe"],
    SILVER: ["roundel", "lozenge"],
    INFLUENCE: ["scale", "bookClosed"],
  };
  const WATERY_FEATURES = new Set(["river_city", "river_port", "canal_farmland", "bog_forest"]);

  /* ---------- deterministic seeding ---------- */

  function fnv1a(str) {
    let h = 2166136261 >>> 0;
    const s = String(str);
    for (let i = 0; i < s.length; i += 1) {
      h ^= s.charCodeAt(i);
      h = Math.imul(h, 16777619);
    }
    return h >>> 0;
  }

  function mulberry32(seed) {
    let a = seed >>> 0;
    return function () {
      a = (a + 0x6d2b79f5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  function rngFor(key) { return mulberry32(fnv1a(key)); }
  function pick(rng, list) { return list[Math.floor(rng() * list.length)]; }

  /* ---------- Armoria rendering ---------- */

  function coaSrc(coa, colors, size) {
    const sizeParam = size ? `&size=${Math.max(48, Math.round(Number(size) * 4))}` : "";
    const colorParam = colors && Object.keys(colors).length
      ? `&colors=${encodeURIComponent(JSON.stringify(colors))}` : "";
    return `${ARMORIA_BASE_PATH}?coa=${encodeURIComponent(JSON.stringify(coa))}${colorParam}&view=1${sizeParam}`;
  }

  function coaShieldSVG(result, size, label) {
    if (!result) return "";
    const width = Math.max(12, Math.round(Number(size) || 30));
    const height = Math.round(width * 1.1);
    return `<span class="wg-shield wg-armoria-shield"
      style="--wg-shield-w:${width}px; --wg-shield-h:${height}px"
      aria-label="${H.escAttr(label)}"
      title="${H.escAttr(label)}">
      <iframe
        class="wg-armoria-badge-frame"
        src="${H.escAttr(coaSrc(result.coa, result.colors, width))}"
        width="${width}"
        height="${height}"
        frameborder="0"
        scrolling="no"
        allowtransparency="true"
        loading="lazy"
        tabindex="-1"
        aria-hidden="true">
      </iframe>
    </span>`;
  }

  /* ---------- province arms: dominion, differenced ---------- */

  function provinceCoa(province, realmFaction) {
    const p = province || {};
    const realm = realmFaction || {};
    const fieldColor = H.normalizeHexColor(realm.color) || "#777777";
    const field = H.customTinctureName(fieldColor) || "sable";
    const contrast = H.chargeTinctureForField(fieldColor);
    const rng = rngFor(`prov:${p.id || p.name || "unknown"}`);
    const feature = p.terrainFeature || p.terrain || "";
    const watery = WATERY_FEATURES.has(feature);
    const options = TERRAIN_CHARGES[feature] ||
      RESOURCE_CHARGES[String(p.resource || "").toUpperCase()] || ["roundel"];
    const coa = {
      seed: fnv1a(`prov:${p.id || p.name}`),
      shield: "heater",
      zoom: 0.78,
      t1: field,
      ordinaries: [{ ordinary: "chief", t: contrast, line: watery ? "wavy" : "straight" }],
      charges: [{ charge: pick(rng, options), t: contrast, p: "e", size: 0.68 }],
    };
    if (feature === "mountain_pass") {
      coa.ordinaries.push({ ordinary: "mount", t: contrast });
    } else if (watery && rng() < 0.6) {
      coa.ordinaries.push({ ordinary: "terrace", t: "azure", line: "wavy" });
    }
    return { coa, colors: field.indexOf("wg_") === 0 ? { [field]: fieldColor } : {} };
  }

  /* ---------- dynasty arms: independent of any realm ---------- */

  function dynastyParts(dynasty) {
    const d = dynasty || {};
    const key = `dyn:${d.id || d.name || "lowborn"}`;
    const rng = rngFor(key);
    const colour = pick(rng, COLOURS);
    const metal = pick(rng, METALS);
    const coa = { seed: fnv1a(key), shield: "heater", zoom: 0.78, t1: colour };
    if (rng() < 0.4) {
      coa.division = { division: pick(rng, DIVISIONS), t: metal, line: "straight" };
    }
    if (rng() < 0.45) {
      coa.ordinaries = [{ ordinary: pick(rng, ORDINARIES), t: metal, line: "straight" }];
    }
    /* metal on colour: the noble charge always contrasts the field */
    coa.charges = [{ charge: pick(rng, NOBLE_CHARGES), t: metal, p: "e", size: coa.ordinaries ? 0.62 : 0.72 }];
    return { coa, colour, metal };
  }

  function dynastyCoa(dynasty) {
    const parts = dynastyParts(dynasty);
    return { coa: parts.coa, colors: {} };
  }

  /* ---------- house arms: dynasty arms plus cadency ---------- */

  function cadetOrder(house, dynasty) {
    const branches = (dynasty && dynasty.cadetBranches) || [];
    const idx = branches.findIndex((b) => b === house.id || (b && (b.id === house.id || b.house === house.id)));
    if (idx >= 0) return idx + 1;
    return 1 + (fnv1a(`house:${house.id || house.name}`) % 5);
  }

  function brisure(coa, briT, order) {
    coa.ordinaries = coa.ordinaries || [];
    coa.charges = coa.charges || [];
    if (order === 1) coa.charges.push({ charge: "label", t: briT, p: "b", size: 0.85 });
    else if (order === 2) coa.ordinaries.push({ ordinary: "bordure", t: briT });
    else if (order === 3) coa.ordinaries.push({ ordinary: "canton", t: briT });
    else coa.charges.push({ charge: CADENCY_MARKS[(order - 3) % CADENCY_MARKS.length], t: briT, p: "b", size: 0.22 });
  }

  function houseParts(house, dynasty) {
    const dyn = dynasty || (house && house.dynastyId ? { id: house.dynastyId } : house);
    const parts = dynastyParts(dyn);
    /* brisures take the metal the dynasty arms do not lean on */
    const briT = parts.metal === "or" ? "argent" : "or";
    if (!house || house.branchType !== "cadet") {
      return { coa: parts.coa, colors: {}, metal: parts.metal, briT };
    }
    const coa = parts.coa;
    brisure(coa, briT, cadetOrder(house, dynasty));
    if (/bastard/i.test(String(house.cadetReason || ""))) {
      coa.ordinaries = coa.ordinaries || [];
      coa.ordinaries.push({ ordinary: "bendSinister", t: briT, above: 1 });
    }
    return { coa, colors: {}, metal: parts.metal, briT };
  }

  function houseCoa(house, dynasty) {
    const parts = houseParts(house, dynasty);
    return { coa: parts.coa, colors: parts.colors };
  }

  /* ---------- character arms: personal difference ---------- */

  function characterCoa(character, house, dynasty) {
    const c = character || {};
    const family = c.family || {};
    const parts = houseParts(house, dynasty);
    const coa = parts.coa;
    const isHead = Boolean((house && house.head === c.id) || (dynasty && dynasty.head === c.id));
    if (family.bastard && !family.legitimised) {
      coa.ordinaries = coa.ordinaries || [];
      coa.ordinaries.push({ ordinary: "bendSinister", t: parts.briT, above: 1 });
    }
    if (!isHead && !c.isRuler) {
      const rank = Number(family.inheritanceRank);
      const index = Number.isFinite(rank) && rank > 0
        ? (rank - 1) % CADENCY_MARKS.length
        : fnv1a(`char:${c.id || c.name}`) % CADENCY_MARKS.length;
      const mark = CADENCY_MARKS[index];
      coa.charges = coa.charges || [];
      coa.charges.push({ charge: mark, t: parts.briT, p: "b", size: mark === "label" ? 0.85 : 0.22 });
    }
    return { coa, colors: parts.colors };
  }

  /* ---------- dispatcher ---------- */

  function coaFor(entity, ctx) {
    const context = ctx || {};
    if (!entity) return null;
    if (entity.family) return characterCoa(entity, context.house, context.dynasty);
    if (entity.branchType) return houseCoa(entity, context.dynasty);
    if (Array.isArray(entity.cadetBranches) || entity.renown !== undefined) return dynastyCoa(entity);
    if (entity.terrainFeature || entity.terrain || entity.resource) {
      return provinceCoa(entity, context.realm || context.faction);
    }
    return dynastyCoa(entity);
  }

  /* ---------- shield renderers ---------- */

  function provinceShield(province, realmFaction, size) {
    if (!province) return "";
    const label = `${province.name || province.id || "Province"} coat of arms`;
    return coaShieldSVG(provinceCoa(province, realmFaction), size, label);
  }

  function dynastyShield(dynasty, size) {
    if (!dynasty) return "";
    const label = `Dynasty ${dynasty.name || dynasty.id} coat of arms`;
    return coaShieldSVG(dynastyCoa(dynasty), size, label);
  }

  function houseShield(house, dynasty, size) {
    if (!house) return "";
    const label = `House ${house.name || house.id} coat of arms`;
    return coaShieldSVG(houseCoa(house, dynasty), size, label);
  }

  function characterShield(character, house, dynasty, size) {
    if (!character) return "";
    const label = `Personal arms of ${character.name || character.id}`;
    return coaShieldSVG(characterCoa(character, house, dynasty), size, label);
  }

  window.WG = window.WG || {};
  window.WG.provinceShield = provinceShield;
  window.WG.dynastyShield = dynastyShield;
  window.WG.houseShield = houseShield;
  window.WG.characterShield = characterShield;
  window.WG.coaFor = coaFor;
  window.WG.lineageHeraldry = {
    provinceCoa, dynastyCoa, houseCoa, characterCoa, coaSrc, fnv1a, mulberry32,
  };
})();

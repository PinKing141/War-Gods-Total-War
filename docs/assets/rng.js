/* Deterministic RNG + value noise + name generation.
   Plain script (no modules) so the app also works when opened from file://. */
(function () {
  "use strict";

  function mulberry32(seed) {
    let a = seed >>> 0;
    return function () {
      a |= 0; a = (a + 0x6D2B79F5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  function hashStr(str) {
    let h = 2166136261;
    for (let i = 0; i < str.length; i++) {
      h ^= str.charCodeAt(i);
      h = Math.imul(h, 16777619);
    }
    return h >>> 0;
  }

  class Rng {
    constructor(seed) { this.next = mulberry32(seed); }
    float(min, max) { return min + this.next() * (max - min); }
    int(min, max) { return Math.floor(this.float(min, max + 1)); }
    chance(p) { return this.next() < p; }
    pick(arr) { return arr[Math.floor(this.next() * arr.length)]; }
  }

  /* ---- 2D value noise with fbm, used for coastlines and border warping ---- */
  function makeNoise(seed) {
    const perm = new Uint8Array(512);
    const rng = mulberry32(seed);
    const p = new Uint8Array(256);
    for (let i = 0; i < 256; i++) p[i] = i;
    for (let i = 255; i > 0; i--) {
      const j = Math.floor(rng() * (i + 1));
      const t = p[i]; p[i] = p[j]; p[j] = t;
    }
    for (let i = 0; i < 512; i++) perm[i] = p[i & 255];

    function grad(ix, iy) { return perm[(ix & 255) + perm[iy & 255]] / 255; }
    function smooth(t) { return t * t * (3 - 2 * t); }

    function noise2(x, y) {
      const x0 = Math.floor(x), y0 = Math.floor(y);
      const fx = x - x0, fy = y - y0;
      const v00 = grad(x0, y0), v10 = grad(x0 + 1, y0);
      const v01 = grad(x0, y0 + 1), v11 = grad(x0 + 1, y0 + 1);
      const sx = smooth(fx), sy = smooth(fy);
      const a = v00 + (v10 - v00) * sx;
      const b = v01 + (v11 - v01) * sx;
      return a + (b - a) * sy; // 0..1
    }

    function fbm(x, y, octaves) {
      let value = 0, amp = 0.5, freq = 1;
      for (let o = 0; o < octaves; o++) {
        value += amp * noise2(x * freq, y * freq);
        amp *= 0.5; freq *= 2;
      }
      return value; // ~0..1
    }

    return { noise2, fbm };
  }

  /* ---- Culture-aware name generation for heirs and captains ---- */
  const VOWELS = ["a", "e", "o", "u", "i"];
  const EPITHETS = [
    "the Younger", "the Quiet", "Ironhand", "the Vigilant", "Threefold",
    "the Unbowed", "Riverborn", "the Grey", "Oathkeeper", "the Patient",
    "Stormcounted", "the Bold", "Halfbridge", "the Lastborn", "Winterled",
  ];

  function cap(s) { return s.charAt(0).toUpperCase() + s.slice(1); }

  function makeNameForge(seedData, rng) {
    function given(cultureId) {
      const parts = seedData.naming[cultureId];
      if (!parts || !parts.roots.length) {
        return cap(rng.pick(["ara", "ben", "cor", "dal", "mor"])) + rng.pick(["an", "is", "eth"]);
      }
      const root = rng.pick(parts.roots);
      const suffix = parts.suffixes.length ? rng.pick(parts.suffixes) : "an";
      let name = root;
      if (!VOWELS.includes(root.charAt(root.length - 1)) &&
          !VOWELS.includes(suffix.charAt(0))) {
        name += rng.pick(VOWELS);
      }
      name += suffix;
      return cap(name);
    }
    function epithet() { return rng.pick(EPITHETS); }
    return { given, epithet };
  }

  window.WG = window.WG || {};
  window.WG.Rng = Rng;
  window.WG.hashStr = hashStr;
  window.WG.makeNoise = makeNoise;
  window.WG.makeNameForge = makeNameForge;
})();

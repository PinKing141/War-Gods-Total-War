/* Coat-of-arms bridge: Armoria renders the live heraldry, while the small
   fallback SVG keeps the old dashboard badges available for debugging. */
(function () {
  "use strict";

  const ARMORIA_BASE_PATH = "assets/armoria/index.html";
  const GOLD = "#e8c96a";
  const ARMORIA_CHARGES = {
    bridge: "bridge",
    cairn: "tower",
    gate: "portcullis",
    peak: "triangle",
    scroll: "scrollClosed",
    bell: "bell",
    horseshoe: "horseshoe",
    banners: "banner",
  };
  const NON_KINGDOM_HERALDRY_TYPES = new Set(["house", "dynasty", "character", "person", "army", "unit"]);
  const KINGDOM_BLAZONS = {
    FAC_ROV_HALEN: {
      ordinaries: [{ ordinary: "fess", t: "white", line: "wavy" }],
      charges: [{ charge: "bridge", t: "gold", t2: "fieldContrast", p: "e", size: 0.72 }],
    },
    FAC_KAERN_RED_BOG: {
      ordinaries: [{ ordinary: "bordure", t: "gold" }],
      charges: [{ charge: "tower", t: "gold", t2: "black", p: "e", size: 0.82 }],
    },
    FAC_GHARU_OPEN_GATE: {
      ordinaries: [{ ordinary: "orle", t: "white" }],
      charges: [{ charge: "portcullis", t: "gold", t2: "black", p: "e", size: 0.82 }],
    },
    FAC_KAVARI_WEST_GEAR: {
      ordinaries: [{ ordinary: "chevron", t: "white" }],
      charges: [{ charge: "gear", t: "gold", p: "h", size: 0.68 }],
    },
    FAC_NALARI_THIRD_CHARTER: {
      ordinaries: [{ ordinary: "bordure", t: "gold" }],
      charges: [{ charge: "scrollClosed", t: "white", t2: "gold", p: "e", size: 0.82 }],
    },
    FAC_MAREN_BLUE_CHAIN: {
      ordinaries: [{ ordinary: "fess", t: "white", line: "wavy" }],
      charges: [{ charge: "chain", t: "gold", p: "e", size: 0.76 }],
    },
    FAC_TALUUN_WHITE_MARE: {
      ordinaries: [{ ordinary: "bordure", t: "black" }],
      charges: [{ charge: "horsePassant", t: "white", t2: "black", p: "e", size: 0.82 }],
    },
    FAC_NINE_BANNERS_HALLOW: {
      ordinaries: [{ ordinary: "cross", t: "gold" }],
      charges: [{ charge: "lanceWithBanner", t: "white", t2: "red", p: "e", size: 0.72 }],
    },
    FAC_LANTER_SEA_LEAGUE: {
      ordinaries: [{ ordinary: "fess", t: "white", line: "wavy" }],
      charges: [{ charge: "anchor", t: "gold", p: "e", size: 0.82 }],
    },
    FAC_NORTHGREY_HIGHLANDS: {
      ordinaries: [{ ordinary: "mount", t: "white" }],
      charges: [{ charge: "tower", t: "gold", t2: "black", p: "e", size: 0.8 }],
    },
    FAC_QERESH_SALT_ROAD: {
      ordinaries: [{ ordinary: "bend", t: "white" }],
      charges: [{ charge: "horseshoe", t: "black", p: "e", size: 0.82 }],
    },
    FAC_EASTERN_REED_CONFED: {
      ordinaries: [{ ordinary: "fess", t: "white", line: "wavy" }],
      charges: [{ charge: "portcullis", t: "gold", t2: "black", p: "e", size: 0.76 }],
    },
    FAC_OSTREN_BANNERFIELDS: {
      ordinaries: [{ ordinary: "chevron", t: "black" }],
      charges: [{ charge: "lanceWithBanner", t: "red", t2: "gold", p: "e", size: 0.78 }],
    },
    FAC_SALT_WITNESS_PROTECTORATE: {
      ordinaries: [{ ordinary: "bendSinister", t: "white" }],
      charges: [{ charge: "scale", t: "black", p: "e", size: 0.82 }],
    },
    FAC_GREEN_CROWN_COURT: {
      ordinaries: [{ ordinary: "orle", t: "white" }],
      charges: [{ charge: "crown", t: "gold", t2: "red", p: "e", size: 0.86 }],
    },
    FAC_DEEP_LEDGER_HOLD: {
      ordinaries: [{ ordinary: "chief", t: "black" }],
      charges: [{ charge: "bookClosed", t: "gold", t2: "white", p: "e", size: 0.82 }],
    },
  };
  const CHARGES = {
    bridge: '<path d="M8 26 h24 v3 h-24 z M10 26 v-6 a6 6 0 0 1 8 0 v6 M22 26 v-6 a6 6 0 0 1 8 0 v6" fill="none" stroke="' + GOLD + '" stroke-width="2.4"/>',
    cairn: '<g fill="' + GOLD + '"><rect x="14" y="24" width="12" height="4" rx="1"/><rect x="16" y="19" width="8" height="4" rx="1"/><rect x="18" y="14" width="4" height="4" rx="1"/></g>',
    gate: '<g stroke="' + GOLD + '" stroke-width="2.6" fill="none"><path d="M12 28 v-12 M28 28 v-12 M10 16 h20"/><path d="M16 28 v-8 M24 28 v-8" stroke-width="1.6"/></g>',
    peak: '<path d="M9 27 l7 -12 4 6 3 -9 8 15 z" fill="' + GOLD + '"/>',
    scroll: '<g stroke="' + GOLD + '" stroke-width="2.2" fill="none"><path d="M14 13 h12 M14 13 v14 h12 v-14"/><path d="M17 18 h6 M17 22 h6" stroke-width="1.5"/></g>',
    bell: '<path d="M20 12 c-5 0 -6 6 -6 10 h-2 v3 h16 v-3 h-2 c0 -4 -1 -10 -6 -10 z M18.5 27 a1.5 1.5 0 0 0 3 0" fill="' + GOLD + '"/>',
    horseshoe: '<path d="M13 28 v-8 a7 7 0 0 1 14 0 v8" fill="none" stroke="' + GOLD + '" stroke-width="3.2" stroke-linecap="round"/>',
    banners: '<g fill="' + GOLD + '"><path d="M12 12 v16 M20 12 v16 M28 12 v16" stroke="' + GOLD + '" stroke-width="1.4"/><path d="M12 12 l6 2.4 -6 2.4 z M20 12 l6 2.4 -6 2.4 z M28 12 l6 2.4 -6 2.4 z"/></g>',
  };

  function shade(hex, factor) {
    const n = parseInt(hex.slice(1), 16);
    const r = Math.min(255, Math.round(((n >> 16) & 255) * factor));
    const g = Math.min(255, Math.round(((n >> 8) & 255) * factor));
    const b = Math.min(255, Math.round((n & 255) * factor));
    return `rgb(${r},${g},${b})`;
  }

  function escAttr(value) {
    return String(value).replace(/[&<>"]/g, (ch) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[ch]));
  }

  function normalizeHexColor(value) {
    const raw = String(value || "").trim();
    if (/^#[0-9a-f]{6}$/i.test(raw)) return raw.toLowerCase();
    if (/^#[0-9a-f]{3}$/i.test(raw)) {
      return "#" + raw.slice(1).split("").map((ch) => ch + ch).join("").toLowerCase();
    }
    return null;
  }

  function hexToRgb(hex) {
    const normalized = normalizeHexColor(hex) || "#777777";
    const n = parseInt(normalized.slice(1), 16);
    return {
      r: (n >> 16) & 255,
      g: (n >> 8) & 255,
      b: n & 255,
    };
  }

  function rgbToHsl({ r, g, b }) {
    r /= 255; g /= 255; b /= 255;
    const max = Math.max(r, g, b);
    const min = Math.min(r, g, b);
    let h = 0;
    const l = (max + min) / 2;
    const d = max - min;
    const s = d === 0 ? 0 : d / (1 - Math.abs(2 * l - 1));
    if (d !== 0) {
      if (max === r) h = ((g - b) / d) % 6;
      else if (max === g) h = (b - r) / d + 2;
      else h = (r - g) / d + 4;
      h = Math.round(h * 60);
      if (h < 0) h += 360;
    }
    return { h, s, l };
  }

  function relativeLuminance(hex) {
    const { r, g, b } = hexToRgb(hex);
    const linear = [r, g, b].map((channel) => {
      const v = channel / 255;
      return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2];
  }

  function customTinctureName(hex) {
    const normalized = normalizeHexColor(hex);
    return normalized ? `wg_${normalized.slice(1)}` : null;
  }

  function chargeTinctureForField(hex) {
    const normalized = normalizeHexColor(hex);
    if (!normalized) return "or";
    const hsl = rgbToHsl(hexToRgb(normalized));
    if (hsl.h >= 30 && hsl.h <= 65 && hsl.l > 0.34) return "sable";
    return relativeLuminance(normalized) > 0.43 ? "sable" : "or";
  }

  function positionSize(positions) {
    const unique = [...new Set(String(positions || "e"))].length;
    if (positions === "e") return 1.05;
    if (unique <= 2) return 0.58;
    if (unique <= 4) return 0.42;
    if (unique <= 6) return 0.32;
    return 0.2;
  }

  function ordinaryItem(ordinary, tincture, line, above) {
    const item = { ordinary, t: tincture };
    if (line) item.line = line;
    if (above) item.above = 1;
    return item;
  }

  function medievalPalette(fieldColor) {
    return {
      fieldContrast: chargeTinctureForField(fieldColor),
      gold: "or",
      white: "argent",
      black: "sable",
      red: "gules",
      blue: "azure",
      green: "vert",
      purple: "purpure",
    };
  }

  function resolveBlazonTincture(value, palette) {
    return palette[value] || value || palette.fieldContrast;
  }

  function explicitKingdomParts(factionData, fieldColor, field) {
    const seed = heraldrySeed(factionData);
    const palette = medievalPalette(fieldColor);
    const blazon = KINGDOM_BLAZONS[factionData.id] || {
      ordinaries: [{ ordinary: "bordure", t: palette.fieldContrast === "or" ? "gold" : "black" }],
      charges: [{
        charge: ARMORIA_CHARGES[factionData.charge] || "crown",
        t: "fieldContrast",
        p: "e",
        size: 0.82,
      }],
    };
    const coa = {
      seed,
      shield: "heater",
      zoom: 0.78,
      t1: field,
      ordinaries: (blazon.ordinaries || []).map((ordinary) =>
        ordinaryItem(
          ordinary.ordinary,
          resolveBlazonTincture(ordinary.t, palette),
          ordinary.line || "straight",
          ordinary.above
        )
      ),
      charges: (blazon.charges || []).map((charge) => {
        const item = {
          charge: charge.charge,
          t: resolveBlazonTincture(charge.t, palette),
          p: charge.p || "e",
          size: charge.size || positionSize(charge.p || "e"),
        };
        if (charge.t2) item.t2 = resolveBlazonTincture(charge.t2, palette);
        if (charge.t3) item.t3 = resolveBlazonTincture(charge.t3, palette);
        if (charge.angle) item.angle = charge.angle;
        if (charge.sinister) item.sinister = charge.sinister;
        if (charge.reversed) item.reversed = charge.reversed;
        return item;
      }),
    };

    if (!coa.ordinaries.length) delete coa.ordinaries;
    if (!coa.charges.length) delete coa.charges;
    return coa;
  }

  function isKingdomHeraldry(data) {
    if (!data || !normalizeHexColor(data.color)) return false;
    const type = String(data.heraldryType || data.heraldryScope || data.kind || data.type || "").toLowerCase();
    if (NON_KINGDOM_HERALDRY_TYPES.has(type)) return false;
    if (["kingdom", "realm", "faction"].includes(type)) return true;
    return Boolean(data.tier || data.tierLabel || data.government || data.identity);
  }

  function kingdomCoa(factionData) {
    const fieldColor = normalizeHexColor(factionData.color) || "#777777";
    const field = customTinctureName(fieldColor) || "sable";
    return explicitKingdomParts(factionData, fieldColor, field);
  }

  function kingdomColorMap(factionData) {
    const fieldColor = normalizeHexColor(factionData && factionData.color);
    const field = customTinctureName(fieldColor);
    return field && fieldColor ? { [field]: fieldColor } : {};
  }

  function fallbackShieldSVG(faction, size) {
    const width = Math.max(12, Math.round(Number(size) || 30));
    const height = Math.round(width * 1.1);
    const charge = CHARGES[faction.charge] || CHARGES.peak;
    const c = normalizeHexColor(faction.color) || "#777777";
    const id = String(faction.id || heraldrySeed(faction)).replace(/[^a-z0-9_-]/gi, "_");
    const label = faction.name || faction.shortName || faction.id || "Unknown realm";
    return `
<svg viewBox="0 0 40 44" width="${width}" height="${height}" class="wg-shield wg-kingdom-shield"
     style="--wg-shield-w:${width}px; --wg-shield-h:${height}px" aria-label="${escAttr(label)} coat of arms">
  <defs>
    <linearGradient id="g_${id}" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="${shade(c, 1.25)}"/>
      <stop offset="1" stop-color="${shade(c, 0.62)}"/>
    </linearGradient>
  </defs>
  <path d="M4 4 h32 v18 c0 10 -8 16 -16 19 c-8 -3 -16 -9 -16 -19 z"
        fill="url(#g_${id})" stroke="#1c150a" stroke-width="1.6"/>
  <path d="M4 4 h32 v18 c0 10 -8 16 -16 19 c-8 -3 -16 -9 -16 -19 z"
        fill="none" stroke="${GOLD}" stroke-width="1" opacity="0.7" transform="translate(0,0.8) scale(0.96)" transform-origin="20 22"/>
  ${charge}
</svg>`;
  }

  function heraldrySeed(factionData) {
    const raw = factionData && (
      factionData.heraldry_seed ||
      factionData.heraldrySeed ||
      factionData.armoriaSeed ||
      factionData.id ||
      factionData.name
    );
    return String(raw || "war-gods-unknown-realm");
  }

  function armoriaShieldSrc(factionData, size) {
    const sizeParam = size ? `&size=${Math.max(48, Math.round(Number(size) * 4))}` : "";
    if (isKingdomHeraldry(factionData)) {
      const coa = encodeURIComponent(JSON.stringify(kingdomCoa(factionData)));
      const colors = encodeURIComponent(JSON.stringify(kingdomColorMap(factionData)));
      return `${ARMORIA_BASE_PATH}?coa=${coa}&colors=${colors}&view=1${sizeParam}`;
    }
    return `${ARMORIA_BASE_PATH}?seed=${encodeURIComponent(heraldrySeed(factionData))}&view=1${sizeParam}`;
  }

  function shieldSVG(faction, size) {
    const data = faction || {};
    const width = Math.max(12, Math.round(Number(size) || 30));
    const height = Math.round(width * 1.1);
    const label = data.name || data.shortName || data.id || "Unknown realm";
    return `<span class="wg-shield wg-armoria-shield"
      style="--wg-shield-w:${width}px; --wg-shield-h:${height}px"
      aria-label="${escAttr(label)} coat of arms"
      title="${escAttr(label)}">
      <iframe
        class="wg-armoria-badge-frame"
        src="${escAttr(armoriaShieldSrc(data, width))}"
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

  function renderFactionShield(factionData) {
    const iframe = document.getElementById("armoria-iframe");
    if (!iframe) {
      return;
    }

    const nextSrc = armoriaShieldSrc(factionData || {});
    if (iframe.getAttribute("src") !== nextSrc) iframe.src = nextSrc;
    if (factionData && factionData.name) iframe.title = `${factionData.name} coat of arms`;
  }

  window.WG = window.WG || {};
  window.WG.shieldSVG = shieldSVG;
  window.WG.fallbackShieldSVG = fallbackShieldSVG;
  window.WG.heraldrySeed = heraldrySeed;
  window.WG.kingdomCoa = kingdomCoa;
  window.WG.armoriaShieldSrc = armoriaShieldSrc;
  window.WG.renderFactionShield = renderFactionShield;
  window.WG.isKingdomHeraldry = isKingdomHeraldry;
})();

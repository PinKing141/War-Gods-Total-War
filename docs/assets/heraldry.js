/* Procedural coat-of-arms: an SVG shield per faction, field in the faction
   color with a gold charge drawn from a small hand-made vocabulary. */
(function () {
  "use strict";

  const GOLD = "#e8c96a";
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

  function shieldSVG(faction, size) {
    const charge = CHARGES[faction.charge] || CHARGES.peak;
    const c = faction.color;
    return `
<svg viewBox="0 0 40 44" width="${size}" height="${size * 1.1}" class="wg-shield" aria-label="${faction.name}">
  <defs>
    <linearGradient id="g_${faction.id}" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="${shade(c, 1.25)}"/>
      <stop offset="1" stop-color="${shade(c, 0.62)}"/>
    </linearGradient>
  </defs>
  <path d="M4 4 h32 v18 c0 10 -8 16 -16 19 c-8 -3 -16 -9 -16 -19 z"
        fill="url(#g_${faction.id})" stroke="#1c150a" stroke-width="1.6"/>
  <path d="M4 4 h32 v18 c0 10 -8 16 -16 19 c-8 -3 -16 -9 -16 -19 z"
        fill="none" stroke="${GOLD}" stroke-width="1" opacity="0.7" transform="translate(0,0.8) scale(0.96)" transform-origin="20 22"/>
  ${charge}
</svg>`;
  }

  window.WG = window.WG || {};
  window.WG.shieldSVG = shieldSVG;
})();

/* Observer UI core: the UI class shell, inspector panel management and
   click delegation. Strictly read-only — the only controls are time
   (pause / speed).

   The UI is assembled from mixin modules loaded after this file:
     fragments.js  — shared HTML fragments and derived summaries
     topbar.js     — clock and realm shield strip
     panels.js     — world / province / realm / war panels
     character.js  — the CK2-style character sheet
     trees.js      — floating family & dynasty tree windows
     chronicle.js  — event feed, wars & recap tabs, toasts
     overlay.js    — map markers, tooltip, map debug readout
   Every module must be loaded before `new WG.UI(...)` is called. */
(function () {
  "use strict";

  const esc = (s) => String(s).replace(/[&<>"]/g, (ch) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[ch]));

  window.WG = window.WG || {};
  window.WG.uiEsc = esc;

  /* copy every prototype method of a mixin class onto WG.UI */
  window.WG.uiMixin = function (cls) {
    for (const key of Object.getOwnPropertyNames(cls.prototype)) {
      if (key !== "constructor") window.WG.UI.prototype[key] = cls.prototype[key];
    }
  };

  class UI {
    constructor(sim, map) {
      this.sim = sim;
      this.map = map;
      this.el = {
        date: document.getElementById("date"),
        shieldStrip: document.getElementById("shield-strip"),
        inspector: document.getElementById("inspector"),
        events: document.getElementById("events-list"),
        tooltip: document.getElementById("tooltip"),
        toasts: document.getElementById("toasts"),
        overlay: document.getElementById("overlay"),
        chronTabs: document.getElementById("chronicle-tabs"),
        mapDebug: document.getElementById("map-debug"),
      };
      const params = new URLSearchParams(location.search);
      this.debugMapEnabled = params.get("debug") === "map" || params.has("mapDebug");
      this.debugEnabled = params.has("debug") || params.has("mapDebug");
      this.chronMode = "chronicle";
      this._tooltipProvId = null;
      this._stripByFaction = new Map();
      this._stripOrder = "";
      this._wireDelegates();
      this._wireChronicleTabs();
      sim.onEvent((ev) => this._onEvent(ev));
    }

    /* ---------- inspector panel shell ---------- */

    _openPanel(html, opts) {
      this.el.inspector.classList.toggle("wide", Boolean(opts && opts.wide));
      this.el.inspector.innerHTML =
        `<button class="close-btn" data-close-panel>✕</button>` + html;
      this.el.inspector.classList.remove("hidden");
    }

    closePanel() {
      this.el.inspector.classList.add("hidden");
      this.el.inspector.classList.remove("wide");
      if (this.map.clearSelection) this.map.clearSelection();
      else this.map.selected = null;
    }

    /* ---------- delegation ---------- */

    _wireDelegates() {
      document.addEventListener("click", (ev) => {
        const closeBtn = ev.target.closest("[data-close-panel]");
        if (closeBtn) { this.closePanel(); return; }
        const closeWin = ev.target.closest("[data-close-window]");
        if (closeWin) { const w = closeWin.closest(".ck2-window"); if (w) w.remove(); return; }
        const ftBtn = ev.target.closest("[data-open-familytree]");
        if (ftBtn) { this.openFamilyTree(ftBtn.dataset.openFamilytree); return; }
        const dtBtn = ev.target.closest("[data-open-dynastytree]");
        if (dtBtn && dtBtn.dataset.openDynastytree) { this.openDynastyTree(dtBtn.dataset.openDynastytree); return; }
        const ck2tab = ev.target.closest("[data-ck2-tab]");
        if (ck2tab) {
          const sheet = ck2tab.closest(".ck2-sheet");
          if (sheet) {
            const key = ck2tab.dataset.ck2Tab;
            sheet.querySelectorAll("[data-ck2-tab]").forEach((t) => t.classList.toggle("active", t === ck2tab));
            sheet.querySelectorAll("[data-ck2-pane]").forEach((p) => p.classList.toggle("active", p.dataset.ck2Pane === key));
          }
          return;
        }
        const realm = ev.target.closest("[data-open-realm]");
        if (realm) { this.openRealm(realm.dataset.openRealm); return; }
        const prov = ev.target.closest("[data-open-prov]");
        if (prov) { this.openProvince(prov.dataset.openProv); return; }
        const char = ev.target.closest("[data-open-char]");
        if (char) { this.openCharacter(char.dataset.openChar); return; }
        const war = ev.target.closest("[data-open-war]");
        if (war) { this.openWar(war.dataset.openWar); return; }
      });
    }
  }

  window.WG.UI = UI;
})();

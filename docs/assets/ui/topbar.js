/* Top bar: the date clock and the realm shield strip. */
(function () {
  "use strict";

  const esc = window.WG.uiEsc;

  class UITopBar {
    /* ---------- top bar ---------- */

    renderClock() {
      this.el.date.textContent = this.sim.formatDate();
    }

    renderShieldStrip() {
      const order = this.sim.seed.factions.map((f) => f.id).join("|");
      if (order !== this._stripOrder) {
        this.el.shieldStrip.innerHTML = "";
        this._stripByFaction.clear();
        for (const f of this.sim.seed.factions) {
          const el = document.createElement("div");
          el.className = "strip-shield";
          el.dataset.openRealm = f.id;
          el.title = f.name;
          el.innerHTML = `
            ${WG.shieldSVG(f, 30)}
            <span class="strip-count"></span>
            <span class="war-flame" hidden>⚔</span>
          `;
          this.el.shieldStrip.appendChild(el);
          this._stripByFaction.set(f.id, el);
        }
        this._stripOrder = order;
      }

      for (const f of this.sim.seed.factions) {
        const provs = this.sim.ownedProvinces(f.id).length;
        const atWar = this.sim.warsOf(f.id).length > 0;
        const el = this._stripByFaction.get(f.id);
        if (!el) continue;
        el.title = f.name;
        el.classList.toggle("at-war", atWar);
        el.classList.toggle("destroyed", provs === 0);
        el.querySelector(".strip-count").textContent = provs;
        el.querySelector(".war-flame").hidden = !atWar;
      }
    }
  }

  window.WG.uiMixin(UITopBar);
})();

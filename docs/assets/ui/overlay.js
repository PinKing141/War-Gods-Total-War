/* Map overlay markers, the province tooltip and the map debug readout. */
(function () {
  "use strict";

  const esc = window.WG.uiEsc;

  class UIMapOverlay {
    /* ---------- map overlay: armies, battles, sieges ---------- */

    renderOverlay() {
      const dpr = window.devicePixelRatio || 1;
      if (!this._markers) this._markers = new Map();
      const keep = new Set();
      const upsert = (key, cls, build) => {
        let el = this._markers.get(key);
        if (!el) {
          el = document.createElement("div");
          el.className = cls;
          this.el.overlay.appendChild(el);
          this._markers.set(key, el);
          build(el, true);
        } else {
          build(el, false);
        }
        keep.add(key);
        return el;
      };

      const byLoc = {};
      for (const a of this.sim.armies) (byLoc[a.loc] = byLoc[a.loc] || []).push(a);
      for (const [loc, group] of Object.entries(byLoc)) {
        const p = this.province(loc);
        if (!p) continue;
        const pt = this.map.worldToScreen(p.x, p.y);
        const x = pt.x / dpr, y = pt.y / dpr;
        const battling = new Set(group.map((a) => a.faction)).size > 1;
        group.forEach((a, i) => {
          const f = this.sim.faction(a.faction);
          upsert("army:" + a.id, "army-marker", (el, fresh) => {
            if (fresh) {
              el.innerHTML = WG.shieldSVG(f, 20) + '<span class="army-count"></span>';
              el.dataset.openChar = a.commanderId;
              el.style.pointerEvents = "auto";
            }
            el.title = `${f.name} — ${a.size.toLocaleString()} under ${(this.sim.character(a.commanderId) || {}).name || "?"}; ${a.undersupplied ? "undersupplied" : "supply"} ${Math.round(a.supply || 0)}/${Math.round(a.maxSupply || 0)}${this.debugEnabled ? `; ${a.intentReason || "holding position"}` : ""}`;
            el.querySelector(".army-count").textContent = (a.size / 1000).toFixed(1) + "k";
            el.style.left = (x + (i - (group.length - 1) / 2) * 40) + "px";
            el.style.top = (y - 34) + "px";
          });
        });
        if (battling) {
          upsert("battle:" + loc, "battle-marker", (el, fresh) => {
            if (fresh) el.textContent = "⚔";
            el.style.left = x + "px";
            el.style.top = (y - 62) + "px";
          });
        }
      }
      for (const seedProv of this.sim.seed.provinces) {
        const p = this.province(seedProv.id) || seedProv;
        const st = this.sim.provinceState[p.id];
        if (!st.siege) continue;
        const pt = this.map.worldToScreen(p.x, p.y);
        upsert("siege:" + p.id, "siege-marker", (el, fresh) => {
          if (fresh) el.innerHTML = "🏰<i></i>";
          el.title = `Siege: ${Math.round(st.siege.progress * 100)}%`;
          el.querySelector("i").style.width = Math.round(st.siege.progress * 100) + "%";
          el.style.left = (pt.x / dpr) + "px";
          el.style.top = (pt.y / dpr + 6) + "px";
        });
      }
      for (const [key, el] of [...this._markers]) {
        if (!keep.has(key)) { el.remove(); this._markers.delete(key); }
      }

      // transient effects: floating casualty numbers, captured-banner flashes
      for (const fx of this.sim.fx.splice(0)) {
        const p = this.province(fx.loc);
        if (!p) continue;
        const pt = this.map.worldToScreen(p.x, p.y);
        const el = document.createElement("div");
        if (fx.kind === "loss") {
          el.className = "float-text";
          el.textContent = `−${fx.amount.toLocaleString()}`;
        } else {
          el.className = "float-text flag";
          el.textContent = "⚑";
          el.style.color = fx.color;
        }
        el.style.left = (pt.x / dpr) + "px";
        el.style.top = (pt.y / dpr - 46) + "px";
        this.el.overlay.appendChild(el);
        setTimeout(() => el.remove(), 1600);
      }
    }

    /* ---------- tooltip ---------- */

    tooltip(prov, ev) {
      const tip = this.el.tooltip;
      if (!prov) {
        tip.classList.add("hidden");
        this._tooltipProvId = null;
        return;
      }
      const p = this.province(prov.id) || prov;
      if (this._tooltipProvId !== p.id) {
        const st = this.provinceState(p.id);
        const f = this.faction(st.controller);
        const feature = this.terrainInfo(p.terrainFeature || p.terrain);
        const biome = this.biomeInfo(this.provinceBiomeId(p));
        const river = this.riverFeature(p.id);
        const armies = this.sim.armies.filter((a) => a.loc === prov.id);
        tip.innerHTML = `
          <div class="tt-title">${esc(p.name)}</div>
          <div class="tt-row">${WG.shieldSVG(f, 15)} ${esc(f.name)}</div>
          ${st.occupier ? `<div class="tt-row bad">occupied by ${esc(this.sim.faction(st.occupier).name)}</div>` : ""}
          ${st.siege ? `<div class="tt-row bad">under siege — ${Math.round(st.siege.progress * 100)}%</div>` : ""}
          <div class="tt-row fine">${esc(biome.label)} · ${esc(feature.label)} · pop ${st.pop.toLocaleString()} · fort ${p.fort}</div>
          ${river && river.hasRiver ? `<div class="tt-row fine">River: ${esc(this.riverSummary(river))}</div>` : ""}
          ${river && river.hasCrossing ? `<div class="tt-row fine">Crossing: ${esc(river.riverCrossingType.replace(/;/g, ", "))}</div>` : ""}
          ${armies.map((a) => `<div class="tt-row fine">⚑ ${esc(this.sim.faction(a.faction).name)}: ${a.size.toLocaleString()} · ${a.undersupplied ? "undersupplied" : "supply"} ${Math.round(a.supply || 0)}/${Math.round(a.maxSupply || 0)}</div>`).join("")}
        `;
        this._tooltipProvId = p.id;
      }
      tip.classList.remove("hidden");
      const pad = 14;
      const w = tip.offsetWidth, h = tip.offsetHeight;
      let x = ev.clientX + pad, y = ev.clientY + pad;
      if (x + w > window.innerWidth - 8) x = ev.clientX - w - pad;
      if (y + h > window.innerHeight - 8) y = ev.clientY - h - pad;
      tip.style.left = x + "px"; tip.style.top = y + "px";
    }

    mapDebug(world) {
      const el = this.el.mapDebug;
      if (!this.debugMapEnabled || !el || !world || !this.map.provinceDebugAt) {
        if (el) el.classList.add("hidden");
        return;
      }
      const info = this.map.provinceDebugAt(world.x, world.y);
      if (!info) { el.classList.add("hidden"); return; }
      const center = info.center_x === null
        ? "—"
        : `${info.center_x.toFixed(2)}, ${info.center_y.toFixed(2)}`;
      el.innerHTML = `
        <div class="debug-title">${esc(info.province_id)}</div>
        <div class="debug-row"><span>RGB</span><b>${info.rgb.join(",")}</b></div>
        <div class="debug-row"><span>center</span><b>${center}</b></div>
        <div class="debug-row"><span>biome</span><b>${esc(info.biome || "none")}</b></div>
        <div class="debug-row"><span>feature</span><b>${esc(info.terrain_feature || info.terrain)}</b></div>
        <div class="debug-row"><span>legacy terrain</span><b>${esc(info.terrain)}</b></div>
        <div class="debug-row"><span>region</span><b>${esc(info.region)}</b></div>
        <div class="debug-row"><span>controller</span><b>${esc(info.controller)}</b></div>
        <div class="debug-row"><span>river</span><b>${esc(info.river || "none")}</b></div>
      `;
      el.classList.remove("hidden");
    }
  }

  window.WG.uiMixin(UIMapOverlay);
})();

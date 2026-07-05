/* Observer UI: shield strip, inspector panels, chronicle, tooltips, toasts.
   Strictly read-only — the only controls are time (pause / speed). */
(function () {
  "use strict";

  const esc = (s) => String(s).replace(/[&<>"]/g, (ch) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[ch]));

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
      };
      this.chronMode = "chronicle";
      this._wireDelegates();
      this._wireChronicleTabs();
      sim.onEvent((ev) => this._onEvent(ev));
    }

    /* ---------- shared fragments ---------- */

    shieldChip(fid, size) {
      const f = this.sim.faction(fid);
      if (!f) return "";
      return `<span class="chip" data-open-realm="${f.id}">${WG.shieldSVG(f, size || 18)}<span>${esc(f.name)}</span></span>`;
    }

    charLink(cid) {
      const c = this.sim.character(cid);
      if (!c) return "<i>unknown</i>";
      return `<a data-open-char="${c.id}">${esc(c.name)}${c.alive ? "" : " †"}</a>`;
    }

    provLink(pid) {
      const p = this.sim.province(pid);
      return p ? `<a data-open-prov="${p.id}">${esc(p.name)}</a>` : "<i>—</i>";
    }

    warLink(warId) {
      const w = this.sim.wars.find((x) => x.id === warId);
      return w ? `<a data-open-war="${w.id}">${esc(w.name)}</a>` : "";
    }

    pips(n, max, chr) {
      let out = "";
      for (let i = 0; i < max; i++) out += `<i class="pip ${i < n ? "on" : ""}">${chr || "◆"}</i>`;
      return `<span class="pips">${out}</span>`;
    }

    /* ---------- top bar ---------- */

    renderClock() {
      this.el.date.textContent = this.sim.formatDate();
    }

    renderShieldStrip() {
      const rows = this.sim.seed.factions.map((f) => {
        const s = this.sim.factionState[f.id];
        const provs = this.sim.ownedProvinces(f.id).length;
        const atWar = this.sim.warsOf(f.id).length > 0;
        return `<div class="strip-shield ${atWar ? "at-war" : ""} ${provs === 0 ? "destroyed" : ""}"
                     data-open-realm="${f.id}" title="${esc(f.name)}">
          ${WG.shieldSVG(f, 30)}
          <span class="strip-count">${provs}</span>
          ${atWar ? '<span class="war-flame">⚔</span>' : ""}
        </div>`;
      });
      this.el.shieldStrip.innerHTML = rows.join("");
    }

    /* ---------- inspector panels ---------- */

    _openPanel(html) {
      this.el.inspector.innerHTML =
        `<button class="close-btn" data-close-panel>✕</button>` + html;
      this.el.inspector.classList.remove("hidden");
    }

    closePanel() {
      this.el.inspector.classList.add("hidden");
      this.map.selected = null;
    }

    openWorld() {
      const s = this.sim;
      const ranked = [...s.seed.factions].sort((a, b) =>
        s.factionState[b.id].prestige - s.factionState[a.id].prestige);
      const strongest = ranked[0];
      const rulers = s.characters.filter((c) => c.isRuler);
      const eldest = s.characters.filter((c) => c.alive)
        .reduce((a, b) => (a.age > b.age ? a : b));
      this._openPanel(`
        <div class="panel-head">
          <h2>The World</h2>
          <div class="subtitle">${esc(s.seed.world.region)} · ${esc(s.formatDate())}</div>
        </div>
        <div class="stat-rows">
          <div class="row"><span>Wars fought / ended</span><b>${s.wars.length} / ${s.totals.warsEnded}</b></div>
          <div class="row"><span>Soldiers fallen</span><b>${s.totals.fallen.toLocaleString()}</b></div>
          <div class="row"><span>Rulers crowned</span><b>${rulers.length}</b></div>
          <div class="row"><span>Eldest living soul</span><b>${this.charLink(eldest.id)} <span class="fine">(${eldest.age})</span></b></div>
          <div class="row"><span>Mightiest banner</span><b>${this.shieldChip(strongest.id)}</b></div>
        </div>
        <h3>The powers, by prestige</h3>
        ${ranked.map((f, i) => {
          const st = s.factionState[f.id];
          const provs = s.ownedProvinces(f.id).length;
          const ruler = s.rulerOf(f.id);
          return `<div class="rank-row" data-open-realm="${f.id}">
            <span class="rank-num">${i + 1}</span>
            ${WG.shieldSVG(f, 22)}
            <div class="rank-body">
              <div>${esc(f.name)}${provs === 0 ? ' <span class="bad fine">landless</span>' : ""}</div>
              <div class="fine">${ruler ? esc(ruler.name) : "—"} · ${provs} land${provs === 1 ? "" : "s"} · ${s.armyStrength(f.id).toLocaleString()} levied</div>
            </div>
            <b>${Math.round(st.prestige)}</b>
          </div>`;
        }).join("")}
      `);
    }

    openProvince(pid) {
      const p = this.sim.province(pid);
      if (!p) return;
      this.map.selected = pid;
      const st = this.sim.provinceState[pid];
      const terr = this.sim.seed.terrains[p.terrain] || { label: p.terrain };
      const claims = this.sim.claims.filter((c) => c.target === pid && c.strength > 10);
      const armies = this.sim.armies.filter((a) => a.loc === pid);
      const names = [
        [`Locally`, p.localName], [`In the old imperial rolls`, p.imperialName],
        [`To the faithful`, p.religiousName], [`To its enemies`, p.enemyName],
      ].filter(([, v]) => v && v !== p.name)
        .map(([k, v]) => `<div class="alias"><span>${k}:</span> ${esc(v)}</div>`).join("");

      this._openPanel(`
        <div class="panel-head">
          <h2>${esc(p.name)}</h2>
          <div class="subtitle">${esc(terr.label)} · ${esc(p.resource.replace(/_/g, " ").toLowerCase())}</div>
        </div>
        ${names}
        <div class="stat-rows">
          <div class="row"><span>Held by</span><b>${this.shieldChip(st.controller)}</b></div>
          ${st.occupier ? `<div class="row occupied"><span>Occupied by</span><b>${this.shieldChip(st.occupier)}</b></div>` : ""}
          ${st.siege ? `<div class="row occupied"><span>Under siege</span><b>${this.shieldChip(st.siege.by)} — ${Math.round(st.siege.progress * 100)}%</b></div>` : ""}
          <div class="row"><span>Population</span><b>${st.pop.toLocaleString()}</b></div>
          <div class="row"><span>Fortifications</span><b>${this.pips(p.fort, 5, "▲")}</b></div>
          <div class="row"><span>Roads</span><b>${this.pips(p.roads, 5)}</b></div>
          ${p.port ? `<div class="row"><span>Harbour</span><b>${this.pips(p.port, 5)}</b></div>` : ""}
          ${p.manaSite ? `<div class="row"><span>Mana site</span><b>${this.pips(p.manaSite, 3, "✦")}</b></div>` : ""}
          ${st.devastation > 4 ? `<div class="row"><span>Devastation</span><b class="bad">${Math.round(st.devastation)}%</b></div>` : ""}
          <div class="row"><span>Strategic value</span><b>${p.value}</b></div>
        </div>
        ${armies.length ? `<h3>Armies present</h3>` + armies.map((a) =>
          `<div class="row">${this.shieldChip(a.faction)}<b>${a.size.toLocaleString()} under ${this.charLink(a.commanderId)}</b></div>`).join("") : ""}
        ${claims.length ? `<h3>Claims on this land</h3>` + claims.map((c) =>
          `<div class="claim"><b>${this.shieldChip(c.claimant)}</b> — ${esc(c.type)} (${Math.round(c.strength)}) <div class="fine">${esc(c.source)} · ${esc(c.myth)}</div></div>`).join("") : ""}
      `);
    }

    openRealm(fid) {
      const f = this.sim.faction(fid);
      if (!f) return;
      const s = this.sim.factionState[fid];
      const culture = this.sim.seed.cultures[f.culture] || {};
      const religion = this.sim.seed.religions[f.religion] || {};
      const ruler = this.sim.rulerOf(fid);
      const provinces = this.sim.ownedProvinces(fid);
      const wars = this.sim.warsOf(fid);
      const captains = this.sim.characters.filter((c) =>
        c.faction === fid && c.alive && c.id !== (ruler && ruler.id));
      const rels = this.sim.seed.relations
        .filter((r) => r.a === fid || r.b === fid)
        .map((r) => {
          const other = r.a === fid ? r.b : r.a;
          const op = Math.round(this.sim.opinion(r.a, r.b));
          const cls = op < -25 ? "bad" : op > 25 ? "good" : "";
          return `<div class="row">${this.shieldChip(other)}<b class="${cls}">${op > 0 ? "+" : ""}${op}</b><div class="fine">${esc(r.tension)}</div></div>`;
        }).join("");
      const income = this.sim.monthlyIncome(fid), upkeep = this.sim.monthlyUpkeep(fid);

      this._openPanel(`
        <div class="panel-head realm-head">
          ${WG.shieldSVG(f, 52)}
          <div>
            <h2>${esc(f.name)}</h2>
            <div class="subtitle">${esc(f.identity)} · ${esc(f.government.replace(/_/g, " "))}</div>
          </div>
        </div>
        ${ruler ? `<div class="ruler-card" data-open-char="${ruler.id}">
            <div class="ruler-name">${esc(ruler.name)}</div>
            <div class="fine">${esc(ruler.role)} · ${ruler.age} years · ${ruler.traits.map((t) => t.label).join(", ")}</div>
          </div>` : `<div class="ruler-card"><i>The seat stands empty.</i></div>`}
        ${(() => {
          const heir = this.sim.heirOf(fid);
          return heir
            ? `<div class="row"><span>Heir</span><b>${this.charLink(heir.id)} <span class="fine">(${heir.age})</span></b></div>`
            : `<div class="row"><span>Heir</span><b class="fine"><i>the line hangs by a thread</i></b></div>`;
        })()}
        <div class="stat-rows">
          <div class="row"><span>Treasury</span><b>${s.treasury.toLocaleString()} silver</b></div>
          <div class="row"><span>Monthly ledger</span><b class="${income - upkeep >= 0 ? "good" : "bad"}">${income - upkeep >= 0 ? "+" : ""}${(income - upkeep).toLocaleString()}</b></div>
          <div class="row"><span>Levies afield</span><b>${this.sim.armyStrength(fid).toLocaleString()}</b></div>
          <div class="row"><span>Manpower</span><b>${s.manpower.toLocaleString()} / ${s.maxManpower.toLocaleString()}</b></div>
          <div class="row"><span>Prestige</span><b>${Math.round(s.prestige)}</b></div>
          ${s.exhaustion > 5 ? `<div class="row"><span>War exhaustion</span><b class="bad">${Math.round(s.exhaustion)}</b></div>` : ""}
          <div class="row"><span>Wars won / lost</span><b>${s.warsWon} / ${s.warsLost}</b></div>
        </div>
        <h3>Faith — ${esc(religion.name || f.religion)}</h3>
        <div class="quote">“${esc(religion.claim || "")}”</div>
        <h3>Culture — ${esc(culture.name || f.culture)} (${esc(culture.selfName || "")})</h3>
        <div class="fine">${esc(culture.values || "")}</div>
        <div class="quote">${esc(culture.contradiction || "")}</div>
        <h3>Lands (${provinces.length})</h3>
        ${provinces.map((p) => {
          const st = this.sim.provinceState[p.id];
          return `<div class="row"><span>${this.provLink(p.id)}</span><b>${st.occupier ? `<i class="bad">occupied</i>` : "held"}</b></div>`;
        }).join("") || "<div class='fine'>Nothing remains.</div>"}
        ${wars.length ? "<h3>Wars</h3>" + wars.map((w) =>
          `<div class="row"><span>${this.warLink(w.id)}</span><b>${w.attacker === fid ? "attacker" : "defender"}</b></div>`).join("") : ""}
        ${captains.length ? "<h3>Notable figures</h3>" + captains.slice(0, 6).map((c) =>
          `<div class="row"><span>${this.charLink(c.id)}</span><b class="fine">${esc(c.role)}</b></div>`).join("") : ""}
        <h3>Standing among neighbours</h3>
        ${rels || "<div class='fine'>No recorded dealings.</div>"}
      `);
    }

    openCharacter(cid) {
      const c = this.sim.character(cid);
      if (!c) return;
      const f = this.sim.faction(c.faction);
      const species = this.sim.seed.species[c.species] || { name: c.species };
      const culture = this.sim.seed.cultures[c.culture] || { name: c.culture };
      const mage = this.sim.mages.find((m) => m.character === cid);
      const armies = this.sim.armies.filter((a) => a.commanderId === cid);

      this._openPanel(`
        <div class="panel-head">
          <h2>${esc(c.name)}${c.alive ? "" : " †"}</h2>
          <div class="subtitle">${esc(c.role)} of ${f ? esc(f.name) : "?"}</div>
        </div>
        <div class="stat-rows">
          <div class="row"><span>Sworn to</span><b>${this.shieldChip(c.faction)}</b></div>
          <div class="row"><span>People</span><b>${esc(species.name)} · ${esc(culture.name || "")}</b></div>
          <div class="row"><span>Age</span><b>${c.age}</b></div>
          <div class="row"><span>Temperament</span><b>${c.traits.map((t) => `<span class="trait">${t.label}</span>`).join(" ")}</b></div>
          <div class="row"><span>Prestige</span><b>${Math.round(c.prestige)}</b></div>
          ${c.kills ? `<div class="row"><span>Soldiers slain under their command</span><b>${c.kills.toLocaleString()}</b></div>` : ""}
          ${c.isRuler && c.reignStart ? `<div class="row"><span>Reigning since</span><b>${c.reignStart} AE</b></div>` : ""}
        </div>
        <div class="quote">Their burden: ${esc(c.pressure)}.</div>
        ${(() => {
          const parent = c.parentId ? this.sim.character(c.parentId) : null;
          const kids = this.sim.childrenOf(c.id);
          if (!parent && !kids.length) return "";
          return "<h3>Lineage</h3>" +
            (parent ? `<div class="row"><span>Born to</span><b>${this.charLink(parent.id)}</b></div>` : "") +
            kids.map((k) => `<div class="row"><span>${k.alive ? "Child" : "Child †"}</span><b>${this.charLink(k.id)} <span class="fine">(${k.age})</span></b></div>`).join("");
        })()}
        ${mage ? `<h3>The Gift</h3>
          <div class="stat-rows">
            <div class="row"><span>Specialization</span><b>${esc(mage.specialization)}</b></div>
            <div class="row"><span>Capacity / Control</span><b>${mage.capacity} / ${mage.control}</b></div>
            <div class="row"><span>Standing in law</span><b>${esc(mage.legal)}</b></div>
            <div class="row"><span>Risk</span><b class="${mage.risk > 50 ? "bad" : ""}">${mage.risk}</b></div>
            ${mage.alive ? "" : `<div class="row"><span></span><b class="bad">The gift has consumed them.</b></div>`}
          </div>` : ""}
        ${armies.length ? "<h3>Commands</h3>" + armies.map((a) =>
          `<div class="row"><span>${a.size.toLocaleString()} at ${this.provLink(a.loc)}</span></div>`).join("") : ""}
      `);
    }

    openWar(warId) {
      const w = this.sim.wars.find((x) => x.id === warId);
      if (!w) return;
      const scorePct = Math.round((w.score + 100) / 2);
      this._openPanel(`
        <div class="panel-head">
          <h2>${esc(w.name)}</h2>
          <div class="subtitle">${w.over ? `concluded ${esc(w.endDate)}` : `raging since ${esc(w.startDate)}`}</div>
        </div>
        <div class="war-sides">
          <div>${w.atkSide.map((fid) => this.shieldChip(fid, 24)).join("<br>")}</div>
          <div class="vs">against</div>
          <div>${w.defSide.map((fid) => this.shieldChip(fid, 24)).join("<br>")}</div>
        </div>
        <div class="stat-rows">
          <div class="row"><span>The prize</span><b>${w.goal.type === "raid" ? "plunder and tribute" : this.provLink(w.goal.province)}</b></div>
        </div>
        ${w.over ? "" : `
          <h3>Fortunes of war</h3>
          <div class="score-bar"><div class="score-fill" style="width:${scorePct}%"></div></div>
          <div class="fine center">${w.score > 10 ? "the attacker has the upper hand" : w.score < -10 ? "the defender holds firm" : "the scales hang level"} (${Math.round(w.score)})</div>`}
        ${w.battles.length ? "<h3>Battles</h3>" + w.battles.slice(-8).reverse().map((b) =>
          `<div class="claim"><b>${esc(b.name)}</b> — won by ${this.shieldChip(b.winner)}
           <div class="fine">${esc(b.date)} · ${b.loserLosses.toLocaleString()} fell on the losing side, ${b.winnerLosses.toLocaleString()} on the winning</div></div>`).join("")
        : "<div class='fine'>No pitched battle has yet been fought.</div>"}
      `);
    }

    /* ---------- chronicle & toasts ---------- */

    _iconFor(type) {
      return { war: "⚔", battle: "⚔", siege: "🏰", peace: "🕊", succession: "👑",
               death: "✝", magic: "✦", muster: "🛡", birth: "✼" }[type] || "•";
    }

    _onEvent(ev) {
      if (this.chronMode === "chronicle" && ev.importance >= 2) this._appendEvent(ev);
      if (ev.importance >= 3) this._toast(ev);
    }

    _appendEvent(ev) {
      const div = document.createElement("div");
      div.className = `event imp${ev.importance} type-${ev.type}`;
      div.innerHTML = `<span class="ev-icon">${this._iconFor(ev.type)}</span>
        <div><div class="ev-date">${esc(ev.date)}</div><div class="ev-text">${esc(ev.text)}</div></div>`;
      div.addEventListener("click", () => this._focusEvent(ev));
      this.el.events.prepend(div);
      while (this.el.events.children.length > 140) this.el.events.lastChild.remove();
    }

    _focusEvent(ev) {
      if (ev.refs.province) {
        const p = this.sim.province(ev.refs.province);
        if (p) { this.map.view.x = p.x; this.map.view.y = p.y; }
      }
      if (ev.refs.war) this.openWar(ev.refs.war);
      else if (ev.refs.character && this.sim.character(ev.refs.character)) this.openCharacter(ev.refs.character);
      else if (ev.refs.province) this.openProvince(ev.refs.province);
      else if (ev.refs.faction) this.openRealm(ev.refs.faction);
    }

    _toast(ev) {
      const div = document.createElement("div");
      div.className = `toast type-${ev.type}`;
      div.innerHTML = `<span class="ev-icon">${this._iconFor(ev.type)}</span><div>${esc(ev.text)}</div>`;
      div.addEventListener("click", () => { this._focusEvent(ev); div.remove(); });
      this.el.toasts.appendChild(div);
      setTimeout(() => { div.classList.add("fade"); setTimeout(() => div.remove(), 900); }, 6500);
      while (this.el.toasts.children.length > 4) this.el.toasts.firstChild.remove();
    }

    renderWarsTab() {
      const wars = [...this.sim.wars].reverse();
      this.el.events.innerHTML = wars.length ? "" : "<div class='fine center pad'>The frontier is quiet. For now.</div>";
      for (const w of wars.slice(0, 40)) {
        const div = document.createElement("div");
        div.className = `event ${w.over ? "war-over" : "war-live"}`;
        div.innerHTML = `<span class="ev-icon">${w.over ? "🕊" : "⚔"}</span>
          <div><div class="ev-date">${esc(w.startDate)}${w.over ? " — " + esc(w.endDate) : ""}</div>
          <div class="ev-text">${esc(w.name)} · ${esc(this.sim.faction(w.attacker).name)} vs ${esc(this.sim.faction(w.defender).name)}</div></div>`;
        div.addEventListener("click", () => this.openWar(w.id));
        this.el.events.appendChild(div);
      }
    }

    _wireChronicleTabs() {
      this.el.chronTabs.addEventListener("click", (ev) => {
        const tab = ev.target.closest("[data-tab]");
        if (!tab) return;
        this.chronMode = tab.dataset.tab;
        for (const t of this.el.chronTabs.querySelectorAll("[data-tab]")) {
          t.classList.toggle("active", t === tab);
        }
        if (this.chronMode === "wars") this.renderWarsTab();
        else {
          this.el.events.innerHTML = "";
          for (const e of this.sim.events.filter((e) => e.importance >= 2).slice(-140)) this._appendEvent(e);
        }
      });
    }

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
        const p = this.sim.province(loc);
        if (!p) continue;
        const pt = this.map.worldToScreen(p.x, p.y);
        const x = pt.x / dpr, y = pt.y / dpr;
        const battling = new Set(group.map((a) => a.faction)).size > 1;
        group.forEach((a, i) => {
          const f = this.sim.faction(a.faction);
          upsert("army:" + a.id, "army-marker", (el, fresh) => {
            if (fresh) {
              el.innerHTML = WG.shieldSVG(f, 20) + "<span></span>";
              el.dataset.openChar = a.commanderId;
              el.style.pointerEvents = "auto";
            }
            el.title = `${f.name} — ${a.size.toLocaleString()} under ${(this.sim.character(a.commanderId) || {}).name || "?"}`;
            el.querySelector("span").textContent = (a.size / 1000).toFixed(1) + "k";
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
      for (const p of this.sim.seed.provinces) {
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
        const p = this.sim.province(fx.loc);
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
      if (!prov) { tip.classList.add("hidden"); return; }
      const st = this.sim.provinceState[prov.id];
      const f = this.sim.faction(st.controller);
      const terr = this.sim.seed.terrains[prov.terrain] || { label: prov.terrain };
      const armies = this.sim.armies.filter((a) => a.loc === prov.id);
      tip.innerHTML = `
        <div class="tt-title">${esc(prov.name)}</div>
        <div class="tt-row">${WG.shieldSVG(f, 15)} ${esc(f.name)}</div>
        ${st.occupier ? `<div class="tt-row bad">occupied by ${esc(this.sim.faction(st.occupier).name)}</div>` : ""}
        ${st.siege ? `<div class="tt-row bad">under siege — ${Math.round(st.siege.progress * 100)}%</div>` : ""}
        <div class="tt-row fine">${esc(terr.label)} · pop ${st.pop.toLocaleString()} · fort ${prov.fort}</div>
        ${armies.map((a) => `<div class="tt-row fine">⚑ ${esc(this.sim.faction(a.faction).name)}: ${a.size.toLocaleString()}</div>`).join("")}
      `;
      tip.classList.remove("hidden");
      const pad = 14;
      const w = tip.offsetWidth, h = tip.offsetHeight;
      let x = ev.clientX + pad, y = ev.clientY + pad;
      if (x + w > window.innerWidth - 8) x = ev.clientX - w - pad;
      if (y + h > window.innerHeight - 8) y = ev.clientY - h - pad;
      tip.style.left = x + "px"; tip.style.top = y + "px";
    }

    /* ---------- delegation ---------- */

    _wireDelegates() {
      document.addEventListener("click", (ev) => {
        const closeBtn = ev.target.closest("[data-close-panel]");
        if (closeBtn) { this.closePanel(); return; }
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

  window.WG = window.WG || {};
  window.WG.UI = UI;
})();

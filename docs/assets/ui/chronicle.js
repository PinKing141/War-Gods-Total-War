/* Chronicle feed, wars and recap tabs, and toast notices. */
(function () {
  "use strict";

  const esc = window.WG.uiEsc;

  class UIChronicle {
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
        const p = this.province(ev.refs.province);
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

    renderRecapTab() {
      const recaps = [...(this.sim.monthlyRecaps || [])].reverse();
      this.el.events.innerHTML = "";
      if (this.debugEnabled && typeof this.sim.validateState === "function") {
        const health = this.sim.validateState();
        const issues = health.issues || [];
        const errors = issues.filter((issue) => issue.severity === "error");
        const warnings = issues.filter((issue) => issue.severity !== "error");
        const div = document.createElement("div");
        div.className = "event recap-card";
        const shownIssues = issues.slice(0, 5).map((issue) =>
          `<div class="fine ${issue.severity === "error" ? "bad" : ""}">${esc(issue.severity || "issue")}: ${esc(issue.code)} at ${esc(issue.location)} — ${esc(issue.message)}</div>`
        ).join("");
        div.innerHTML = `<span class="ev-icon">${errors.length ? "!" : "OK"}</span>
          <div>
            <div class="ev-date">Simulation health · ${esc(health.checkedAt || this.sim.formatDate())}</div>
            <div class="ev-text">${errors.length ? `${errors.length} validation error(s)` : warnings.length ? `${warnings.length} warning(s)` : "No validation issues detected."}</div>
            <div class="fine">factions ${health.counts.factions} · provinces ${health.counts.provinces} · characters ${health.counts.characters} · armies ${health.counts.armies} · active wars ${health.counts.activeWars}</div>
            ${shownIssues || "<div class='fine good'>Runtime IDs, controllers, armies, wars, claims, mages and non-negative fields all check out.</div>"}
          </div>`;
        this.el.events.appendChild(div);
      }
      if (!recaps.length) {
        const empty = document.createElement("div");
        empty.className = "fine center pad";
        empty.textContent = "No month has closed yet.";
        this.el.events.appendChild(empty);
        return;
      }
      for (const recap of recaps.slice(0, 36)) {
        const div = document.createElement("div");
        div.className = "event recap-card";
        const types = Object.entries(recap.typeCounts || {})
          .sort((a, b) => b[1] - a[1])
          .map(([type, count]) => `${type} ${count}`)
          .join(" · ") || "quiet month";
        const trouble = (recap.troubledFactions || [])
          .map((r) => `${esc(this.faction(r.faction).shortName || this.faction(r.faction).name)}: ${esc(r.risks.join(", "))}`)
          .join("<br>");
        const headlines = (recap.headlines || []).map((h) => `<div class="fine">- ${esc(h)}</div>`).join("");
        div.innerHTML = `<span class="ev-icon">☾</span>
          <div>
            <div class="ev-date">${esc(recap.date)}</div>
            <div class="ev-text">Wars ${recap.activeWars.length} · sieges ${recap.activeSieges.length} · fallen ${recap.fallen.toLocaleString()} · wars ended ${recap.warsEnded}</div>
            <div class="fine">${esc(types)}</div>
            ${trouble ? `<div class="fine bad">${trouble}</div>` : `<div class="fine good">No major realm crisis flagged.</div>`}
            ${headlines}
          </div>`;
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
        else if (this.chronMode === "recap") this.renderRecapTab();
        else {
          this.el.events.innerHTML = "";
          for (const e of this.sim.events.filter((e) => e.importance >= 2).slice(-140)) this._appendEvent(e);
        }
      });
    }
  }

  window.WG.uiMixin(UIChronicle);
})();

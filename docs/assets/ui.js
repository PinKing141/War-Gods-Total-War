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
        mapDebug: document.getElementById("map-debug"),
      };
      const params = new URLSearchParams(location.search);
      this.debugMapEnabled = params.get("debug") === "map" || params.has("mapDebug");
      this.chronMode = "chronicle";
      this._wireDelegates();
      this._wireChronicleTabs();
      sim.onEvent((ev) => this._onEvent(ev));
    }

    /* ---------- shared fragments ---------- */

    province(pid) {
      return (this.map && this.map.province && this.map.province(pid)) ||
        this.sim.province(pid);
    }

    provinceState(pid) {
      const p = this.province(pid);
      if (this.map && this.map.provinceState) return this.map.provinceState(p || pid, this.sim);
      return this.sim.provinceState[pid];
    }

    faction(fid) {
      return this.sim.faction(fid) ||
        (this.map && this.map.faction && this.map.faction(fid)) ||
        { id: fid, name: fid || "Unknown", shortName: fid || "Unknown", color: "#888070", charge: "peak" };
    }

    terrainInfo(id) {
      return (this.map && this.map.terrainInfo && this.map.terrainInfo(id)) ||
        this.sim.seed.terrains[id] ||
        { label: String(id || "unknown").replace(/_/g, " ").replace(/\b\w/g, (m) => m.toUpperCase()) };
    }

    biomeInfo(id) {
      return (this.map && this.map.biomeInfo && this.map.biomeInfo(id)) ||
        (window.WG && WG.WORLD_BIOME_INFO && WG.WORLD_BIOME_INFO[id]) ||
        { label: String(id || "unknown").replace(/_/g, " ").replace(/\b\w/g, (m) => m.toUpperCase()) };
    }

    provinceBiomeId(p) {
      if (!p) return "unknown";
      if (p.biome) return p.biome;
      const feature = p.terrainFeature || p.terrain;
      return {
        river_city: "farmland",
        canal_farmland: "farmland",
        bog_forest: "marsh",
        frontier_farms: "farmland",
        mountain_pass: "mountain",
        charter_city: "farmland",
        river_port: "coast",
        steppe_market: "steppe",
        sacred_battlefield: "farmland",
        mine_hills: "mountain",
        iron_hills: "mountain",
        oasis_salt_road: "oasis",
        dryland_plateau: "dryland",
        grain_estate: "farmland",
      }[feature] || "dryland";
    }

    riverFeature(pid) {
      return (this.map && this.map.riverFeatures && this.map.riverFeatures(pid)) || null;
    }

    riverSummary(feature) {
      if (!feature || !feature.hasRiver) return "";
      const name = feature.primaryRiverName || feature.primaryRiverId || "Unnamed river";
      const count = feature.riverIds.length > 1 ? ` + ${feature.riverIds.length - 1} more` : "";
      const width = feature.maxWidthClass ? `class ${feature.maxWidthClass}` : "unclassed";
      return `${name}${count} (${width})`;
    }

    riverRows(feature) {
      if (!feature || !feature.hasRiver) return "";
      const types = feature.riverTypes.length
        ? feature.riverTypes.map((t) => t.replace(/_/g, " ")).join(", ")
        : "river";
      const crossing = feature.hasCrossing
        ? feature.riverCrossingType.replace(/;/g, ", ").replace(/_/g, " ")
        : "none";
      const navigation = feature.navigableRiver ? "navigable" : "not navigable";
      const effects = [
        feature.riverTradeValue ? `trade +${feature.riverTradeValue}` : "",
        feature.supplyBonus ? `supply +${feature.supplyBonus}` : "",
        feature.farmlandBonus ? `farmland +${feature.farmlandBonus}` : "",
        feature.riverDefenseBonus ? `defense +${feature.riverDefenseBonus}` : "",
        feature.riverMovementPenalty ? `movement penalty +${feature.riverMovementPenalty}` : "",
      ].filter(Boolean).join(" · ");
      return `
        <div class="row"><span>River</span><b>${esc(this.riverSummary(feature))}</b></div>
        <div class="row"><span>Type</span><b>${esc(types)}</b></div>
        <div class="row"><span>Crossing</span><b>${esc(crossing)}</b></div>
        <div class="row"><span>Navigation</span><b>${esc(navigation)}</b></div>
        ${feature.hasFloodplain ? `<div class="row"><span>Floodplain</span><b>yes</b></div>` : ""}
        ${effects ? `<div class="row"><span>Effects</span><b>${esc(effects)}</b></div>` : ""}
      `;
    }

    shieldChip(fid, size) {
      const f = this.faction(fid);
      if (!f) return "";
      return `<span class="chip" data-open-realm="${f.id}">${WG.shieldSVG(f, size || 18)}<span>${esc(f.name)}</span></span>`;
    }

    charLink(cid) {
      const c = this.sim.character(cid);
      if (!c) return "<i>unknown</i>";
      return `<a data-open-char="${c.id}">${esc(c.name)}${c.alive ? "" : " †"}</a>`;
    }

    provLink(pid) {
      const p = this.province(pid);
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

    provinceWarStatus(p, st) {
      const controllerWars = this.sim.warsOf(st.controller || p.controller);
      const armies = this.sim.armies.filter((a) => a.loc === p.id);
      if (st.siege) {
        return `under siege by ${this.faction(st.siege.by).shortName || this.faction(st.siege.by).name} (${Math.round(st.siege.progress * 100)}%)`;
      }
      if (st.occupier) {
        return `occupied by ${this.faction(st.occupier).shortName || this.faction(st.occupier).name}`;
      }
      if (armies.length) {
        const sides = [...new Set(armies.map((a) => a.faction))].map((fid) => this.faction(fid).shortName || this.faction(fid).name);
        return `armies present: ${sides.join(", ")}`;
      }
      if (controllerWars.length) return `realm at war (${controllerWars.length})`;
      return "peaceful";
    }

    provinceImportance(p, st, river, armies, claims) {
      const reasons = [];
      if (p.value >= 90) reasons.push("high strategic value");
      else if (p.value >= 75) reasons.push("valuable frontier holding");
      if (p.fort >= 4) reasons.push("major fortress");
      else if (p.fort >= 3) reasons.push("strong fort");
      if (p.roads >= 4) reasons.push("road hub");
      if (p.port) reasons.push("port access");
      if (p.manaSite) reasons.push("mana site");
      if (river && river.hasRiver) {
        if (river.hasCrossing) reasons.push("river crossing");
        if (river.hasFloodplain) reasons.push("floodplain");
        if (river.navigableRiver) reasons.push("river trade");
      }
      if (st.siege) reasons.push("active siege");
      if (st.occupier) reasons.push("occupied territory");
      if (armies.length) reasons.push("armies present");
      if (claims.length) reasons.push(`${claims.length} active claim${claims.length === 1 ? "" : "s"}`);
      if (!reasons.length && p.resource) reasons.push(`${String(p.resource).replace(/_/g, " ").toLowerCase()} resource`);
      return reasons.join(" · ");
    }

    factionEconomy(fid) {
      const st = this.sim.factionState[fid];
      if (!st) return null;
      const income = this.sim.monthlyIncome(fid);
      const upkeep = this.sim.monthlyUpkeep(fid);
      const court = Math.max(0, Math.round(st.treasury * 0.02));
      return { income, upkeep, court, net: income - upkeep - court };
    }

    factionRisks(fid) {
      const st = this.sim.factionState[fid];
      if (!st) return [];
      const risks = [];
      const econ = this.factionEconomy(fid);
      const owned = this.sim.ownedProvinces(fid);
      const occupied = owned.filter((p) => this.sim.provinceState[p.id].occupier);
      const sieged = owned.filter((p) => this.sim.provinceState[p.id].siege);
      if (!owned.length) risks.push("landless");
      if (econ && econ.net < 0) risks.push(`deficit ${econ.net}`);
      if (st.treasury < 80) risks.push("low treasury");
      if (st.manpower < st.maxManpower * 0.25) risks.push("low manpower");
      if (st.exhaustion >= 30) risks.push(`war exhaustion ${Math.round(st.exhaustion)}`);
      if (occupied.length) risks.push(`${occupied.length} occupied`);
      if (sieged.length) risks.push(`${sieged.length} under siege`);
      if (!this.sim.heirOf(fid)) risks.push("no clear heir");
      return risks;
    }

    warCasualties(war) {
      return war.battles.reduce((sum, b) => sum + (b.winnerLosses || 0) + (b.loserLosses || 0), 0);
    }

    warSieges(war) {
      const parties = new Set([...(war.atkSide || []), ...(war.defSide || [])]);
      return this.sim.seed.provinces
        .map((p) => ({ p, st: this.sim.provinceState[p.id] }))
        .filter(({ st }) => st.siege && parties.has(st.siege.by));
    }

    warGoalLabel(war) {
      if (!war.goal) return "unknown";
      if (war.goal.type === "raid") return `raid and tribute from ${this.provLink(war.goal.province)}`;
      return `control of ${this.provLink(war.goal.province)}`;
    }

    warWinnerSummary(war) {
      if (war.over) return "concluded";
      const goal = war.goal && war.goal.province ? this.sim.provinceState[war.goal.province] : null;
      const goalHeldByAttacker = goal && (goal.controller === war.attacker || goal.occupier === war.attacker);
      const battleEdge = war.battles.length
        ? war.battles.slice(-5).reduce((score, b) => score + (war.atkSide.includes(b.winner) ? 1 : -1), 0)
        : 0;
      if (war.score >= 15) return goalHeldByAttacker ? "attackers are winning: war score and the goal favor them" : "attackers are winning on war score";
      if (war.score <= -15) return "defenders are winning: attacker pressure is failing";
      if (goalHeldByAttacker) return "attackers have the goal, but the war is still close";
      if (battleEdge > 0) return "attackers have the recent battle edge";
      if (battleEdge < 0) return "defenders have the recent battle edge";
      return "too close to call";
    }

    warOccupationSummary(war) {
      const attackerHeld = this.sim.seed.provinces.filter((p) => {
        const st = this.sim.provinceState[p.id];
        return war.defSide.includes(st.controller) && st.occupier && war.atkSide.includes(st.occupier);
      });
      const defenderHeld = this.sim.seed.provinces.filter((p) => {
        const st = this.sim.provinceState[p.id];
        return war.atkSide.includes(st.controller) && st.occupier && war.defSide.includes(st.occupier);
      });
      const goal = war.goal && war.goal.province ? this.sim.provinceState[war.goal.province] : null;
      const goalHeld = goal && goal.occupier
        ? this.faction(goal.occupier).shortName || this.faction(goal.occupier).name
        : goal ? this.faction(goal.controller).shortName || this.faction(goal.controller).name : "none";
      return {
        attackerHeld,
        defenderHeld,
        label: `attackers hold ${attackerHeld.length} · defenders hold ${defenderHeld.length} · goal held by ${goalHeld}`,
      };
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
      if (this.map.clearSelection) this.map.clearSelection();
      else this.map.selected = null;
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
      const p = this.province(pid);
      if (!p) return;
      if (this.map.selectProvince) this.map.selectProvince(pid);
      else this.map.selected = pid;
      const st = this.provinceState(pid);
      const feature = this.terrainInfo(p.terrainFeature || p.terrain);
      const biome = this.biomeInfo(this.provinceBiomeId(p));
      const river = this.riverFeature(p.id);
      const riverRows = this.riverRows(river);
      const warStatus = this.provinceWarStatus(p, st);
      const claims = this.sim.claims.filter((c) => c.target === pid && c.strength > 10);
      const armies = this.sim.armies.filter((a) => a.loc === pid);
      const why = this.provinceImportance(p, st, river, armies, claims);
      const names = [
        [`Locally`, p.localName], [`In the old imperial rolls`, p.imperialName],
        [`To the faithful`, p.religiousName], [`To its enemies`, p.enemyName],
      ].filter(([, v]) => v && v !== p.name)
        .map(([k, v]) => `<div class="alias"><span>${k}:</span> ${esc(v)}</div>`).join("");

      this._openPanel(`
        <div class="panel-head">
          <h2>${esc(p.name)}</h2>
          <div class="subtitle">${esc(biome.label)} biome · ${esc(String(p.resource || "unknown").replace(/_/g, " ").toLowerCase())}</div>
        </div>
        ${names}
        <div class="stat-rows">
          <div class="row"><span>Controller</span><b>${this.shieldChip(st.controller)}</b></div>
          ${st.staticMapProvince ? `<div class="row"><span>Simulation</span><b class="fine">world-map province</b></div>` : ""}
          ${st.occupier ? `<div class="row occupied"><span>Occupied by</span><b>${this.shieldChip(st.occupier)}</b></div>` : ""}
          ${st.siege ? `<div class="row occupied"><span>Under siege</span><b>${this.shieldChip(st.siege.by)} — ${Math.round(st.siege.progress * 100)}%</b></div>` : ""}
          <div class="row"><span>Current status</span><b class="${warStatus === "peaceful" ? "good" : "bad"}">${esc(warStatus)}</b></div>
          <div class="row"><span>Population</span><b>${st.pop.toLocaleString()}</b></div>
          <div class="row"><span>Garrison</span><b>${Math.round(st.garrison || 0).toLocaleString()}</b></div>
          <div class="row"><span>Fort level</span><b>${this.pips(p.fort, 5, "▲")}</b></div>
          <div class="row"><span>Roads</span><b>${this.pips(p.roads, 5)}</b></div>
          ${p.port ? `<div class="row"><span>Harbour</span><b>${this.pips(p.port, 5)}</b></div>` : ""}
          ${p.manaSite ? `<div class="row"><span>Mana site</span><b>${this.pips(p.manaSite, 3, "✦")}</b></div>` : ""}
          ${st.devastation > 4 ? `<div class="row"><span>Devastation</span><b class="bad">${Math.round(st.devastation)}%</b></div>` : ""}
          <div class="row"><span>Biome</span><b>${esc(biome.label)}</b></div>
          <div class="row"><span>Terrain feature</span><b>${esc(feature.label)}</b></div>
          <div class="row"><span>Economy / value</span><b>${p.value} <span class="fine">roads ${p.roads}, port ${p.port || 0}</span></b></div>
          ${p.regionName ? `<div class="row"><span>Region</span><b>${esc(p.regionName)}</b></div>` : ""}
          <div class="row"><span>Why it matters</span><b>${esc(why || "local holding")}</b></div>
        </div>
        ${riverRows ? `<h3>River data</h3><div class="stat-rows">${riverRows}</div>` : ""}
        ${armies.length ? `<h3>Armies present</h3>` + armies.map((a) =>
          `<div class="row">${this.shieldChip(a.faction)}<b>${a.size.toLocaleString()} under ${this.charLink(a.commanderId)}</b></div>`).join("") : ""}
        ${claims.length ? `<h3>Claims on this land</h3>` + claims.map((c) =>
          `<div class="claim"><b>${this.shieldChip(c.claimant)}</b> — ${esc(c.type)} (${Math.round(c.strength)}) <div class="fine">${esc(c.source)} · ${esc(c.myth)}</div></div>`).join("") : ""}
      `);
    }

    openRealm(fid) {
      const f = this.faction(fid);
      if (!f) return;
      if (this.map.selectRealm) this.map.selectRealm(fid, this.sim);
      if (!this.sim.factionState[fid]) {
        const provinces = this.map && this.map.mapProvinces
          ? this.map.mapProvinces.filter((p) => p.controller === fid)
          : [];
        const culture = this.sim.seed.cultures[f.culture] || {};
        const religion = this.sim.seed.religions[f.religion] || {};
        const biomeCounts = {};
        const featureCounts = {};
        const regionCounts = {};
        for (const p of provinces) {
          const biome = this.provinceBiomeId(p);
          const feature = p.terrainFeature || p.terrain;
          biomeCounts[biome] = (biomeCounts[biome] || 0) + 1;
          featureCounts[feature] = (featureCounts[feature] || 0) + 1;
          regionCounts[p.regionName || p.region] = (regionCounts[p.regionName || p.region] || 0) + 1;
        }
        const topBiomes = Object.entries(biomeCounts)
          .sort((a, b) => b[1] - a[1])
          .slice(0, 4)
          .map(([biome, count]) => `${esc(this.biomeInfo(biome).label)} (${count})`)
          .join(", ");
        const topFeatures = Object.entries(featureCounts)
          .sort((a, b) => b[1] - a[1])
          .slice(0, 4)
          .map(([feature, count]) => `${esc(this.terrainInfo(feature).label)} (${count})`)
          .join(", ");
        const topRegions = Object.entries(regionCounts)
          .sort((a, b) => b[1] - a[1])
          .slice(0, 4)
          .map(([region, count]) => `${esc(region)} (${count})`)
          .join(", ");
        this._openPanel(`
          <div class="panel-head realm-head">
            ${WG.shieldSVG(f, 52)}
            <div>
              <h2>${esc(f.name)}</h2>
              <div class="subtitle">${esc(f.identity || "mapped local power")} · ${esc((f.government || "local_rule").replace(/_/g, " "))}</div>
            </div>
          </div>
          <div class="stat-rows">
            <div class="row"><span>Mapped provinces</span><b>${provinces.length}</b></div>
            <div class="row"><span>Observer state</span><b class="fine">mapped placeholder, not active in the war loop</b></div>
            ${f.pressure ? `<div class="row"><span>Pressure</span><b>${esc(f.pressure)}</b></div>` : ""}
            ${topRegions ? `<div class="row"><span>Regions</span><b>${topRegions}</b></div>` : ""}
            ${topBiomes ? `<div class="row"><span>Biomes</span><b>${topBiomes}</b></div>` : ""}
            ${topFeatures ? `<div class="row"><span>Terrain features</span><b>${topFeatures}</b></div>` : ""}
          </div>
          ${religion.name ? `<h3>Faith — ${esc(religion.name)}</h3><div class="quote">“${esc(religion.claim || "")}”</div>` : ""}
          ${culture.name ? `<h3>Culture — ${esc(culture.name)} (${esc(culture.selfName || "")})</h3>
            <div class="fine">${esc(culture.values || "")}</div>
            <div class="quote">${esc(culture.contradiction || "")}</div>` : ""}
          <h3>Lands</h3>
          ${provinces.slice(0, 36).map((p) =>
            `<div class="row"><span>${this.provLink(p.id)}</span><b class="fine">${esc(this.biomeInfo(this.provinceBiomeId(p)).label)} · ${esc(this.terrainInfo(p.terrainFeature || p.terrain).label)}</b></div>`).join("")}
          ${provinces.length > 36 ? `<div class="fine pad">${provinces.length - 36} more provinces are mapped in this realm.</div>` : ""}
        `);
        return;
      }
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
      const econ = this.factionEconomy(fid);
      const income = econ.income, upkeep = econ.upkeep;
      const risks = this.factionRisks(fid);
      const occupied = provinces.filter((p) => this.sim.provinceState[p.id].occupier);
      const sieged = provinces.filter((p) => this.sim.provinceState[p.id].siege);

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
          <div class="row"><span>Held provinces</span><b>${provinces.length}</b></div>
          <div class="row"><span>Treasury</span><b>${s.treasury.toLocaleString()} silver</b></div>
          ${f.goal ? `<div class="row"><span>Likely goal</span><b>${esc(f.goal.replace(/_/g, " "))}</b></div>` : ""}
          <div class="row"><span>Economy pressure</span><b class="${econ.net >= 0 ? "good" : "bad"}">${econ.net >= 0 ? "+" : ""}${econ.net.toLocaleString()} <span class="fine">income ${income}, upkeep ${upkeep}, court ${econ.court}</span></b></div>
          <div class="row"><span>Army strength</span><b>${this.sim.armyStrength(fid).toLocaleString()} levied</b></div>
          <div class="row"><span>Manpower</span><b>${s.manpower.toLocaleString()} / ${s.maxManpower.toLocaleString()}</b></div>
          <div class="row"><span>Prestige</span><b>${Math.round(s.prestige)}</b></div>
          ${s.exhaustion > 5 ? `<div class="row"><span>War exhaustion</span><b class="bad">${Math.round(s.exhaustion)}</b></div>` : ""}
          ${occupied.length ? `<div class="row occupied"><span>Occupied lands</span><b>${occupied.length}</b></div>` : ""}
          ${sieged.length ? `<div class="row occupied"><span>Under siege</span><b>${sieged.length}</b></div>` : ""}
          <div class="row"><span>Wars won / lost</span><b>${s.warsWon} / ${s.warsLost}</b></div>
          <div class="row"><span>Instability / crisis</span><b class="${risks.length ? "bad" : "good"}">${risks.length ? esc(risks.join(" · ")) : "stable for now"}</b></div>
        </div>
        ${f.pressure ? `<h3>Political pressure</h3><div class="quote">${esc(f.pressure)}</div>` : ""}
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
      const scorePct = Math.max(0, Math.min(100, Math.round((w.score + 100) / 2)));
      const casualties = this.warCasualties(w);
      const sieges = this.warSieges(w);
      const attackerStrength = w.atkSide.reduce((sum, fid) => sum + this.sim.armyStrength(fid), 0);
      const defenderStrength = w.defSide.reduce((sum, fid) => sum + this.sim.armyStrength(fid), 0);
      const attackerExhaustion = w.atkSide.reduce((sum, fid) => sum + (this.sim.factionState[fid]?.exhaustion || 0), 0);
      const defenderExhaustion = w.defSide.reduce((sum, fid) => sum + (this.sim.factionState[fid]?.exhaustion || 0), 0);
      const occupation = this.warOccupationSummary(w);
      const targetProvinces = [w.goal && w.goal.province, ...sieges.map(({ p }) => p.id)]
        .filter(Boolean)
        .filter((id, i, arr) => arr.indexOf(id) === i);
      this._openPanel(`
        <div class="panel-head">
          <h2>${esc(w.name)}</h2>
          <div class="subtitle">${w.over ? `concluded ${esc(w.endDate)}` : `raging since ${esc(w.startDate)}`}</div>
        </div>
        <div class="war-sides">
          <div><div class="fine">Attackers</div>${w.atkSide.map((fid) => this.shieldChip(fid, 24)).join("<br>")}</div>
          <div class="vs">against</div>
          <div><div class="fine">Defenders</div>${w.defSide.map((fid) => this.shieldChip(fid, 24)).join("<br>")}</div>
        </div>
        <div class="stat-rows">
          <div class="row"><span>War goal</span><b>${this.warGoalLabel(w)}</b></div>
          <div class="row"><span>Target provinces</span><b>${targetProvinces.map((id) => this.provLink(id)).join(" · ") || "none"}</b></div>
          <div class="row"><span>Who is winning</span><b class="${w.score > 10 ? "bad" : w.score < -10 ? "good" : ""}">${esc(this.warWinnerSummary(w))}</b></div>
          <div class="row"><span>War score</span><b>${Math.round(w.score)}</b></div>
          <div class="row"><span>Occupation score</span><b>${esc(occupation.label)}</b></div>
          <div class="row"><span>Armies in field</span><b>attackers ${attackerStrength.toLocaleString()} · defenders ${defenderStrength.toLocaleString()}</b></div>
          <div class="row"><span>Exhaustion</span><b>attackers ${Math.round(attackerExhaustion)} · defenders ${Math.round(defenderExhaustion)}</b></div>
          <div class="row"><span>Battles / casualties</span><b>${w.battles.length} / ${casualties.toLocaleString()}</b></div>
          <div class="row"><span>Active sieges</span><b>${sieges.length}</b></div>
        </div>
        ${w.over ? "" : `
          <h3>Fortunes of war</h3>
          <div class="score-bar"><div class="score-fill" style="width:${scorePct}%"></div></div>
          <div class="fine center">${w.score > 10 ? "the attacker has the upper hand" : w.score < -10 ? "the defender holds firm" : "the scales hang level"} (${Math.round(w.score)})</div>`}
        ${sieges.length ? "<h3>Sieges</h3>" + sieges.map(({ p, st }) =>
          `<div class="claim"><b>${this.provLink(p.id)}</b> — ${this.shieldChip(st.siege.by)} ${Math.round(st.siege.progress * 100)}%
           <div class="fine">controller: ${esc(this.faction(st.controller).name)} · fort ${p.fort} · garrison ${Math.round(st.garrison).toLocaleString()}</div></div>`).join("") : ""}
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
      this.el.events.innerHTML = recaps.length ? "" : "<div class='fine center pad'>No month has closed yet.</div>";
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
      if (!prov) { tip.classList.add("hidden"); return; }
      const p = this.province(prov.id) || prov;
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

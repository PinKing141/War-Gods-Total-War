/* Inspector panels: the world, provinces, realms and wars. */
(function () {
  "use strict";

  const esc = window.WG.uiEsc;

  class UIPanels {
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
              <div class="fine">${ruler ? esc(ruler.name) : "—"} · ${esc(this.factionTierLabel(f))} · ${provs} land${provs === 1 ? "" : "s"} · ${s.armyStrength(f.id).toLocaleString()} levied</div>
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
      const instability = this.sim.provinceInstability ? this.sim.provinceInstability(p.id) : { score: st.instability || 0, causes: [] };
      const society = this.sim.provinceSocietySummary ? this.sim.provinceSocietySummary(p.id) : null;
      const societyRows = society ? `
        <h3>Society</h3>
        <div class="stat-rows">
          <div class="row"><span>Social Pressure</span><b>unrest ${Math.round(society.effects.unrest)} · tax x${society.effects.tax.toFixed(2)} · recruits x${society.effects.recruitment.toFixed(2)}</b></div>
          ${society.mostRestive ? `<div class="row"><span>Most Restive</span><b>${esc(society.mostRestive.label)} <span class="fine">${esc(society.mostRestive.needs)} · unrest ${Math.round(society.mostRestive.unrest)}</span></b></div>` : ""}
          ${society.dominant.map((g) => `<div class="row"><span>${esc(g.label)}</span><b>${Math.round(g.size).toLocaleString()} <span class="fine">loyalty ${Math.round(g.loyalty)} · influence ${Math.round(g.influence)} · ${esc(g.needs)}</span></b></div>`).join("")}
        </div>` : "";
      const revolt = st.revoltId && this.sim.revolts ? this.sim.revolts.find((r) => r.id === st.revoltId) : null;
      const names = [
        [`Locally`, p.localName], [`In the old imperial rolls`, p.imperialName],
        [`To the faithful`, p.religiousName], [`To its enemies`, p.enemyName],
      ].filter(([, v]) => v && v !== p.name)
        .map(([k, v]) => `<div class="alias"><span>${k}:</span> ${esc(v)}</div>`).join("");

      const controllerFaction = this.faction(st.controller);
      this._openPanel(`
        <div class="panel-head with-arms">
          <span class="head-arms">${WG.provinceShield ? WG.provinceShield(p, controllerFaction, 46) : ""}</span>
          <div class="head-text">
            <h2>${esc(p.name)}</h2>
            <div class="subtitle">${esc(biome.label)} biome · ${esc(String(p.resource || "unknown").replace(/_/g, " ").toLowerCase())}</div>
          </div>
        </div>
        ${names}
        <div class="stat-rows">
          <div class="row"><span>Controller</span><b>${this.shieldChip(st.controller)}</b></div>
          ${this.debugEnabled && st.staticMapProvince ? `<div class="row"><span>Debug State</span><b class="fine">static map province</b></div>` : ""}
          ${st.occupier ? `<div class="row occupied"><span>Occupied By</span><b>${this.shieldChip(st.occupier)}</b></div>` : ""}
          ${st.siege ? `<div class="row occupied"><span>Under Siege</span><b>${this.shieldChip(st.siege.by)} — ${Math.round(st.siege.progress * 100)}%</b></div>` : ""}
          ${revolt ? `<div class="row occupied"><span>Revolt</span><b>${esc(revolt.type.replace(/_/g, " "))} — ${Math.round(revolt.progress * 100)}%</b></div>` : ""}
          <div class="row"><span>Status</span><b class="${warStatus === "peaceful" ? "good" : "bad"}">${esc(warStatus)}</b></div>
          <div class="row"><span>Population</span><b>${st.pop.toLocaleString()}</b></div>
          <div class="row"><span>Garrison</span><b>${Math.round(st.garrison || 0).toLocaleString()}</b></div>
          <div class="row"><span>Fort Level</span><b>${this.pips(p.fort, 5, "▲")}</b></div>
          <div class="row"><span>Roads</span><b>${this.pips(p.roads, 5)}</b></div>
          ${p.port ? `<div class="row"><span>Harbour</span><b>${this.pips(p.port, 5)}</b></div>` : ""}
          ${p.manaSite ? `<div class="row"><span>Mana Site</span><b>${this.pips(p.manaSite, 3, "✦")}</b></div>` : ""}
          ${st.devastation > 4 ? `<div class="row"><span>Devastation</span><b class="bad">${Math.round(st.devastation)}%</b></div>` : ""}
          ${instability.score > 10 ? `<div class="row"><span>Instability</span><b class="${instability.score >= 55 ? "bad" : ""}">${Math.round(instability.score)} <span class="fine">${esc(instability.causes.join(", ") || "local strain")}</span></b></div>` : ""}
          <div class="row"><span>Biome</span><b>${esc(biome.label)}</b></div>
          <div class="row"><span>Terrain Feature</span><b>${esc(feature.label)}</b></div>
          <div class="row"><span>Economy</span><b>${p.value} <span class="fine">roads ${p.roads}, port ${p.port || 0}</span></b></div>
          ${p.regionName ? `<div class="row"><span>Region</span><b>${esc(p.regionName)}</b></div>` : ""}
          <div class="row"><span>Strategic Value</span><b>${esc(why || "local holding")}</b></div>
        </div>
        ${societyRows}
        ${riverRows ? `<h3>Rivers</h3><div class="stat-rows">${riverRows}</div>` : ""}
        ${armies.length ? `<h3>Armies Present</h3>` + armies.map((a) =>
          `<div class="row">${this.shieldChip(a.faction)}<b>${a.size.toLocaleString()} under ${this.charLink(a.commanderId)} <span class="fine">${a.undersupplied ? "undersupplied" : "supply"} ${Math.round(a.supply || 0)} / ${Math.round(a.maxSupply || 0)}${this.debugEnabled ? ` · ${esc(a.intentReason || "holding position")}` : ""}</span></b></div>`).join("") : ""}
        ${claims.length ? `<h3>Claims</h3>` + claims.map((c) =>
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
            ${this.realmShieldFrame(f)}
            <div>
              <h2>${esc(f.name)}</h2>
              <div class="subtitle">${esc(this.factionTierLabel(f))} · ${esc(f.identity || "frontier power")} · ${esc((f.government || "local_rule").replace(/_/g, " "))}</div>
            </div>
          </div>
          <div class="stat-rows">
            <div class="row"><span>Lands</span><b>${provinces.length}</b></div>
            <div class="row"><span>Tier</span><b>${esc(this.factionTierLabel(f))}</b></div>
            <div class="row"><span>Status</span><b class="fine">surveyed frontier realm</b></div>
            ${this.debugEnabled ? `<div class="row"><span>Debug State</span><b class="fine">not active in the war loop</b></div>` : ""}
            ${f.pressure ? `<div class="row"><span>Conflict</span><b>${esc(f.pressure)}</b></div>` : ""}
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
        if (WG.renderFactionShield) WG.renderFactionShield(f);
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
      const priorities = this.sim.aiPriorityScores ? this.sim.aiPriorityScores(fid).slice(0, 4) : [];
      const internalSummary = this.sim.internalPoliticsSummary ? this.sim.internalPoliticsSummary(fid) : [];
      const succession = this.sim.successionStatus ? this.sim.successionStatus(fid) : null;
      const dynastyInfo = this.sim.dynastySummaryForFaction ? this.sim.dynastySummaryForFaction(fid) : null;
      const court = this.sim.courtOf ? this.sim.courtOf(fid) : s.court;
      const instability = this.sim.internalInstability ? this.sim.internalInstability(fid) : 0;
      const occupied = provinces.filter((p) => this.sim.provinceState[p.id].occupier);
      const sieged = provinces.filter((p) => this.sim.provinceState[p.id].siege);
      const revolting = provinces.filter((p) => this.sim.provinceState[p.id].revoltId);

      this._openPanel(`
        <div class="panel-head realm-head">
          ${this.realmShieldFrame(f)}
          <div>
            <h2>${esc(f.name)}</h2>
            <div class="subtitle">${esc(this.factionTierLabel(f))} · ${esc(f.identity)} · ${esc(f.government.replace(/_/g, " "))}</div>
          </div>
        </div>
        ${ruler ? `<div class="ruler-card" data-open-char="${ruler.id}">
            <div class="ruler-name">${esc(ruler.name)}</div>
            <div class="fine">${esc(ruler.role)} · ${ruler.age} years · ${ruler.traits.map((t) => t.label).join(", ")}</div>
          </div>` : `<div class="ruler-card"><i>The seat stands empty.</i></div>`}
        ${(() => {
          const heir = this.sim.heirOf(fid);
          return heir
            ? `<div class="row"><span>Heir</span><b>${this.charLink(heir.id)} <span class="fine">(${heir.age}${succession ? `, legitimacy ${succession.legitimacy}` : ""})</span></b></div>`
            : `<div class="row"><span>Heir</span><b class="fine"><i>the line hangs by a thread</i></b></div>`;
        })()}
        <div class="stat-rows">
          <div class="row"><span>Held Provinces</span><b>${provinces.length}</b></div>
          <div class="row"><span>Tier</span><b>${esc(this.factionTierLabel(f))}</b></div>
          <div class="row"><span>Treasury</span><b>${s.treasury.toLocaleString()} silver</b></div>
          ${f.goal ? `<div class="row"><span>Goal</span><b>${esc(f.goal.replace(/_/g, " "))}</b></div>` : ""}
          <div class="row"><span>Economy</span><b class="${econ.net >= 0 ? "good" : "bad"}">${econ.net >= 0 ? "+" : ""}${econ.net.toLocaleString()} <span class="fine">income ${income}, upkeep ${upkeep}, court ${econ.court}${econ.debtService ? `, debt ${econ.debtService}` : ""}</span></b></div>
          <div class="row"><span>Taxation</span><b class="${econ.taxBurden >= 70 ? "bad" : ""}">${Math.round(econ.taxBurden || 0)}</b></div>
          <div class="row"><span>Food</span><b class="${econ.foodStress >= 55 ? "bad" : econ.foodStress <= 20 ? "good" : ""}">stress ${Math.round(econ.foodStress || 0)}</b></div>
          <div class="row"><span>Trade</span><b>${Math.round(econ.tradeValue || 0)} <span class="fine">devastation loss ${Math.round(econ.devastationLoss || 0)}</span></b></div>
          ${econ.warDebt ? `<div class="row"><span>War Debt</span><b class="${econ.warDebt >= 700 ? "bad" : ""}">${Math.round(econ.warDebt).toLocaleString()} silver</b></div>` : ""}
          ${econ.tributeDue ? `<div class="row"><span>Tribute</span><b>${Math.round(econ.tributeDue).toLocaleString()} silver owed</b></div>` : ""}
          <div class="row"><span>Army Strength</span><b>${this.sim.armyStrength(fid).toLocaleString()} levied</b></div>
          <div class="row"><span>Manpower</span><b>${s.manpower.toLocaleString()} / ${s.maxManpower.toLocaleString()}</b></div>
          <div class="row"><span>Prestige</span><b>${Math.round(s.prestige)}</b></div>
          ${succession ? `<div class="row"><span>Succession Law</span><b>${esc(succession.law)}</b></div>` : ""}
          ${succession ? `<div class="row"><span>Crisis Risk</span><b class="${succession.crisisRisk >= 55 ? "bad" : succession.crisisRisk <= 24 ? "good" : ""}">${succession.crisisRisk}</b></div>` : ""}
          ${succession && succession.regency ? `<div class="row occupied"><span>Regency</span><b>council rule</b></div>` : ""}
          ${succession && succession.crisis ? `<div class="row occupied"><span>Succession Crisis</span><b>${esc(succession.crisis.backing || "rival claimants")}</b></div>` : ""}
          ${s.internal ? `<div class="row"><span>Internal Stability</span><b class="${instability >= 45 ? "bad" : instability <= 22 ? "good" : ""}">${100 - instability} <span class="fine">instability ${instability}</span></b></div>` : ""}
          ${s.internal ? `<div class="row"><span>Revolt Risk</span><b class="${s.internal.revoltRisk >= 45 ? "bad" : ""}">${s.internal.revoltRisk}</b></div>` : ""}
          ${s.internal ? `<div class="row"><span>Succession Pressure</span><b class="${s.internal.successionPressure >= 55 ? "bad" : ""}">${s.internal.successionPressure}</b></div>` : ""}
          ${s.exhaustion > 5 ? `<div class="row"><span>War Exhaustion</span><b class="bad">${Math.round(s.exhaustion)}</b></div>` : ""}
          ${occupied.length ? `<div class="row occupied"><span>Occupied Lands</span><b>${occupied.length}</b></div>` : ""}
          ${sieged.length ? `<div class="row occupied"><span>Under Siege</span><b>${sieged.length}</b></div>` : ""}
          ${revolting.length ? `<div class="row occupied"><span>Revolts</span><b>${revolting.length}</b></div>` : ""}
          <div class="row"><span>Wars Won / Lost</span><b>${s.warsWon} / ${s.warsLost}</b></div>
          <div class="row"><span>Risk</span><b class="${risks.length ? "bad" : "good"}">${risks.length ? esc(risks.join(" · ")) : "stable for now"}</b></div>
        </div>
        ${f.pressure ? `<h3>Conflict</h3><div class="quote">${esc(f.pressure)}</div>` : ""}
        ${econ.lastDecision ? `<h3>Survival Decision</h3><div class="quote">${esc(econ.lastDecision.text)}</div>` : ""}
        ${priorities.length ? `<h3>Priorities</h3>` + priorities.map((p) =>
          `<div class="row"><span>${esc(p.label)}</span><b>${p.score}</b><div class="fine">${esc(p.reason)}</div></div>`).join("") : ""}
        ${court ? `<h3>Court & Offices</h3>
          <div class="stat-rows">
            <div class="row"><span>Court stability</span><b class="${court.stability < 35 ? "bad" : court.stability > 65 ? "good" : ""}">${Math.round(court.stability || 0)} <span class="fine">${Math.round(court.filled || 0)} offices filled</span></b></div>
            ${this.courtOfficeRows(fid)}
          </div>` : ""}
        ${internalSummary.length ? `<h3>Internal Politics</h3>` + internalSummary.map((p) =>
          `<div class="row"><span>${esc(p.label)}</span><b class="${p.value >= 55 ? "bad" : ""}">${p.value}</b><div class="fine">${esc(p.reason)}</div></div>`).join("") : ""}
        ${succession && succession.pretenders.length ? `<h3>Pretenders</h3>` + succession.pretenders.map((p) =>
          `<div class="row"><span>${this.charLink(p.character)}</span><b>${p.claimStrength}</b><div class="fine">${esc(p.backing || "court backing")}</div></div>`).join("") : ""}
        ${dynastyInfo ? `<h3>Dynasty & House</h3>
          <div class="arms-row">
            <div class="arms-item">${WG.dynastyShield ? WG.dynastyShield(dynastyInfo.dynasty, 40) : ""}<span class="arms-caption">${esc(dynastyInfo.dynasty.name)}</span></div>
            <div class="arms-item">${WG.houseShield ? WG.houseShield(dynastyInfo.house, dynastyInfo.dynasty, 40) : ""}<span class="arms-caption">${esc(dynastyInfo.house.name)}</span></div>
          </div>
          <div class="stat-rows">
            <div class="row"><span>Dynasty</span><b>${esc(dynastyInfo.dynasty.name)} <span class="fine">renown ${Math.round(dynastyInfo.dynasty.renown || 0)}</span></b></div>
            <div class="row"><span>House</span><b>${esc(dynastyInfo.house.name)} <span class="fine">legitimacy ${Math.round(dynastyInfo.house.legitimacy || 0)}</span></b></div>
            ${dynastyInfo.founder ? `<div class="row"><span>Founder</span><b>${this.charLink(dynastyInfo.founder.id)}</b></div>` : ""}
            ${dynastyInfo.head ? `<div class="row"><span>House head</span><b>${this.charLink(dynastyInfo.head.id)}</b></div>` : ""}
            <div class="row"><span>Living members</span><b>${dynastyInfo.house.livingMembers.length} <span class="fine">dynasty members ${dynastyInfo.members.length}</span></b></div>
            ${dynastyInfo.claims.length ? `<div class="row"><span>Claims</span><b>${dynastyInfo.claims.map((claim) => this.provLink(claim.target)).join(", ")}</b></div>` : ""}
            ${dynastyInfo.rivals.length ? `<div class="row"><span>Rivals</span><b>${dynastyInfo.rivals.map((d) => esc(d.name)).join(", ")}</b></div>` : ""}
            ${dynastyInfo.dynasty.cadetBranches && dynastyInfo.dynasty.cadetBranches.length ? `<div class="row"><span>Cadet branches</span><b>${dynastyInfo.dynasty.cadetBranches.map((b) => esc(b.name)).join(", ")}</b></div>` : ""}
          </div>` : ""}
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
      if (WG.renderFactionShield) WG.renderFactionShield(f);
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
          <div class="row"><span>War Goal</span><b>${this.warGoalLabel(w)}</b></div>
          ${w.intentReason ? `<div class="row"><span>Cause</span><b>${esc(w.intentReason)}</b></div>` : ""}
          <div class="row"><span>Target Provinces</span><b>${targetProvinces.map((id) => this.provLink(id)).join(" · ") || "none"}</b></div>
          <div class="row"><span>Balance</span><b class="${w.score > 10 ? "bad" : w.score < -10 ? "good" : ""}">${esc(this.warWinnerSummary(w))}</b></div>
          <div class="row"><span>War Score</span><b>${Math.round(w.score)}</b></div>
          <div class="row"><span>Occupation</span><b>${esc(occupation.label)}</b></div>
          <div class="row"><span>Armies in Field</span><b>attackers ${attackerStrength.toLocaleString()} · defenders ${defenderStrength.toLocaleString()}</b></div>
          <div class="row"><span>Exhaustion</span><b>attackers ${Math.round(attackerExhaustion)} · defenders ${Math.round(defenderExhaustion)}</b></div>
          <div class="row"><span>Battles / Casualties</span><b>${w.battles.length} / ${casualties.toLocaleString()}</b></div>
          <div class="row"><span>Active Sieges</span><b>${sieges.length}</b></div>
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
        ${this.peaceSummaryRows(w)}
      `);
    }
  }

  window.WG.uiMixin(UIPanels);
})();

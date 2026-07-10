/* Shared UI fragments: links, chips, medallions, rows and derived summaries. */
(function () {
  "use strict";

  const esc = window.WG.uiEsc;

  class UIFragments {
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

    factionTierLabel(faction) {
      return faction && faction.tierLabel
        ? faction.tierLabel
        : { tier_1: "Great Power", tier_2: "Regional Power", tier_3: "Minor State", tier_4: "Background Power" }[(faction && faction.tier) || "tier_3"] || "Minor State";
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
      return `<span class="chip" data-open-realm="${f.id}">${WG.shieldSVG(f, size || 18)}<span class="chip-label">${esc(f.name)}</span></span>`;
    }

    realmShieldFrame(f) {
      const src = WG.armoriaShieldSrc
        ? WG.armoriaShieldSrc(f)
        : `assets/armoria/index.html?seed=${encodeURIComponent(f.id)}&view=1`;
      return `<div id="faction-shield-wrapper" class="faction-shield-wrapper" aria-label="${esc(f.name)} coat of arms">
        <iframe
          id="armoria-iframe"
          class="armoria-iframe"
          src="${esc(src)}"
          width="100%"
          height="100%"
          frameborder="0"
          scrolling="no"
          allowtransparency="true"
          title="${esc(f.name)} coat of arms">
        </iframe>
      </div>`;
    }

    charLink(cid) {
      const c = this.sim.character(cid);
      if (!c) return "<i>unknown</i>";
      return `<a data-open-char="${c.id}">${esc(c.name)}${c.alive ? "" : " †"}</a>`;
    }

    characterTooltip(c) {
      if (!c) return "Unknown person";
      const f = this.faction(c.faction);
      const family = c.family || {};
      const parts = [
        c.name,
        `age ${c.age}`,
        c.role,
        f && f.name,
        family.house || c.house,
        c.alive ? `health ${Math.round(c.health || 0)}` : "dead",
      ].filter(Boolean);
      return parts.join(" | ");
    }

    officeLabel(office) {
      return this.sim.officeLabel ? this.sim.officeLabel(office) : String(office || "").replace(/_/g, " ");
    }

    courtOfficeRows(fid) {
      const court = this.sim.courtOf ? this.sim.courtOf(fid) : (this.sim.factionState[fid] || {}).court;
      if (!court || !court.offices) return "";
      const preferred = ["ruler", "heir", "chancellor", "marshal", "steward", "spymaster", "court_mage", "high_priest", "captain_of_guard", "governor", "regent"];
      return preferred.map((office) => {
        const assignment = court.offices[office];
        const holder = assignment && this.sim.character(assignment.character);
        return `<div class="row"><span>${esc(this.officeLabel(office))}</span><b>${holder ? this.charLink(holder.id) : "<span class='fine'>vacant</span>"} ${assignment ? `<span class="fine">effectiveness ${Math.round(assignment.effectiveness || 0)}</span>` : ""}</b></div>`;
      }).join("");
    }

    portraitMedallion(charOrId, options = {}) {
      const c = typeof charOrId === "string" ? this.sim.character(charOrId) : charOrId;
      if (!c) return `<span class="ck-portrait ck-portrait-empty ${esc(options.className || "")}" title="Unknown person"><span class="ck-silhouette"></span></span>`;
      const sizeClass = options.size ? ` ck-portrait-${options.size}` : "";
      const deadClass = c.alive ? "" : " is-dead";
      const rulerClass = c.isRuler ? " is-ruler" : "";
      const ofDynasty = this._viewDynastyId && c.family && c.family.dynastyId === this._viewDynastyId;
      const label = options.label !== undefined && options.label !== null && options.label !== ""
        ? `<span class="ck-portrait-label">${esc(options.label)}</span>` : "";
      const banner = options.banner ? `<span class="ck2-medal-banner">${esc(options.banner)}</span>` : "";
      return `<button class="ck-portrait${sizeClass}${deadClass}${rulerClass} ${esc(options.className || "")}" data-open-char="${c.id}" title="${esc(this.characterTooltip(c))}" aria-label="${esc(this.characterTooltip(c))}">
        <span class="ck-silhouette" aria-hidden="true"></span>
        ${c.alive ? "" : `<span class="ck2-cross" aria-hidden="true">✝</span>`}
        ${ofDynasty && !options.noDrop ? `<span class="ck2-drop" aria-hidden="true"></span>` : ""}
        ${label}
        ${banner}
      </button>`;
    }

    /* Display-only placeholder for the five CK2-style base attributes.
       There is no stats system behind these yet — values are seeded from
       the character id so each person reads as a distinct individual.
       Replace with real sim data when the attribute system is built. */
    placeholderSkill(cid, key) {
      let h = 2166136261 >>> 0;
      const s = `${cid}:${key}`;
      for (let i = 0; i < s.length; i += 1) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); }
      return 2 + ((h >>> 0) % 17); // 2..18, CK2-like spread
    }

    familyPortraitRow(label, people, limit) {
      const visible = (people || []).slice(0, limit || 14);
      const more = people && people.length > visible.length ? `<span class="ck-more">+${people.length - visible.length}</span>` : "";
      return `<div class="ck2-band">
        <div class="ck2-band-title">${esc(label)}</div>
        <div class="ck-family-strip">
          ${visible.length ? visible.map((person) => this.portraitMedallion(person, { size: "small", label: person.age })).join("") + more : `<span class="ck-empty">None recorded</span>`}
        </div>
      </div>`;
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
      if (st.revoltId) {
        const revolt = this.sim.revolts && this.sim.revolts.find((r) => r.id === st.revoltId);
        return revolt ? `${revolt.type.replace(/_/g, " ")} (${Math.round(revolt.progress * 100)}%)` : "revolt reported";
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
      if (st.revoltId) reasons.push("active revolt");
      if ((st.instability || 0) >= 45) reasons.push(`instability ${Math.round(st.instability)}`);
      if (st.occupier) reasons.push("occupied territory");
      if (armies.length) reasons.push("armies present");
      if (claims.length) reasons.push(`${claims.length} active claim${claims.length === 1 ? "" : "s"}`);
      if (!reasons.length && p.resource) reasons.push(`${String(p.resource).replace(/_/g, " ").toLowerCase()} resource`);
      return reasons.join(" · ");
    }

    factionEconomy(fid) {
      const st = this.sim.factionState[fid];
      if (!st) return null;
      if (this.sim.economySnapshot) return this.sim.economySnapshot(fid);
      const income = this.sim.monthlyIncome(fid);
      const upkeep = this.sim.monthlyUpkeep(fid);
      const court = Math.max(0, Math.round(st.treasury * 0.02));
      return { income, upkeep, court, net: income - upkeep - court, warDebt: 0, foodStress: 0, tradeValue: 0, devastationLoss: 0, tributeDue: 0 };
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
      if (econ && econ.warDebt > 600) risks.push(`war debt ${econ.warDebt}`);
      if (econ && econ.foodStress >= 55) risks.push(`food stress ${econ.foodStress}`);
      if (st.manpower < st.maxManpower * 0.25) risks.push("low manpower");
      if (st.exhaustion >= 30) risks.push(`war exhaustion ${Math.round(st.exhaustion)}`);
      if (this.sim.internalInstability && this.sim.internalInstability(fid) >= 45) risks.push(`internal instability ${this.sim.internalInstability(fid)}`);
      if (st.internal && st.internal.revoltRisk >= 45) risks.push(`revolt risk ${st.internal.revoltRisk}`);
      if (st.internal && st.internal.successionPressure >= 55) risks.push(`succession pressure ${st.internal.successionPressure}`);
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

    peaceSummaryRows(war) {
      const summary = war.peaceSummary;
      if (!summary) return "";
      const changed = (summary.changedHands || []).map((change) => {
        if (change.province) {
          return `${this.provLink(change.province)}: ${esc(this.faction(change.from).shortName || this.faction(change.from).name)} to ${esc(this.faction(change.to).shortName || this.faction(change.to).name)}`;
        }
        if (change.tributeFrom) {
          return `${esc(this.faction(change.tributeFrom).shortName || this.faction(change.tributeFrom).name)} pays ${change.silver} silver and ${change.futureTribute} future tribute`;
        }
        if (change.reparationsFrom) {
          return `${esc(this.faction(change.reparationsFrom).shortName || this.faction(change.reparationsFrom).name)} pays ${change.silver} silver reparations`;
        }
        return "";
      }).filter(Boolean).join(" · ") || "no land changed hands";
      const prestige = (summary.prestige || [])
        .map((p) => `${esc(this.faction(p.faction).shortName || this.faction(p.faction).name)} +${p.amount}`)
        .join(" · ") || "none";
      const losses = (summary.standingLosses || [])
        .map((p) => `${esc(this.faction(p.faction).shortName || this.faction(p.faction).name)}: ${esc(p.reason)}`)
        .join(" · ") || "none";
      return `
        <h3>Peace Summary</h3>
        <div class="stat-rows">
          <div class="row"><span>Cause</span><b>${esc(summary.reason || "unknown")}</b></div>
          <div class="row"><span>Changed Hands</span><b>${changed}</b></div>
          <div class="row"><span>Prestige Gained</span><b>${prestige}</b></div>
          <div class="row"><span>Standing Lost</span><b>${losses}</b></div>
          <div class="row"><span>Truce</span><b>${esc(summary.truce || "none")}</b></div>
        </div>
      `;
    }
  }

  window.WG.uiMixin(UIFragments);
})();

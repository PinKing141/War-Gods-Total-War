/* CK2-style character sheet: stone frame, medallions, tabs and mini-strips. */
(function () {
  "use strict";

  const esc = window.WG.uiEsc;

  class UICharacterSheet {
    openCharacter(cid) {
      const c = this.sim.character(cid);
      if (!c) return;
      const f = this.sim.faction(c.faction);
      const species = this.sim.seed.species[c.species] || { name: c.species };
      const culture = this.sim.seed.cultures[c.culture] || { name: c.culture };
      const faith = this.sim.seed.religions[c.faith] || { name: c.faith || "unknown faith" };
      const mage = this.sim.mages.find((m) => m.character === cid);
      const armies = this.sim.armies.filter((a) => a.commanderId === cid);
      const drive = this.sim.characterDriveProfile ? this.sim.characterDriveProfile(c) : null;
      const relationships = this.sim.relationshipsOf
        ? this.sim.relationshipsOf(cid, { outgoingOnly: true }).slice(0, 8)
        : [];
      const record = c.militaryRecord || {};
      const memories = Array.isArray(c.memories) ? c.memories.slice(0, 8) : [];
      const family = c.family || {};
      const closeFamily = this.sim.closeFamilyOf ? this.sim.closeFamilyOf(cid) : { parents: [], children: [], siblings: [], spouses: [], lovers: [] };
      const dynasty = family.dynastyId && this.sim.dynasty ? this.sim.dynasty(family.dynastyId) : null;
      const house = family.houseId && this.sim.house ? this.sim.house(family.houseId) : null;
      const houseHead = house && house.head ? this.sim.character(house.head) : null;
      const houseFounder = house && house.founder ? this.sim.character(house.founder) : null;
      const dynastyFounder = dynasty && dynasty.founder ? this.sim.character(dynasty.founder) : null;
      const dynastyHead = dynasty && dynasty.head ? this.sim.character(dynasty.head) : null;
      const heir = this.sim.heirOf(c.faction);
      const succession = this.sim.successionStatus ? this.sim.successionStatus(c.faction) : null;
      const characterClaims = (this.sim.claims || [])
        .filter((claim) => claim.claimant === c.faction)
        .slice(0, 6);
      const activeWars = this.sim.warsOf(c.faction).slice(0, 4);
      const notableVictories = Array.isArray(record.notableVictories) ? record.notableVictories.slice(0, 3) : [];
      const notableDefeats = Array.isArray(record.notableDefeats) ? record.notableDefeats.slice(0, 3) : [];
      const houseMemberCount = house && Array.isArray(house.members) ? house.members.length : 0;
      const dynastyMemberCount = dynasty && Array.isArray(dynasty.members) ? dynasty.members.length : 0;
      const offices = this.sim.characterOffices ? this.sim.characterOffices(c.id) : [];
      const dynasticRole = house && house.head === c.id
        ? "House head"
        : dynasty && dynasty.head === c.id
          ? "Dynasty head"
          : heir && heir.id === c.id
            ? "Heir"
            : c.isRuler
              ? "Ruler"
              : "House member";
      const traitList = (c.traits || []).map((t) => `<span class="trait">${esc(t.label || t.id || t)}</span>`).join(" ");
      const dynastyPeople = [dynastyFounder, dynastyHead, houseFounder, houseHead].filter(Boolean)
        .filter((person, index, arr) => arr.findIndex((other) => other.id === person.id) === index);

      /* grandparents = parents of parents */
      const grandparents = [];
      for (const parent of closeFamily.parents || []) {
        const pf = this.sim.closeFamilyOf ? this.sim.closeFamilyOf(parent.id) : null;
        for (const gp of (pf && pf.parents) || []) {
          if (!grandparents.some((g) => g.id === gp.id)) grandparents.push(gp);
        }
      }

      /* the drop marks members of the viewed character's dynasty */
      this._viewDynastyId = family.dynastyId || null;

      const wife = (closeFamily.spouses || [])[0] || null;
      const court = this.sim.courtOf ? this.sim.courtOf(c.faction) : (this.sim.factionState[c.faction] || {}).court;
      const regentId = court && court.offices && court.offices.regent && court.offices.regent.character;
      const regent = regentId ? this.sim.character(regentId) : null;
      const underMedals = [
        c.isRuler && heir && heir.id !== c.id ? this.portraitMedallion(heir, { banner: "Heir", className: "ck2-heir-medal" }) : "",
        regent && regent.id !== c.id ? this.portraitMedallion(regent, { banner: "Regent", className: "ck2-heir-medal" }) : "",
      ].filter(Boolean).join("");

      /* five CK2-style base attributes — display-only placeholders for now */
      const skillDefs = [
        ["⚜", "Diplomacy", "diplomacy"],
        ["⚔", "Martial", "martial"],
        ["⚖", "Stewardship", "stewardship"],
        ["✒", "Intrigue", "intrigue"],
        ["✦", "Learning", "learning"],
      ];
      const skillRows = skillDefs.map(([glyph, label, key]) => {
        const base = this.placeholderSkill(c.id, key);
        const total = base + this.placeholderSkill(c.id, key + ":bonus") % 9;
        return `<div class="ck2-skillrow" title="${esc(label)} (placeholder)"><i>${glyph}</i><span>${esc(label)}</span><b>${base} <em>(${total})</em></b></div>`;
      }).join("");

      const dynRow = (glyph, label, value, cls) =>
        `<div class="ck2-dynrow"><i>${glyph}</i><span>${esc(label)}</span><b class="${cls || ""}">${value}</b></div>`;

      /* ---- heraldic mini-strips: demesne, pacts, wars, claims ----
         Rows of shields only — the story lives in the tooltips. */
      const mini = (html, tip, cls) =>
        `<span class="ck2-mini ${cls || ""}" title="${esc(tip)}">${html}</span>`;
      const miniStrip = (glyph, tip, items) => items.length
        ? `<div class="ck2-ministrip"><i class="ck2-mini-glyph" title="${esc(tip)}">${glyph}</i>${items.join("")}</div>`
        : "";

      /* Demesne: the lands held directly. A ruler can only govern a few
         provinces personally before revolt pressure forces granting the
         rest to vassals, nobles and kin — the vassalage system itself is
         not yet simulated, so until then the demesne is the capital plus
         the highest-value holdings up to a placeholder limit, and the
         remainder are shown dimmed as "granted". */
      const DEMESNE_LIMIT = 3;
      const demesneItems = [];
      if (f && this.sim.ownedProvinces) {
        const owned = (this.sim.ownedProvinces(c.faction) || []).slice()
          .sort((a, b) => (b.value || 0) - (a.value || 0));
        if (c.isRuler) {
          owned.slice(0, DEMESNE_LIMIT).forEach((p) => demesneItems.push(
            mini(WG.provinceShield(p, f, 26), `${p.name} — held directly (demesne)`)));
          owned.slice(DEMESNE_LIMIT, DEMESNE_LIMIT + 6).forEach((p) => demesneItems.push(
            mini(WG.provinceShield(p, f, 26), `${p.name} — granted to a vassal noble to govern`, "is-granted")));
          if (owned.length > DEMESNE_LIMIT + 6) demesneItems.push(`<span class="ck2-mini-more">+${owned.length - DEMESNE_LIMIT - 6}</span>`);
        } else if (dynasty && dynasty.homeProvince) {
          const home = this.province(dynasty.homeProvince);
          const holder = home && this.faction(this.sim.provinceState[home.id]?.controller || home.controller);
          if (home) demesneItems.push(mini(WG.provinceShield(home, holder || f, 26), `${home.name} — seat of ${dynasty.name}`));
        }
      }

      /* Pacts: truces (non-aggression), war-side alliances, dynastic bonds */
      const pactItems = [];
      const fState = this.sim.factionState ? this.sim.factionState[c.faction] : null;
      if (fState && fState.truces) {
        for (const [other, until] of Object.entries(fState.truces)) {
          if (until <= this.sim.day) continue;
          const of = this.faction(other);
          if (!of) continue;
          const years = Math.max(1, Math.round((until - this.sim.day) / 360));
          pactItems.push(mini(WG.shieldSVG(of, 26), `Non-aggression truce with ${of.name} — ${years} more year${years > 1 ? "s" : ""}`));
        }
      }
      const allies = new Set();
      for (const w of activeWars) {
        const side = w.atkSide.includes(c.faction) ? w.atkSide : w.defSide.includes(c.faction) ? w.defSide : [];
        side.forEach((fid) => { if (fid !== c.faction) allies.add(fid); });
      }
      for (const fid of allies) {
        const of = this.faction(fid);
        if (of) pactItems.push(mini(WG.shieldSVG(of, 26), `Alliance in arms with ${of.name}`));
      }
      if (dynasty && Array.isArray(dynasty.alliances)) {
        for (const did of dynasty.alliances.slice(0, 4)) {
          const od = this.sim.dynasty ? this.sim.dynasty(did) : null;
          if (od && od.id !== dynasty.id) pactItems.push(mini(WG.dynastyShield(od, 26), `Bond of marriage and friendship with Dynasty ${od.name}`));
        }
      }

      /* Wars: the enemy's arms */
      const warItems = [];
      for (const w of activeWars) {
        const attacking = w.atkSide.includes(c.faction);
        const enemies = attacking ? w.defSide : w.atkSide;
        for (const fid of enemies) {
          const of = this.faction(fid);
          if (of) warItems.push(mini(WG.shieldSVG(of, 26), `${w.name} — ${attacking ? "attacking" : "defending against"} ${of.name}, war score ${Math.round(w.score || 0)}`, "is-war"));
        }
      }

      /* Claims: the coveted land's arms in its current holder's colours */
      const claimItems = characterClaims.map((claim) => {
        const p = this.province(claim.target);
        if (!p) return "";
        const st = this.sim.provinceState[p.id] || {};
        const holder = this.faction(st.controller || p.controller);
        return mini(WG.provinceShield(p, holder || f, 26),
          `Claim on ${p.name} — ${claim.type || "claim"}, strength ${Math.round(claim.strength || 0)}${holder ? `, held by ${holder.name}` : ""}`);
      }).filter(Boolean);

      const miniStrips = [
        miniStrip("⌂", "Demesne — lands held directly; the rest are granted to vassals", demesneItems),
        miniStrip("⚭", "Pacts — truces, alliances and marriage bonds", pactItems),
        miniStrip("⚔", "Wars currently being waged", warItems),
        miniStrip("⚑", "Claims pressed by this realm", claimItems),
      ].join("");

      const familyPane = `
        <div class="ck2-band-split">
          ${this.familyPortraitRow("Parents", closeFamily.parents, 6)}
          ${this.familyPortraitRow("Grandparents", grandparents, 6)}
        </div>
        ${this.familyPortraitRow("Children", closeFamily.children, 14)}
        ${this.familyPortraitRow("Siblings", closeFamily.siblings, 14)}
        <div class="ck2-band-split">
          ${this.familyPortraitRow("Spouses", closeFamily.spouses, 6)}
          ${this.familyPortraitRow("Lovers", closeFamily.lovers, 6)}
        </div>
        ${this.familyPortraitRow("Dynasty", dynastyPeople, 10)}`;

      const relationsPane = `
        ${relationships.length ? `<div class="ck2-band"><div class="ck2-band-title">Bonds & Grudges</div>
          <div class="ck-family-strip ck-relations-strip">
            ${relationships.map((r) => {
              const other = this.sim.character(r.to);
              const label = `${r.type.replace(/_/g, " ")} ${Math.round(r.strength || 0)}`;
              return other ? this.portraitMedallion(other, { size: "small", label }) : `<span class="ck-empty">${esc(r.to)}</span>`;
            }).join("")}
          </div></div>` : `<div class="ck-empty pad">No recorded bonds.</div>`}
        ${c.loyalties ? `<div class="stat-rows">
          <div class="row"><span>Faction</span><b>${this.shieldChip(c.loyalties.faction || c.faction)}</b></div>
          ${c.loyalties.dynasty ? `<div class="row"><span>Dynasty</span><b>${esc(c.loyalties.dynasty)}</b></div>` : ""}
          ${c.loyalties.faith ? `<div class="row"><span>Faith</span><b>${esc((this.sim.seed.religions[c.loyalties.faith] || {}).name || c.loyalties.faith)}</b></div>` : ""}
        </div>` : ""}`;

      const courtPane = `
        ${offices.length ? `<div class="ck2-band"><div class="ck2-band-title">Offices Held</div></div>
          <div class="stat-rows">${offices.map((o) => `<div class="row"><span>${esc(o.label)}</span><b>${esc((this.faction(o.faction) || {}).name || o.faction)} <span class="fine">effectiveness ${Math.round(o.effectiveness || 0)}</span></b></div>`).join("")}</div>` : ""}
        <div class="ck2-band"><div class="ck2-band-title">The Court of ${f ? esc(f.name) : "?"}</div></div>
        <div class="stat-rows">${this.courtOfficeRows(c.faction) || `<div class="row"><span>Court</span><b class="fine">No court records</b></div>`}</div>`;

      const warsPane = `
        <div class="ck2-band"><div class="ck2-band-title">Claims & Wars</div></div>
        <div class="stat-rows">
          ${characterClaims.length ? characterClaims.map((claim) => `<div class="row"><span>${this.provLink(claim.target)}</span><b>${esc(claim.type || "claim")} <span class="fine">strength ${Math.round(claim.strength || 0)}</span></b></div>`).join("") : `<div class="row"><span>Claims</span><b class="fine">No active faction claims</b></div>`}
          ${activeWars.length ? activeWars.map((w) => `<div class="row"><span>${this.warLink(w.id)}</span><b>${w.attacker === c.faction ? "attacking" : "defending"} <span class="fine">score ${Math.round(w.score || 0)}</span></b></div>`).join("") : `<div class="row"><span>Wars</span><b class="fine">No active wars</b></div>`}
        </div>
        <div class="ck2-band"><div class="ck2-band-title">Military Record</div></div>
        <div class="stat-rows">
          <div class="row"><span>Record</span><b>${Math.round(record.battlesWon || 0)}-${Math.round(record.battlesLost || 0)} in ${Math.round(record.battlesFought || 0)} battles</b></div>
          <div class="row"><span>Sieges / wounds</span><b>${Math.round(record.siegesLed || 0)} / ${Math.round(record.wounds || 0)}</b></div>
          ${c.kills ? `<div class="row"><span>Soldiers slain under command</span><b>${c.kills.toLocaleString()}</b></div>` : ""}
          ${armies.length ? armies.map((a) => `<div class="row"><span>Command</span><b>${a.size.toLocaleString()} at ${this.provLink(a.loc)}</b></div>`).join("") : `<div class="row"><span>Command</span><b class="fine">No field command</b></div>`}
        </div>
        ${(notableVictories.length || notableDefeats.length) ? `<div class="ck2-band"><div class="ck2-band-title">Notable Battles</div></div>
          <div class="stat-rows">
            ${notableVictories.map((b) => `<div class="row"><span>Victory</span><b>${esc(b.name || "battle")} <span class="fine">${esc(b.date || "")}</span></b></div>`).join("")}
            ${notableDefeats.map((b) => `<div class="row"><span>Defeat</span><b>${esc(b.name || "battle")} <span class="fine">${esc(b.date || "")}</span></b></div>`).join("")}
          </div>` : ""}`;

      const storyPane = `
        <div class="quote">Ambition: ${esc(c.ambition || "unknown")} | Fear: ${esc(c.fear || "unknown")}.</div>
        ${drive ? `<div class="quote">Drive: ${esc(drive.summary)}.</div>` : ""}
        <div class="quote">Their burden: ${esc(c.pressure)}.</div>
        <div class="ck2-band"><div class="ck2-band-title">Standing</div></div>
        <div class="stat-rows">
          ${family.branchType === "cadet" ? `<div class="row"><span>Cadet branch</span><b>${esc(family.cadetReason || "cadet branch")} <span class="fine">founder ${family.branchFounder ? this.charLink(family.branchFounder) : "unknown"}</span></b></div>` : ""}
          ${family.bastard ? `<div class="row"><span>Birth status</span><b class="${family.legitimised ? "good" : "bad"}">${family.legitimised ? "legitimised bastard" : "bastard"}</b></div>` : ""}
          <div class="row"><span>Dynastic role</span><b>${esc(dynasticRole)}</b></div>
          <div class="row"><span>Inheritance</span><b>${family.inheritanceRank ? `rank ${Math.round(family.inheritanceRank)}` : "unranked"} <span class="fine">claim ${Math.round(family.claimStrength || 0)} | family legitimacy ${Math.round(family.legitimacy || 0)}</span></b></div>
          ${succession && heir && heir.id === c.id ? `<div class="row"><span>Succession standing</span><b class="${succession.legitimacy < 40 ? "bad" : succession.legitimacy > 70 ? "good" : ""}">heir legitimacy ${succession.legitimacy} <span class="fine">crisis risk ${succession.crisisRisk}</span></b></div>` : ""}
          ${dynasty && dynasty.homeProvince ? `<div class="row"><span>Home province</span><b>${this.provLink(dynasty.homeProvince)}</b></div>` : ""}
        </div>
        ${memories.length ? `<div class="ck2-band"><div class="ck2-band-title">Memories</div></div>
          <div class="stat-rows">
            ${memories.map((m) => `<div class="row"><span>${esc(m.type || "memory")}</span><b>${esc(m.text || "")} <span class="fine">${esc(m.date || "")}</span></b></div>`).join("")}
          </div>` : ""}
        ${mage ? `<div class="ck2-band"><div class="ck2-band-title">The Gift</div></div>
          <div class="stat-rows">
            <div class="row"><span>Specialization</span><b>${esc(mage.specialization)}</b></div>
            <div class="row"><span>Capacity / Control</span><b>${mage.capacity} / ${mage.control}</b></div>
            <div class="row"><span>Standing in law</span><b>${esc(mage.legal)}</b></div>
            <div class="row"><span>Risk</span><b class="${mage.risk > 50 ? "bad" : ""}">${mage.risk}</b></div>
            ${mage.alive ? "" : `<div class="row"><span></span><b class="bad">The gift has consumed them.</b></div>`}
          </div>` : ""}`;

      this._openPanel(`
        <div class="ck2-sheet">
          <div class="ck2-top">
            <div class="ck2-namebar">
              <span class="ck2-name">${esc(c.name)}${c.alive ? "" : " †"} of ${f ? esc(f.name) : "?"}</span>
              <span class="ck2-age">${c.age}</span>
            </div>
            <div class="ck2-top-body">
              <div class="ck2-left-plate">
                ${c.isRuler ? `<span class="ck2-rank-crown" title="Ruler">♛</span>` : ""}
                <span class="ck2-arms ck2-realm-arms" title="${f ? esc(f.name) : "Realm"}">${f && WG.shieldSVG ? WG.shieldSVG(f, 52) : ""}</span>
                <span class="ck2-arms" title="Personal arms">${WG.characterShield ? WG.characterShield(c, house, dynasty, 40) : ""}</span>
                <span class="ck2-arms-caption">${esc(c.role || "")}</span>
              </div>
              <div class="ck2-portrait-plate">
                <div class="ck2-portrait-cluster">
                  ${this.portraitMedallion(c, { size: "large", noDrop: true, className: "ck2-main-portrait" })}
                  ${wife && wife.id !== c.id ? this.portraitMedallion(wife, { banner: "Spouse", className: "ck2-spouse-overlap" }) : ""}
                </div>
                ${underMedals ? `<div class="ck2-under-medals">${underMedals}</div>` : ""}
                <div class="ck2-traitbar">${traitList || `<span class="fine">No recorded traits</span>`}</div>
                ${miniStrips ? `<div class="ck2-ministrips">${miniStrips}</div>` : ""}
              </div>
              <div class="ck2-dynbox">
                <div class="ck2-dynsection">
                  <div class="ck2-dynname">${dynasty ? esc(dynasty.name) : "Lowborn"}</div>
                  <div class="ck2-dyn-arms">
                    ${dynasty && WG.dynastyShield ? WG.dynastyShield(dynasty, 44) : ""}
                    ${house && house.branchType === "cadet" && WG.houseShield ? WG.houseShield(house, dynasty, 34) : ""}
                  </div>
                  <div class="ck2-tree-buttons">
                    <button class="ck2-tree-btn" data-open-familytree="${c.id}" title="Family tree"><span>⚭</span></button>
                    <button class="ck2-tree-btn" data-open-dynastytree="${dynasty ? dynasty.id : ""}" ${dynasty ? "" : "disabled"} title="Dynasty tree"><span>⌘</span></button>
                  </div>
                  <div class="ck2-culture-line">${esc(culture.name || species.name || "")}</div>
                  <div class="ck2-faith-line" title="${esc(faith.name || c.faith)}"><i>✝</i><span>${esc(faith.name || c.faith)}</span></div>
                </div>
                <div class="ck2-dynsection">
                  ${dynRow("●", "Wealth", `${Math.round(c.wealth || 0).toLocaleString()}`)}
                  ${dynRow("★", "Prestige", Math.round(c.prestige || 0))}
                  ${dynRow("✠", "Legitimacy", Math.round(c.legitimacy || 0), (c.legitimacy || 0) < 35 ? "bad" : "")}
                  ${dynRow("♥", "Health", Math.round(c.health || 0), (c.health || 0) < 35 ? "bad" : "")}
                  ${dynRow("▲", "Stress", Math.round(c.stress || 0), (c.stress || 0) > 65 ? "bad" : "")}
                  ${dynRow("✎", "Born", `${c.birthYear} AE${c.deathYear ? ` — † ${c.deathYear} AE` : ""}`)}
                  ${c.isRuler && c.reignStart ? dynRow("♛", "Reigning", `since ${c.reignStart} AE`) : ""}
                  ${dynasty ? dynRow("✦", "Renown", Math.round(dynasty.renown || 0)) : ""}
                </div>
                <div class="ck2-skillrows">${skillRows}</div>
              </div>
            </div>
          </div>

          <div class="ck2-tabs">
            <div class="ck2-tab active" data-ck2-tab="family">Family</div>
            <div class="ck2-tab" data-ck2-tab="relations">Relations</div>
            <div class="ck2-tab" data-ck2-tab="court">Court</div>
            <div class="ck2-tab" data-ck2-tab="wars">Wars</div>
            <div class="ck2-tab" data-ck2-tab="story">Story</div>
          </div>
          <div class="ck2-panes">
            <div class="ck2-pane active" data-ck2-pane="family">${familyPane}</div>
            <div class="ck2-pane" data-ck2-pane="relations">${relationsPane}</div>
            <div class="ck2-pane" data-ck2-pane="court">${courtPane}</div>
            <div class="ck2-pane" data-ck2-pane="wars">${warsPane}</div>
            <div class="ck2-pane" data-ck2-pane="story">${storyPane}</div>
          </div>
        </div>
      `, { wide: true });
      this._viewDynastyId = null;
    }
  }

  window.WG.uiMixin(UICharacterSheet);
})();

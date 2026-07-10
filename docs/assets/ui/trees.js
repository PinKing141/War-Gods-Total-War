/* Floating parchment windows: family tree and dynasty tree. */
(function () {
  "use strict";

  const esc = window.WG.uiEsc;

  class UITreeWindows {

    /* ============ floating windows: family & dynasty trees ============
       Standalone parchment windows the observer can drag anywhere and
       stack. Read-only, like everything else in the sim. */

    openFloatWindow(key, title, contentHTML) {
      const existing = document.querySelector(`.ck2-window[data-window="${key}"]`);
      if (existing) { this._raiseWindow(existing); return existing; }
      this._windowZ = (this._windowZ || 300) + 1;
      const count = document.querySelectorAll(".ck2-window").length;
      const win = document.createElement("div");
      win.className = "ck2-window";
      win.dataset.window = key;
      win.style.left = `${90 + count * 34}px`;
      win.style.top = `${70 + count * 30}px`;
      win.style.zIndex = this._windowZ;
      win.innerHTML = `
        <div class="ck2-window-title">
          <span class="ck2-window-name">${esc(title)}</span>
          <button class="ck2-window-close" data-close-window title="Close">✕</button>
        </div>
        <div class="ck2-window-body">${contentHTML}</div>`;
      document.body.appendChild(win);
      win.addEventListener("mousedown", () => this._raiseWindow(win));
      this._makeDraggable(win, win.querySelector(".ck2-window-title"));
      return win;
    }

    _raiseWindow(win) {
      this._windowZ = (this._windowZ || 300) + 1;
      win.style.zIndex = this._windowZ;
    }

    _makeDraggable(win, handle) {
      let startX = 0, startY = 0, origX = 0, origY = 0;
      const onMove = (ev) => {
        win.style.left = `${origX + ev.clientX - startX}px`;
        win.style.top = `${Math.max(0, origY + ev.clientY - startY)}px`;
      };
      const onUp = () => {
        document.removeEventListener("mousemove", onMove);
        document.removeEventListener("mouseup", onUp);
        win.classList.remove("dragging");
      };
      handle.addEventListener("mousedown", (ev) => {
        if (ev.target.closest("[data-close-window]")) return;
        startX = ev.clientX; startY = ev.clientY;
        origX = win.offsetLeft; origY = win.offsetTop;
        win.classList.add("dragging");
        document.addEventListener("mousemove", onMove);
        document.addEventListener("mouseup", onUp);
        ev.preventDefault();
      });
    }

    _treeCell(person, opts = {}) {
      if (!person) return `<div class="ft-cell ft-cell-empty"><span class="ft-disc"></span><span class="ft-plaque">unknown</span></div>`;
      const sizeOpt = opts.size !== undefined ? opts.size : "small";
      return `<div class="ft-cell">
        ${this.portraitMedallion(person, { size: sizeOpt, noDrop: opts.noDrop })}
        <span class="ft-plaque" title="${esc(this.characterTooltip(person))}">${esc(person.name)}</span>
      </div>`;
    }

    _parentsOf(cid) {
      const fam = this.sim.closeFamilyOf ? this.sim.closeFamilyOf(cid) : null;
      return (fam && fam.parents) || [];
    }

    /* ancestry node: person + bracket of their parents, recursive */
    _ancestryNode(person, depth, opts = {}) {
      if (!person) return "";
      const parents = depth > 0 ? this._parentsOf(person.id).slice(0, 2) : [];
      return `<div class="ft-node">
        ${this._treeCell(person, opts.root ? { size: "", noDrop: true } : {})}
        ${parents.length ? `<div class="ft-parents">${parents.map((p) => this._ancestryNode(p, depth - 1)).join("")}</div>` : ""}
      </div>`;
    }

    openFamilyTree(cid) {
      const c = this.sim.character(cid);
      if (!c) return;
      this._viewDynastyId = (c.family && c.family.dynastyId) || null;
      const closeFamily = this.sim.closeFamilyOf ? this.sim.closeFamilyOf(cid) : { parents: [], children: [] };
      const children = (closeFamily.children || []).slice(0, 12);
      const html = `
        <div class="ft-columns-head">
          <span>Children</span><span class="ft-head-center">Family Tree</span><span>Parents · Grandparents · Great&nbsp;Grandparents</span>
        </div>
        <div class="ft-tree">
          <div class="ft-children">
            ${children.length ? children.map((k) => this._treeCell(k)).join("") : `<div class="ck-empty">No children</div>`}
          </div>
          <div class="ft-root">
            ${this._ancestryNode(c, 3, { root: true })}
          </div>
        </div>`;
      this.openFloatWindow(`ftree:${cid}`, `${c.name} — Family Tree`, html);
      this._viewDynastyId = null;
    }

    /* descendant node: person + row of their dynastic children beneath */
    _descendantNode(person, dynastyId, depth, seen) {
      if (!person || seen.has(person.id)) return "";
      seen.add(person.id);
      const fam = this.sim.closeFamilyOf ? this.sim.closeFamilyOf(person.id) : null;
      const kids = depth > 0
        ? ((fam && fam.children) || []).filter((k) => k.family && k.family.dynastyId === dynastyId).slice(0, 8)
        : [];
      return `<div class="dt-node">
        ${this._treeCell(person)}
        ${kids.length ? `<div class="dt-kids">${kids.map((k) => this._descendantNode(k, dynastyId, depth - 1, seen)).join("")}</div>` : ""}
      </div>`;
    }

    openDynastyTree(dynastyId) {
      const dynasty = this.sim.dynasty ? this.sim.dynasty(dynastyId) : null;
      if (!dynasty) return;
      this._viewDynastyId = dynastyId;
      const members = Array.isArray(dynasty.members) ? dynasty.members : [];
      const living = members.map((id) => this.sim.character(id)).filter((m) => m && m.alive).length;
      const founder = dynasty.founder ? this.sim.character(dynasty.founder) : null;
      const root = founder || (dynasty.head ? this.sim.character(dynasty.head) : null);
      const html = `
        <div class="dt-header">
          <span class="dt-arms">${WG.dynastyShield ? WG.dynastyShield(dynasty, 46) : ""}</span>
          <div class="dt-header-stats">
            <div><span>Total Members:</span><b>${members.length}</b></div>
            <div><span>Living Members:</span><b>${living}</b></div>
            <div><span>Renown:</span><b>${Math.round(dynasty.renown || 0)}</b></div>
          </div>
        </div>
        <div class="dt-tree">
          ${root ? this._descendantNode(root, dynastyId, 3, new Set()) : `<div class="ck-empty">No recorded founder</div>`}
        </div>`;
      this.openFloatWindow(`dtree:${dynastyId}`, `Dynasty ${dynasty.name}`, html);
      this._viewDynastyId = null;
    }
  }

  window.WG.uiMixin(UITreeWindows);
})();

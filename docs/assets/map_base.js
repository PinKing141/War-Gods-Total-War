/* Shared canvas map infrastructure.
   This file owns camera, input, and selection state only. Renderers provide
   their own province picking and drawing data. */
(function () {
  "use strict";

  function fallbackNoise() {
    return {
      fbm(x, y) {
        const s = Math.sin(x * 127.1 + y * 311.7) * 43758.5453123;
        return s - Math.floor(s);
      },
    };
  }

  class MapBase {
    constructor(canvas, seed) {
      this.canvas = canvas;
      this.ctx = canvas.getContext("2d");
      this.seed = seed;
      this.W = seed.world.width;
      this.H = seed.world.height;
      this.noise = WG.makeNoise ? WG.makeNoise(1337) : fallbackNoise();
      this.provinces = seed.provinces || [];
      this.adjacency = {};
      this.view = { x: this.W / 2, y: this.H / 2, zoom: 0.9 };
      this.mapMode = "political";
      this.selected = null;
      this.selectedRealm = null;
      this.selectedRealmProvinceIds = [];
      this.hovered = null;
      this._image = null;
      this._dirty = true;
    }

    markDirty() {
      this._dirty = true;
    }

    _hex(hex) {
      return [
        parseInt(hex.slice(1, 3), 16),
        parseInt(hex.slice(3, 5), 16),
        parseInt(hex.slice(5, 7), 16),
      ];
    }

    setMode(mode) {
      this.mapMode = mode;
      this.markDirty();
    }

    worldToScreen(wx, wy) {
      const { width, height } = this.canvas;
      const z = this.view.zoom * (width / this.W);
      return {
        x: (wx - this.view.x) * z + width / 2,
        y: (wy - this.view.y) * z + height / 2,
        z,
      };
    }

    screenToWorld(sx, sy) {
      const { width, height } = this.canvas;
      const z = this.view.zoom * (width / this.W);
      return {
        x: (sx - width / 2) / z + this.view.x,
        y: (sy - height / 2) / z + this.view.y,
      };
    }

    province(id) {
      return this.provinces.find((p) => p.id === id) || null;
    }

    provinceAt() {
      return null;
    }

    provinceState(province, sim) {
      const id = typeof province === "string" ? province : province && province.id;
      const p = typeof province === "string" ? this.province(id) : province;
      if (sim && id && sim.provinceState[id]) return sim.provinceState[id];
      return { controller: p ? p.controller : null, occupier: null };
    }

    controlledProvinces(fid, sim) {
      if (!fid) return [];
      return this.provinces.filter((p) => {
        const st = this.provinceState(p, sim);
        return st.controller === fid || st.occupier === fid;
      });
    }

    _ensureAdj(a, b) {
      if (!this.adjacency[a] || !this.adjacency[b]) return;
      if (!this.adjacency[a].includes(b)) this.adjacency[a].push(b);
      if (!this.adjacency[b].includes(a)) this.adjacency[b].push(a);
    }

    selectProvince(id) {
      this.selected = id;
      this.selectedRealm = null;
      this.selectedRealmProvinceIds = [];
      this.markDirty();
    }

    selectRealm(fid, sim) {
      this.selected = null;
      this.selectedRealm = fid;
      this.selectedRealmProvinceIds = this.controlledProvinces(fid, sim).map((p) => p.id);
      this.markDirty();
    }

    clearSelection() {
      this.selected = null;
      this.selectedRealm = null;
      this.selectedRealmProvinceIds = [];
      this.hovered = null;
      this.markDirty();
    }

    attach(container, { onHover, onClick, onViewChange }) {
      let dragging = false;
      let moved = false;
      let lastX = 0;
      let lastY = 0;

      const toWorld = (ev) => {
        const rect = this.canvas.getBoundingClientRect();
        const dpr = window.devicePixelRatio || 1;
        const sx = (ev.clientX - rect.left) * dpr;
        const sy = (ev.clientY - rect.top) * dpr;
        return this.screenToWorld(sx, sy);
      };

      container.addEventListener("mousedown", (ev) => {
        dragging = true;
        moved = false;
        lastX = ev.clientX;
        lastY = ev.clientY;
      });

      window.addEventListener("mouseup", () => {
        dragging = false;
      });

      container.addEventListener("mousemove", (ev) => {
        if (dragging) {
          const dpr = window.devicePixelRatio || 1;
          const z = this.view.zoom * (this.canvas.width / this.W);
          const dx = (ev.clientX - lastX) * dpr;
          const dy = (ev.clientY - lastY) * dpr;
          if (Math.abs(ev.clientX - lastX) + Math.abs(ev.clientY - lastY) > 2) moved = true;
          this.view.x -= dx / z;
          this.view.y -= dy / z;
          this._clampView();
          lastX = ev.clientX;
          lastY = ev.clientY;
          onViewChange && onViewChange();
        }

        const w = toWorld(ev);
        const prov = this.provinceAt(w.x, w.y);
        this.hovered = prov ? prov.id : null;
        onHover && onHover(prov, ev, w);
      });

      container.addEventListener("mouseleave", () => {
        this.hovered = null;
        onHover && onHover(null);
      });

      container.addEventListener("click", (ev) => {
        if (moved) return;
        const w = toWorld(ev);
        onClick && onClick(this.provinceAt(w.x, w.y), ev);
      });

      container.addEventListener("wheel", (ev) => {
        ev.preventDefault();
        const factor = ev.deltaY < 0 ? 1.15 : 1 / 1.15;
        this.view.zoom = Math.min(5, Math.max(0.55, this.view.zoom * factor));
        this._clampView();
        onViewChange && onViewChange();
      }, { passive: false });
    }

    _clampView() {
      const margin = 120;
      this.view.x = Math.min(this.W + margin, Math.max(-margin, this.view.x));
      this.view.y = Math.min(this.H + margin, Math.max(-margin, this.view.y));
    }

    resize() {
      const dpr = window.devicePixelRatio || 1;
      const rect = this.canvas.parentElement.getBoundingClientRect();
      this.canvas.width = Math.floor(rect.width * dpr);
      this.canvas.height = Math.floor(rect.height * dpr);
      this.canvas.style.width = rect.width + "px";
      this.canvas.style.height = rect.height + "px";
    }

    render() {
      const ctx = this.ctx;
      ctx.save();
      ctx.fillStyle = "#1f2d36";
      ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
      ctx.fillStyle = "rgba(246, 233, 198, 0.82)";
      ctx.font = "600 16px Georgia, serif";
      ctx.textAlign = "center";
      ctx.fillText("Loading map layers...", this.canvas.width / 2, this.canvas.height / 2);
      ctx.restore();
    }
  }

  window.WG = window.WG || {};
  window.WG.MapBase = MapBase;
})();

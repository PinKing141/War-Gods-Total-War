/* Painted political map on <canvas>.
   Ownership of every grid cell is precomputed once (warped nearest-province,
   so borders look organic); repainting by controller is a palette lookup, so
   the map recolors cheaply as provinces change hands during the sim. */
(function () {
  "use strict";

  const GRID_W = 640, GRID_H = 400;      // simulation-space raster
  const SEA = -1;

  class WorldMap {
    constructor(canvas, seed) {
      this.canvas = canvas;
      this.ctx = canvas.getContext("2d");
      this.seed = seed;
      this.W = seed.world.width;
      this.H = seed.world.height;
      this.noise = WG.makeNoise(1337);
      this.provinces = seed.provinces;
      this.cellOwner = new Int16Array(GRID_W * GRID_H).fill(SEA);
      this.adjacency = {};
      this.view = { x: this.W / 2, y: this.H / 2, zoom: 0.9 };
      this._image = null;          // offscreen canvas with the painted map
      this._dirty = true;
      this._computeOwnership();
      this._computeAdjacency();
    }

    /* ---------------- geometry ---------------- */

    _warp(x, y) {
      // Domain-warp so borders and coasts wobble organically.
      const n = this.noise;
      const s = 0.004;
      return {
        x: x + (n.fbm(x * s, y * s, 4) - 0.5) * 220,
        y: y + (n.fbm(x * s + 41.7, y * s + 12.3, 4) - 0.5) * 220,
      };
    }

    _landField(x, y) {
      // >0 means land. Union of soft blobs around provinces + coast noise.
      let best = -1e9;
      for (const p of this.provinces) {
        const dx = x - p.x, dy = y - p.y;
        const d = Math.sqrt(dx * dx + dy * dy);
        const radius = 210 + p.value * 0.9;
        best = Math.max(best, radius - d);
      }
      const coast = (this.noise.fbm(x * 0.006 + 7.7, y * 0.006 + 3.1, 4) - 0.5) * 130;
      return best + coast;
    }

    _computeOwnership() {
      const sx = this.W / GRID_W, sy = this.H / GRID_H;
      for (let gy = 0; gy < GRID_H; gy++) {
        for (let gx = 0; gx < GRID_W; gx++) {
          const wx = (gx + 0.5) * sx, wy = (gy + 0.5) * sy;
          const w = this._warp(wx, wy);
          if (this._landField(w.x, w.y) <= 0) continue;   // sea
          let bestIdx = 0, bestDist = Infinity;
          for (let i = 0; i < this.provinces.length; i++) {
            const p = this.provinces[i];
            const dx = w.x - p.x, dy = w.y - p.y;
            const d = dx * dx + dy * dy;
            if (d < bestDist) { bestDist = d; bestIdx = i; }
          }
          this.cellOwner[gy * GRID_W + gx] = bestIdx;
        }
      }
    }

    _computeAdjacency() {
      const adj = {};
      this.provinces.forEach((p) => { adj[p.id] = new Set(); });
      for (let gy = 0; gy < GRID_H; gy++) {
        for (let gx = 0; gx < GRID_W - 1; gx++) {
          const a = this.cellOwner[gy * GRID_W + gx];
          const b = this.cellOwner[gy * GRID_W + gx + 1];
          const c = gy + 1 < GRID_H ? this.cellOwner[(gy + 1) * GRID_W + gx] : a;
          if (a >= 0 && b >= 0 && a !== b) {
            adj[this.provinces[a].id].add(this.provinces[b].id);
            adj[this.provinces[b].id].add(this.provinces[a].id);
          }
          if (a >= 0 && c >= 0 && a !== c) {
            adj[this.provinces[a].id].add(this.provinces[c].id);
            adj[this.provinces[c].id].add(this.provinces[a].id);
          }
        }
      }
      for (const key of Object.keys(adj)) this.adjacency[key] = [...adj[key]];
      // Steppe riders reach the frontier even across thin gaps: ensure the
      // White Mare camp connects to Open Gate and the sacred field.
      this._ensureAdj("PROV_WHITE_MARE", "PROV_OPEN_GATE");
      this._ensureAdj("PROV_WHITE_MARE", "PROV_NINTH_BANNER");
    }

    _ensureAdj(a, b) {
      if (!this.adjacency[a] || !this.adjacency[b]) return;
      if (!this.adjacency[a].includes(b)) this.adjacency[a].push(b);
      if (!this.adjacency[b].includes(a)) this.adjacency[b].push(a);
    }

    provinceAt(worldX, worldY) {
      const gx = Math.floor(worldX / this.W * GRID_W);
      const gy = Math.floor(worldY / this.H * GRID_H);
      if (gx < 0 || gy < 0 || gx >= GRID_W || gy >= GRID_H) return null;
      const idx = this.cellOwner[gy * GRID_W + gx];
      return idx >= 0 ? this.provinces[idx] : null;
    }

    /* ---------------- painting ---------------- */

    markDirty() { this._dirty = true; }

    _hex(hex) {
      return [parseInt(hex.slice(1, 3), 16), parseInt(hex.slice(3, 5), 16),
              parseInt(hex.slice(5, 7), 16)];
    }

    _paintWorld(sim) {
      // Paint into an offscreen canvas at grid resolution, then scale up with
      // smoothing — cheap and gives soft painted edges.
      if (!this._image) {
        this._image = document.createElement("canvas");
        this._image.width = GRID_W; this._image.height = GRID_H;
      }
      const ictx = this._image.getContext("2d");
      const img = ictx.createImageData(GRID_W, GRID_H);
      const data = img.data;

      const seaDeep = this._hex("#2c4257"), seaShallow = this._hex("#3d5c74");
      const factionRGB = {};
      for (const f of this.seed.factions) factionRGB[f.id] = this._hex(f.color);
      const terrainRGB = {};
      for (const [key, t] of Object.entries(this.seed.terrains)) terrainRGB[key] = this._hex(t.base);

      for (let gy = 0; gy < GRID_H; gy++) {
        for (let gx = 0; gx < GRID_W; gx++) {
          const i = gy * GRID_W + gx;
          const o = this.cellOwner[i];
          const off = i * 4;
          const wx = gx / GRID_W * this.W, wy = gy / GRID_H * this.H;
          const tex = this.noise.fbm(wx * 0.02, wy * 0.02, 3) - 0.5; // paper grain
          if (o === SEA) {
            // near-coast shading
            let coastal = false;
            for (let d = 0; d < 4 && !coastal; d++) {
              const nx = gx + [1, -1, 0, 0][d], ny = gy + [0, 0, 1, -1][d];
              if (nx >= 0 && ny >= 0 && nx < GRID_W && ny < GRID_H &&
                  this.cellOwner[ny * GRID_W + nx] !== SEA) coastal = true;
            }
            const base = coastal ? seaShallow : seaDeep;
            const wave = tex * 18;
            data[off] = base[0] + wave; data[off + 1] = base[1] + wave;
            data[off + 2] = base[2] + wave; data[off + 3] = 255;
            continue;
          }
          const prov = this.provinces[o];
          const state = sim ? sim.provinceState[prov.id] : null;
          const controller = state ? state.controller : prov.controller;
          const terr = terrainRGB[prov.terrain] || [170, 160, 120];
          const fac = factionRGB[controller] || [120, 120, 120];

          // political tint over terrain, CK3-style
          let mix = 0.64;
          // occupied provinces show the occupier in a hatch pattern
          let rgb = [
            terr[0] * (1 - mix) + fac[0] * mix,
            terr[1] * (1 - mix) + fac[1] * mix,
            terr[2] * (1 - mix) + fac[2] * mix,
          ];
          if (state && state.occupier && state.occupier !== controller) {
            const occ = factionRGB[state.occupier] || [200, 200, 200];
            const stripe = ((gx + gy) % 6) < 3;
            if (stripe) rgb = [
              terr[0] * 0.35 + occ[0] * 0.65,
              terr[1] * 0.35 + occ[1] * 0.65,
              terr[2] * 0.35 + occ[2] * 0.65,
            ];
          }
          // border darkening: any 4-neighbour owned by another *controller*
          let border = false, realmBorder = false;
          for (let d = 0; d < 4; d++) {
            const nx = gx + [1, -1, 0, 0][d], ny = gy + [0, 0, 1, -1][d];
            if (nx < 0 || ny < 0 || nx >= GRID_W || ny >= GRID_H) continue;
            const n = this.cellOwner[ny * GRID_W + nx];
            if (n === SEA) { border = true; continue; }
            if (n !== o) {
              border = true;
              const np = this.provinces[n];
              const nState = sim ? sim.provinceState[np.id] : null;
              const nCtrl = nState ? nState.controller : np.controller;
              if (nCtrl !== controller) realmBorder = true;
            }
          }
          const shade = 1.14 + tex * 0.16;
          let r = rgb[0] * shade, g = rgb[1] * shade, b = rgb[2] * shade;
          if (realmBorder) { r *= 0.40; g *= 0.40; b *= 0.40; }
          else if (border) { r *= 0.72; g *= 0.72; b *= 0.72; }
          data[off] = r; data[off + 1] = g; data[off + 2] = b; data[off + 3] = 255;
        }
      }
      ictx.putImageData(img, 0, 0);
      this._dirty = false;
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
      const { width } = this.canvas;
      const z = this.view.zoom * (width / this.W);
      return {
        x: (sx - this.canvas.width / 2 / (window.devicePixelRatio || 1)) *
           (window.devicePixelRatio || 1) / z + this.view.x,
        y: (sy - this.canvas.height / 2 / (window.devicePixelRatio || 1)) *
           (window.devicePixelRatio || 1) / z + this.view.y,
      };
    }

    render(sim) {
      if (this._dirty) this._paintWorld(sim);
      const ctx = this.ctx;
      const { width, height } = this.canvas;
      ctx.save();
      ctx.fillStyle = "#22303d";
      ctx.fillRect(0, 0, width, height);

      const tl = this.worldToScreen(0, 0);
      const z = tl.z;
      ctx.imageSmoothingEnabled = true;
      ctx.imageSmoothingQuality = "high";
      ctx.drawImage(this._image, tl.x, tl.y, this.W * z, this.H * z);

      // rivers
      ctx.lineCap = "round"; ctx.lineJoin = "round";
      for (const river of this.seed.rivers) {
        ctx.beginPath();
        river.forEach(([rx, ry], i) => {
          const pt = this.worldToScreen(rx, ry);
          if (i === 0) ctx.moveTo(pt.x, pt.y); else ctx.lineTo(pt.x, pt.y);
        });
        ctx.strokeStyle = "rgba(66, 104, 134, 0.85)";
        ctx.lineWidth = Math.max(1.5, 3.4 * z);
        ctx.stroke();
      }

      // province labels
      ctx.textAlign = "center";
      for (const p of this.provinces) {
        const pt = this.worldToScreen(p.x, p.y);
        const size = Math.max(9, 13 * z);
        ctx.font = `600 ${size}px 'Iowan Old Style', 'Palatino Linotype', Georgia, serif`;
        ctx.fillStyle = "rgba(20, 16, 8, 0.85)";
        ctx.strokeStyle = "rgba(244, 232, 200, 0.65)";
        ctx.lineWidth = 3;
        const label = p.name.toUpperCase();
        ctx.save();
        ctx.letterSpacing = `${1.5 * z}px`;
        ctx.strokeText(label, pt.x, pt.y + 26 * z);
        ctx.fillText(label, pt.x, pt.y + 26 * z);
        ctx.restore();
      }
      ctx.restore();
    }

    /* ---------------- interaction ---------------- */

    attach(container, { onHover, onClick, onViewChange }) {
      let dragging = false, moved = false, lastX = 0, lastY = 0;
      const dpr = window.devicePixelRatio || 1;

      const toWorld = (ev) => {
        const rect = this.canvas.getBoundingClientRect();
        const sx = (ev.clientX - rect.left) * dpr;
        const sy = (ev.clientY - rect.top) * dpr;
        const z = this.view.zoom * (this.canvas.width / this.W);
        return {
          x: (sx - this.canvas.width / 2) / z + this.view.x,
          y: (sy - this.canvas.height / 2) / z + this.view.y,
        };
      };

      container.addEventListener("mousedown", (ev) => {
        dragging = true; moved = false;
        lastX = ev.clientX; lastY = ev.clientY;
      });
      window.addEventListener("mouseup", () => { dragging = false; });
      container.addEventListener("mousemove", (ev) => {
        if (dragging) {
          const z = this.view.zoom * (this.canvas.width / this.W);
          const dx = (ev.clientX - lastX) * dpr, dy = (ev.clientY - lastY) * dpr;
          if (Math.abs(ev.clientX - lastX) + Math.abs(ev.clientY - lastY) > 2) moved = true;
          this.view.x -= dx / z; this.view.y -= dy / z;
          this._clampView();
          lastX = ev.clientX; lastY = ev.clientY;
          onViewChange && onViewChange();
        }
        const w = toWorld(ev);
        onHover && onHover(this.provinceAt(w.x, w.y), ev, w);
      });
      container.addEventListener("mouseleave", () => onHover && onHover(null));
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
  }

  window.WG = window.WG || {};
  window.WG.WorldMap = WorldMap;
})();

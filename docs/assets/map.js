/* Painted political map on <canvas>.
   Ownership of every grid cell is precomputed once (warped nearest-province,
   so borders look organic); repainting by controller is a palette lookup, so
   the map recolors cheaply as provinces change hands during the sim. */
(function () {
  "use strict";

  const GRID_W = 880, GRID_H = 550;      // simulation-space raster
  const SEA = -1;

  const TERRAIN_GLYPHS = {
    mountain_pass: "▲", bog_forest: "♣", canal_farmland: "≈",
    river_city: "⌂", charter_city: "⌂", river_port: "⌂",
    sacred_battlefield: "✦",
  };

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
      this.coastDistance = new Uint16Array(GRID_W * GRID_H);
      this.adjacency = {};
      this.view = { x: this.W / 2, y: this.H / 2, zoom: 0.9 };
      this.mapMode = "political";  // political | culture | religion | terrain | devastation
      this.selected = null;        // province id to outline
      this.riverPaths = seed.riverPaths || [];
      this._image = null;          // offscreen canvas with the painted map
      this._dirty = true;
      this._computeOwnership();
      this._computeCoastDistance();
      this._computeAdjacency();
      this._computeDecorations();
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

    _computeCoastDistance() {
      // Multi-source distance field from the land/sea edge.  The renderer uses
      // it for continental shelves and coastal foam instead of a one-cell
      // neighbour check, so the ocean reads as a gradual bathymetry layer.
      const max = 65535;
      this.coastDistance.fill(max);
      const queue = new Int32Array(GRID_W * GRID_H);
      let head = 0, tail = 0;
      for (let gy = 0; gy < GRID_H; gy++) {
        for (let gx = 0; gx < GRID_W; gx++) {
          const i = gy * GRID_W + gx;
          const o = this.cellOwner[i];
          for (let d = 0; d < 4; d++) {
            const nx = gx + [1, -1, 0, 0][d], ny = gy + [0, 0, 1, -1][d];
            if (nx < 0 || ny < 0 || nx >= GRID_W || ny >= GRID_H) continue;
            const n = this.cellOwner[ny * GRID_W + nx];
            if ((o === SEA && n !== SEA) || (o !== SEA && n === SEA)) {
              this.coastDistance[i] = 0;
              queue[tail++] = i;
              break;
            }
          }
        }
      }
      while (head < tail) {
        const i = queue[head++];
        const gx = i % GRID_W, gy = Math.floor(i / GRID_W);
        const next = this.coastDistance[i] + 1;
        for (let d = 0; d < 4; d++) {
          const nx = gx + [1, -1, 0, 0][d], ny = gy + [0, 0, 1, -1][d];
          if (nx < 0 || ny < 0 || nx >= GRID_W || ny >= GRID_H) continue;
          const ni = ny * GRID_W + nx;
          if (next < this.coastDistance[ni]) {
            this.coastDistance[ni] = next;
            queue[tail++] = ni;
          }
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

    _computeDecorations() {
      // Border segments per province (for the selected-province outline) and
      // scattered glyph anchor points per province (for terrain doodads).
      const sx = this.W / GRID_W, sy = this.H / GRID_H;
      this.borderSegs = {};
      this.glyphPoints = {};
      const glyphCandidates = {};
      this.provinces.forEach((p) => { this.borderSegs[p.id] = []; this.glyphPoints[p.id] = []; });
      this.provinces.forEach((p) => { glyphCandidates[p.id] = []; });

      for (let gy = 0; gy < GRID_H; gy++) {
        for (let gx = 0; gx < GRID_W; gx++) {
          const o = this.cellOwner[gy * GRID_W + gx];
          if (o < 0) continue;
          const id = this.provinces[o].id;
          const right = gx + 1 < GRID_W ? this.cellOwner[gy * GRID_W + gx + 1] : SEA;
          const down = gy + 1 < GRID_H ? this.cellOwner[(gy + 1) * GRID_W + gx] : SEA;
          if (right !== o) {
            this.borderSegs[id].push([(gx + 1) * sx, gy * sy, (gx + 1) * sx, (gy + 1) * sy]);
            if (right >= 0) this.borderSegs[this.provinces[right].id].push([(gx + 1) * sx, gy * sy, (gx + 1) * sx, (gy + 1) * sy]);
          }
          if (down !== o) {
            this.borderSegs[id].push([gx * sx, (gy + 1) * sy, (gx + 1) * sx, (gy + 1) * sy]);
            if (down >= 0) this.borderSegs[this.provinces[down].id].push([gx * sx, (gy + 1) * sy, (gx + 1) * sx, (gy + 1) * sy]);
          }
          // Organic glyph candidates: jittered, deterministic samples rather
          // than a visible modulo grid.  A small Poisson-style filter below
          // keeps the chosen marks from clumping too tightly.
          if (gx % 10 === 5 && gy % 10 === 5 && this.coastDistance[gy * GRID_W + gx] > 2) {
            const wx = gx * sx, wy = gy * sy;
            const prov = this.provinces[o];
            if (Math.abs(wy - prov.y) > 46 || Math.abs(wx - prov.x) > 120) {
              const h = this._hash2(gx + o * 97, gy - o * 131);
              if (h > 0.78) {
                const jx = (this._hash2(gx, gy) - 0.5) * 34 * sx;
                const jy = (this._hash2(gx + 19, gy - 23) - 0.5) * 30 * sy;
                glyphCandidates[id].push([wx + jx, wy + jy, h]);
              }
            }
          }
        }
      }
      for (const p of this.provinces) {
        const minDist = p.terrain === "mountain_pass" ? 70 : 58;
        for (const cand of glyphCandidates[p.id].sort((a, b) => b[2] - a[2])) {
          if (this.glyphPoints[p.id].every(([x, y]) => {
            const dx = x - cand[0], dy = y - cand[1];
            return dx * dx + dy * dy >= minDist * minDist;
          })) this.glyphPoints[p.id].push([cand[0], cand[1], cand[2]]);
        }
      }
    }

    _hash2(x, y) {
      const s = Math.sin(x * 127.1 + y * 311.7) * 43758.5453123;
      return s - Math.floor(s);
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

      const seaDeep = this._hex("#27384b"), seaMid = this._hex("#314d66"),
            seaShallow = this._hex("#547f91"), foamRGB = this._hex("#9fc2c1");
      const factionRGB = {}, cultureRGB = {}, religionRGB = {};
      for (const f of this.seed.factions) {
        factionRGB[f.id] = this._hex(f.color);
        cultureRGB[f.id] = this._hex(this.seed.cultureColors[f.culture] || "#888070");
        religionRGB[f.id] = this._hex(this.seed.religionColors[f.religion] || "#888070");
      }
      const ruinRGB = this._hex("#8c2f22");
      const terrainRGB = {};
      for (const [key, t] of Object.entries(this.seed.terrains)) terrainRGB[key] = this._hex(t.base);
      const mode = this.mapMode;

      for (let gy = 0; gy < GRID_H; gy++) {
        for (let gx = 0; gx < GRID_W; gx++) {
          const i = gy * GRID_W + gx;
          const o = this.cellOwner[i];
          const off = i * 4;
          const wx = gx / GRID_W * this.W, wy = gy / GRID_H * this.H;
          const tex = this.noise.fbm(wx * 0.02, wy * 0.02, 3) - 0.5; // paper grain
          if (o === SEA) {
            const dist = Math.min(1, this.coastDistance[i] / 18);
            const shelf = Math.max(0, 1 - dist);
            const band = (Math.sin(this.coastDistance[i] * 0.9 + tex * 5) + 1) * 0.5;
            const midMix = Math.max(0, 1 - Math.abs(dist - 0.45) * 2.2);
            let base = [
              seaDeep[0] * dist + seaShallow[0] * shelf,
              seaDeep[1] * dist + seaShallow[1] * shelf,
              seaDeep[2] * dist + seaShallow[2] * shelf,
            ];
            base = [
              base[0] * (1 - midMix * 0.35) + seaMid[0] * midMix * 0.35,
              base[1] * (1 - midMix * 0.35) + seaMid[1] * midMix * 0.35,
              base[2] * (1 - midMix * 0.35) + seaMid[2] * midMix * 0.35,
            ];
            if (this.coastDistance[i] <= 2 && band > 0.42) {
              base = [
                base[0] * 0.62 + foamRGB[0] * 0.38,
                base[1] * 0.62 + foamRGB[1] * 0.38,
                base[2] * 0.62 + foamRGB[2] * 0.38,
              ];
            }
            const wave = tex * 16 + band * shelf * 10;
            data[off] = base[0] + wave; data[off + 1] = base[1] + wave;
            data[off + 2] = base[2] + wave; data[off + 3] = 255;
            continue;
          }
          const prov = this.provinces[o];
          const state = sim ? sim.provinceState[prov.id] : null;
          const controller = state ? state.controller : prov.controller;
          const terr = terrainRGB[prov.terrain] || [170, 160, 120];

          // choose the tint layer for the active map mode
          let tint = factionRGB[controller] || [120, 120, 120];
          let mix = 0.64;
          if (mode === "culture") tint = cultureRGB[controller] || tint;
          else if (mode === "religion") tint = religionRGB[controller] || tint;
          else if (mode === "terrain") mix = 0;
          else if (mode === "devastation") {
            const d = state ? Math.min(1, state.devastation / 80) : 0;
            tint = ruinRGB; mix = 0.15 + d * 0.65;
          }
          let rgb = [
            terr[0] * (1 - mix) + tint[0] * mix,
            terr[1] * (1 - mix) + tint[1] * mix,
            terr[2] * (1 - mix) + tint[2] * mix,
          ];
          // occupied provinces show the occupier in a hatch pattern
          if (mode === "political" && state && state.occupier && state.occupier !== controller) {
            const occ = factionRGB[state.occupier] || [200, 200, 200];
            const stripe = ((gx + gy) % 8) < 4;
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
      for (const river of this.riverPaths) {
        ctx.beginPath();
        river.forEach(([rx, ry], i) => {
          const pt = this.worldToScreen(rx, ry);
          if (i === 0) ctx.moveTo(pt.x, pt.y); else ctx.lineTo(pt.x, pt.y);
        });
        ctx.strokeStyle = "rgba(66, 104, 134, 0.85)";
        ctx.lineWidth = Math.max(1.5, 3.4 * z);
        ctx.stroke();
      }

      // terrain glyph doodads (subtle painted-map furniture)
      ctx.textAlign = "center";
      const glyphSize = Math.max(8, 12 * z);
      ctx.font = `${glyphSize}px Georgia, serif`;
      ctx.fillStyle = "rgba(24, 20, 10, 0.28)";
      for (const p of this.provinces) {
        const glyph = TERRAIN_GLYPHS[p.terrain];
        if (!glyph) continue;
        for (const [gx, gy] of this.glyphPoints[p.id]) {
          const pt = this.worldToScreen(gx, gy);
          ctx.fillText(glyph, pt.x, pt.y);
        }
      }

      // selected province outline
      if (this.selected && this.borderSegs[this.selected]) {
        ctx.strokeStyle = "rgba(238, 214, 140, 0.95)";
        ctx.lineWidth = Math.max(1.5, 2.6 * z);
        ctx.beginPath();
        for (const [x1, y1, x2, y2] of this.borderSegs[this.selected]) {
          const a = this.worldToScreen(x1, y1), b = this.worldToScreen(x2, y2);
          ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y);
        }
        ctx.stroke();
      }

      // province labels
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

      // realm names painted across their territory (political mode only)
      if (this.mapMode === "political" && sim) {
        for (const f of this.seed.factions) {
          const owned = this.seed.provinces.filter(
            (p) => sim.provinceState[p.id].controller === f.id);
          if (!owned.length) continue;
          let cx = 0, cy = 0;
          for (const p of owned) { cx += p.x; cy += p.y; }
          cx /= owned.length; cy /= owned.length;
          const pt = this.worldToScreen(cx, cy);
          const size = Math.max(13, (17 + Math.sqrt(owned.length) * 9) * z);
          const yOff = owned.length === 1 ? -34 * z : -6 * z;
          ctx.font = `700 italic ${size}px 'Iowan Old Style', 'Palatino Linotype', Georgia, serif`;
          ctx.save();
          ctx.letterSpacing = `${4 * z}px`;
          ctx.globalAlpha = 0.62;
          ctx.strokeStyle = "rgba(12, 9, 4, 0.9)";
          ctx.lineWidth = Math.max(2, 3.4 * z);
          ctx.fillStyle = "rgba(246, 233, 198, 0.95)";
          const name = f.shortName.toUpperCase();
          ctx.strokeText(name, pt.x, pt.y + yOff);
          ctx.fillText(name, pt.x, pt.y + yOff);
          ctx.restore();
        }
      }
      ctx.restore();
    }

    setMode(mode) {
      this.mapMode = mode;
      this.markDirty();
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

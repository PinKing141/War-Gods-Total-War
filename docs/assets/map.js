/* Parchment map renderer over the worldgen geometry.
   Three layers: a lit sepia terrain layer painted once (bathymetry, biome
   fills shaded by the heightmap, rivers, coast ink, glyph doodads, grain);
   a political layer of translucent realm tints + smoothed ink borders,
   rebuilt only when the sim's mapVersion changes; and a cheap per-frame
   pass for selection outline and calligraphic labels. */
(function () {
  "use strict";

  const LAYER_W = 2200;                 // offscreen layer resolution
  const INK = "#3b301c";

  function hex(h) {
    return [parseInt(h.slice(1, 3), 16), parseInt(h.slice(3, 5), 16), parseInt(h.slice(5, 7), 16)];
  }
  function css([r, g, b], a) {
    return `rgba(${Math.round(Math.max(0, Math.min(255, r)))},${Math.round(Math.max(0, Math.min(255, g)))},${Math.round(Math.max(0, Math.min(255, b)))},${a === undefined ? 1 : a})`;
  }
  function lerp3(a, b, t) {
    return [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t];
  }

  // muted parchment biome bases per lore terrain type
  const BIOME = {
    river_city: "#c6b88c", canal_farmland: "#b9bb84", bog_forest: "#9aa471",
    frontier_farms: "#bfba85", mountain_pass: "#b4a683", charter_city: "#c8b68e",
    river_port: "#bdb586", steppe_market: "#ccb47f", sacred_battlefield: "#c2ad85",
  };

  class WorldMap {
    constructor(canvas, seed, world) {
      this.canvas = canvas;
      this.ctx = canvas.getContext("2d");
      this.seed = seed;
      this.world = world;
      this.W = world.W;
      this.H = world.H;
      this.noise = WG.makeNoise(4242);
      this.provinces = seed.provinces;
      this.view = { x: this.W / 2, y: this.H / 2, zoom: 0.9 };
      this.mapMode = "political";   // political | culture | religion | terrain | devastation
      this.selected = null;
      this._terrain = null;
      this._political = null;
      this._dirty = true;
      this._lastSim = null;

      this.adjacency = world.adjacency;
      this._ensureAdj("PROV_WHITE_MARE", "PROV_OPEN_GATE");
      this._ensureAdj("PROV_WHITE_MARE", "PROV_NINTH_BANNER");

      this._k = LAYER_W / this.W;   // world -> layer scale
      this._provPaths = this._buildProvincePaths();
      this._outlinePaths = world.provOutlines.map((polys) => {
        const path = new Path2D();
        for (const poly of polys) {
          poly.forEach(([x, y], i) => (i ? path.lineTo(x, y) : path.moveTo(x, y)));
        }
        return path;
      });
    }

    _ensureAdj(a, b) {
      if (!this.adjacency[a] || !this.adjacency[b]) return;
      if (!this.adjacency[a].includes(b)) this.adjacency[a].push(b);
      if (!this.adjacency[b].includes(a)) this.adjacency[b].push(a);
    }

    _buildProvincePaths() {
      // Path2D per province in *world* coordinates (scaled at draw time).
      return this.provinces.map((p, pi) => {
        const path = new Path2D();
        for (const c of this.world.landCells) {
          if (c.prov !== pi || c.poly.length < 3) continue;
          c.poly.forEach(([x, y], i) => (i ? path.lineTo(x, y) : path.moveTo(x, y)));
          path.closePath();
        }
        return path;
      });
    }

    provinceAt(worldX, worldY) {
      if (worldX < 0 || worldY < 0 || worldX > this.W || worldY > this.H) return null;
      const cell = this.world.cellAt(worldX, worldY);
      if (!cell || !cell.land) return null;
      return this.provinces[cell.prov] || null;
    }

    markDirty() { this._dirty = true; }
    setMode(mode) { this.mapMode = mode; this.markDirty(); }

    /* ================= terrain layer (painted once) ================= */

    _buildTerrain() {
      const k = this._k;
      const layer = document.createElement("canvas");
      layer.width = LAYER_W;
      layer.height = Math.round(this.H * k);
      const ctx = layer.getContext("2d");
      ctx.scale(k, k);
      const world = this.world;

      // --- sea: parchment wash, deeper = duskier ---
      const seaNear = hex("#a7b5a3"), seaDeep = hex("#7f948e");
      ctx.fillStyle = css(seaDeep);
      ctx.fillRect(0, 0, this.W, this.H);
      for (const c of world.cells) {
        if (c.land || c.poly.length < 3) continue;
        const t = Math.min(1, (c.coastDist < 0 ? 12 : c.coastDist) / 9);
        const grain = (this.noise.fbm(c.x * 0.012, c.y * 0.012, 3) - 0.5) * 14;
        const col = lerp3(seaNear, seaDeep, t).map((v) => v + grain);
        ctx.fillStyle = css(col);
        this._fillPoly(ctx, c.poly, 1.6);
      }

      // --- coastal shelf halo (light bands hugging the land) ---
      ctx.lineJoin = "round"; ctx.lineCap = "round";
      for (const [width, alpha] of [[30, 0.10], [16, 0.14], [7, 0.20]]) {
        ctx.strokeStyle = `rgba(226,232,208,${alpha})`;
        ctx.lineWidth = width;
        for (const { path } of world.coastPaths) this._strokePoly(ctx, path);
      }

      // --- land cells: biome color, lit by the heightmap ---
      const light = [-0.62, -0.62, 0.48];
      for (const c of world.landCells) {
        if (c.poly.length < 3) continue;
        const p = this.provinces[c.prov];
        let col = hex(BIOME[p.terrain] || "#c0b487");
        const e = c.elev;
        if (e > 0.55) {
          // ramp toward bare rock and dark crags
          const t = Math.min(1, (e - 0.55) / 0.35);
          col = lerp3(col, hex("#7e7159"), t);
          if (e > 0.82) col = lerp3(col, hex("#5b5244"), (e - 0.82) / 0.18);
        } else {
          col = lerp3(hex("#c9bc90"), col, 0.35 + e);   // pale lowlands
        }
        // hillshade: gradient of the elevation field, lambertian, NW light
        const d = 9;
        const gx = (world.elevAt(c.x + d, c.y) - world.elevAt(c.x - d, c.y)) / (2 * d);
        const gy = (world.elevAt(c.x, c.y + d) - world.elevAt(c.x, c.y - d)) / (2 * d);
        const nz = 1 / Math.sqrt(gx * gx * 40000 + gy * gy * 40000 + 1);
        const shade = (-gx * 200 * light[0] - gy * 200 * light[1] + light[2]) * nz;
        const lit = 0.90 + Math.max(-0.5, Math.min(0.9, shade)) * 0.30;
        const grain = (this.noise.fbm(c.x * 0.02, c.y * 0.02, 3) - 0.5) * 0.05;
        col = col.map((v) => v * (lit + grain));
        ctx.fillStyle = css(col);
        this._fillPoly(ctx, c.poly, 1.6);
      }

      // --- rivers ---
      for (const river of world.riverPaths) {
        const w = Math.min(6.5, 1.6 + river.size * 0.45);
        ctx.strokeStyle = "rgba(93,120,116,0.9)";
        ctx.lineWidth = w;
        this._strokePoly(ctx, river.path);
        ctx.strokeStyle = "rgba(158,182,170,0.65)";
        ctx.lineWidth = Math.max(0.8, w * 0.4);
        this._strokePoly(ctx, river.path);
      }

      // --- coastline ink ---
      ctx.strokeStyle = "rgba(59,48,28,0.85)";
      ctx.lineWidth = 2.4;
      for (const { path } of world.coastPaths) this._strokePoly(ctx, path);

      // --- glyph doodads, Poisson-spaced ---
      this._drawGlyphs(ctx);

      // --- compass rose in open sea ---
      this._drawCompass(ctx);

      // --- paper grain + vignette over everything ---
      this._drawGrain(ctx);

      this._terrain = layer;
    }

    _fillPoly(ctx, poly, expand) {
      // tiny outward stroke hides hairline seams between cells
      ctx.beginPath();
      poly.forEach(([x, y], i) => (i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)));
      ctx.closePath();
      ctx.fill();
      if (expand) {
        ctx.lineWidth = expand;
        ctx.strokeStyle = ctx.fillStyle;
        ctx.stroke();
      }
    }

    _strokePoly(ctx, pts) {
      ctx.beginPath();
      pts.forEach(([x, y], i) => (i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)));
      ctx.stroke();
    }

    _drawGlyphs(ctx) {
      const world = this.world;
      const placed = [];
      const ok = (x, y, r) => placed.every(([px, py]) => (px - x) ** 2 + (py - y) ** 2 > r * r);
      const cells = [...world.landCells].sort((a, b) =>
        this._hash2(a.x, a.y) - this._hash2(b.x, b.y));
      ctx.textAlign = "center";
      for (const c of cells) {
        const p = this.provinces[c.prov];
        const h = this._hash2(c.x * 1.7, c.y * 2.3);
        if (c.elev > 0.64 && h < 0.75 && ok(c.x, c.y, 34)) {
          const s = 13 + c.elev * 14;
          ctx.font = `${s}px Georgia, serif`;
          ctx.fillStyle = "rgba(70,60,42,0.55)";
          ctx.fillText("▲", c.x, c.y + s * 0.35);
          placed.push([c.x, c.y]);
        } else if (p.terrain === "bog_forest" && c.elev < 0.55 && h < 0.4 && ok(c.x, c.y, 40)) {
          ctx.font = "13px Georgia, serif";
          ctx.fillStyle = "rgba(84,94,60,0.5)";
          ctx.fillText("♣", c.x, c.y + 4);
          placed.push([c.x, c.y]);
        } else if (p.terrain === "steppe_market" && h < 0.25 && ok(c.x, c.y, 46)) {
          ctx.font = "11px Georgia, serif";
          ctx.fillStyle = "rgba(112,98,62,0.4)";
          ctx.fillText("ᐦᐦ", c.x, c.y + 3);
          placed.push([c.x, c.y]);
        }
      }
      // one city mark on each urban province's anchor
      for (const p of this.provinces) {
        if (!["river_city", "charter_city", "river_port"].includes(p.terrain)) continue;
        ctx.font = "16px Georgia, serif";
        ctx.fillStyle = "rgba(60,50,32,0.7)";
        ctx.fillText("⌂", p.x, p.y - 8);
      }
    }

    _hash2(x, y) {
      const s = Math.sin(x * 127.1 + y * 311.7) * 43758.5453123;
      return s - Math.floor(s);
    }

    _drawCompass(ctx) {
      // put it in whichever corner is open water
      const world = this.world;
      const corners = [[130, this.H - 140], [this.W - 150, this.H - 140],
                       [130, 150], [this.W - 150, 150]];
      const spot = corners.find(([x, y]) => {
        const cell = world.cellAt(x, y);
        return cell && !cell.land && cell.coastDist >= 2;
      });
      if (!spot) return;
      const [cx, cy] = spot;
      ctx.save();
      ctx.translate(cx, cy);
      ctx.strokeStyle = "rgba(59,48,28,0.55)";
      ctx.fillStyle = "rgba(59,48,28,0.55)";
      ctx.lineWidth = 1.4;
      ctx.beginPath(); ctx.arc(0, 0, 46, 0, Math.PI * 2); ctx.stroke();
      ctx.beginPath(); ctx.arc(0, 0, 38, 0, Math.PI * 2); ctx.stroke();
      for (let i = 0; i < 8; i++) {
        const a = (i * Math.PI) / 4;
        const R = i % 2 === 0 ? 44 : 26;
        ctx.beginPath();
        ctx.moveTo(Math.cos(a) * R, Math.sin(a) * R);
        ctx.lineTo(Math.cos(a + 2.6) * 7, Math.sin(a + 2.6) * 7);
        ctx.lineTo(Math.cos(a - 2.6) * 7, Math.sin(a - 2.6) * 7);
        ctx.closePath();
        ctx.fill();
      }
      ctx.font = "italic 15px Georgia, serif";
      ctx.textAlign = "center";
      ctx.fillText("N", 0, -52);
      ctx.restore();
    }

    _drawGrain(ctx) {
      const g = document.createElement("canvas");
      g.width = 256; g.height = 160;
      const gctx = g.getContext("2d");
      const img = gctx.createImageData(256, 160);
      for (let y = 0; y < 160; y++) {
        for (let x = 0; x < 256; x++) {
          const v = 118 + (this.noise.fbm(x * 0.09 + 55, y * 0.09 + 91, 3) - 0.5) * 90;
          const off = (y * 256 + x) * 4;
          img.data[off] = v; img.data[off + 1] = v; img.data[off + 2] = v; img.data[off + 3] = 255;
        }
      }
      gctx.putImageData(img, 0, 0);
      ctx.save();
      ctx.globalAlpha = 0.30;
      ctx.globalCompositeOperation = "soft-light";
      ctx.drawImage(g, 0, 0, this.W, this.H);
      ctx.globalCompositeOperation = "source-over";
      // vignette
      const v = ctx.createRadialGradient(this.W / 2, this.H / 2, this.H * 0.45,
                                         this.W / 2, this.H / 2, this.W * 0.72);
      v.addColorStop(0, "rgba(40,30,14,0)");
      v.addColorStop(1, "rgba(40,30,14,0.30)");
      ctx.globalAlpha = 1;
      ctx.fillStyle = v;
      ctx.fillRect(0, 0, this.W, this.H);
      ctx.restore();
    }

    /* ================= political layer (on mapVersion) ================= */

    _modeColor(sim, pi) {
      const controller = sim ? sim.provinceState[this.provinces[pi].id].controller
                             : this.provinces[pi].controller;
      const f = this.seed.factions.find((x) => x.id === controller);
      if (!f) return null;
      if (this.mapMode === "culture") return this.seed.cultureColors[f.culture] || "#888070";
      if (this.mapMode === "religion") return this.seed.religionColors[f.religion] || "#888070";
      return f.color;
    }

    _buildPolitical(sim) {
      const k = this._k;
      if (!this._political) {
        this._political = document.createElement("canvas");
        this._political.width = LAYER_W;
        this._political.height = Math.round(this.H * k);
      }
      const layer = this._political;
      const ctx = layer.getContext("2d");
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.clearRect(0, 0, layer.width, layer.height);
      ctx.scale(k, k);
      ctx.lineJoin = "round"; ctx.lineCap = "round";

      // realm tints
      if (this.mapMode !== "terrain") {
        for (let pi = 0; pi < this.provinces.length; pi++) {
          const st = sim ? sim.provinceState[this.provinces[pi].id] : null;
          if (this.mapMode === "devastation") {
            const dev = st ? Math.min(1, st.devastation / 80) : 0;
            if (dev < 0.03) continue;
            ctx.globalAlpha = 0.15 + dev * 0.5;
            ctx.fillStyle = "#8c2f22";
          } else {
            const col = this._modeColor(sim, pi);
            if (!col) continue;
            ctx.globalAlpha = 0.46;
            ctx.fillStyle = col;
          }
          ctx.fill(this._provPaths[pi]);
          // occupation stripes over the base tint
          if (this.mapMode === "political" && st && st.occupier &&
              st.occupier !== st.controller) {
            const occ = this.seed.factions.find((x) => x.id === st.occupier);
            if (occ) {
              ctx.save();
              ctx.clip(this._provPaths[pi]);
              ctx.globalAlpha = 0.5;
              ctx.strokeStyle = occ.color;
              ctx.lineWidth = 7;
              for (let x = -this.H; x < this.W + this.H; x += 26) {
                ctx.beginPath();
                ctx.moveTo(x, 0);
                ctx.lineTo(x + this.H, this.H);
                ctx.stroke();
              }
              ctx.restore();
            }
          }
        }
      }
      ctx.globalAlpha = 1;

      // borders: heavy ink between realms, faint ink inside a realm
      const ctrl = (pi) => sim ? sim.provinceState[this.provinces[pi].id].controller
                               : this.provinces[pi].controller;
      for (const b of this.world.borderPaths) {
        const cross = ctrl(b.a) !== ctrl(b.b);
        if (this.mapMode === "terrain" && !cross) continue;
        ctx.strokeStyle = cross ? "rgba(38,29,14,0.85)" : "rgba(90,75,48,0.45)";
        ctx.lineWidth = cross ? 3.4 : 1.3;
        this._strokePoly(ctx, b.path);
      }
    }

    /* ================= view & composition ================= */

    worldToScreen(wx, wy) {
      const { width } = this.canvas;
      const z = this.view.zoom * (width / this.W);
      return {
        x: (wx - this.view.x) * z + width / 2,
        y: (wy - this.view.y) * z + this.canvas.height / 2,
        z,
      };
    }

    render(sim) {
      if (!this._terrain) this._buildTerrain();
      if (this._dirty || this._lastSim !== sim) {
        this._buildPolitical(sim);
        this._dirty = false;
        this._lastSim = sim;
      }
      const ctx = this.ctx;
      const { width, height } = this.canvas;
      ctx.save();
      ctx.fillStyle = "#141610";
      ctx.fillRect(0, 0, width, height);

      const tl = this.worldToScreen(0, 0);
      const z = tl.z;
      const drawW = this.W * z, drawH = this.H * z;
      ctx.imageSmoothingEnabled = true;
      ctx.imageSmoothingQuality = "high";
      ctx.drawImage(this._terrain, tl.x, tl.y, drawW, drawH);
      ctx.drawImage(this._political, tl.x, tl.y, drawW, drawH);

      // selected province outline
      if (this.selected) {
        const pi = this.provinces.findIndex((p) => p.id === this.selected);
        if (pi >= 0) {
          ctx.save();
          ctx.translate(tl.x, tl.y);
          ctx.scale(z, z);
          ctx.strokeStyle = "rgba(238,214,140,0.95)";
          ctx.lineWidth = Math.max(1.6, 3 / z) * 1.2;
          ctx.shadowColor = "rgba(238,214,140,0.6)";
          ctx.shadowBlur = 6 / z;
          ctx.stroke(this._outlinePaths[pi]);
          ctx.restore();
        }
      }

      this._drawLabels(ctx, sim, z);
      ctx.restore();
    }

    _drawLabels(ctx, sim, z) {
      // province names: small caps ink, fading out when zoomed far away
      const provAlpha = Math.max(0, Math.min(1, (z * this.W / this.canvas.width - 0.55) * 3 + 0.55));
      ctx.textAlign = "center";
      if (provAlpha > 0.05) {
        for (const p of this.provinces) {
          const pt = this.worldToScreen(p.x, p.y);
          const size = Math.max(9, 12.5 * z);
          ctx.font = `600 ${size}px 'Iowan Old Style', 'Palatino Linotype', Georgia, serif`;
          ctx.save();
          ctx.globalAlpha = provAlpha;
          ctx.letterSpacing = `${1.4 * z}px`;
          ctx.strokeStyle = "rgba(238,228,196,0.75)";
          ctx.lineWidth = 3;
          ctx.fillStyle = "rgba(52,42,24,0.9)";
          ctx.strokeText(p.name.toUpperCase(), pt.x, pt.y + 22 * z);
          ctx.fillText(p.name.toUpperCase(), pt.x, pt.y + 22 * z);
          ctx.restore();
        }
      }
      if (this.mapMode !== "political" || !sim) return;

      // realm names: dark ink calligraphy curved along the realm's axis
      for (const f of this.seed.factions) {
        const stats = this._realmAxis(sim, f.id);
        if (!stats) continue;
        const { cx, cy, angle, spread, count } = stats;
        const label = f.shortName.toUpperCase();
        const fs = Math.max(12, Math.min(46, (9 + Math.sqrt(count) * 1.55) * z));
        ctx.font = `700 italic ${fs}px 'Iowan Old Style', 'Palatino Linotype', Georgia, serif`;
        const spacing = fs * 0.34;
        const widths = [...label].map((ch) => ctx.measureText(ch).width + spacing);
        const total = widths.reduce((a, b) => a + b, -spacing);
        const lenWorld = Math.min(spread * 1.35, total / z + 40);
        const scaleFit = Math.min(1, (lenWorld * z) / total);
        const arc = lenWorld * 0.10;

        const dir = [Math.cos(angle), Math.sin(angle)];
        const perp = dir[1] > 0 || (dir[1] === 0 && dir[0] < 0)
          ? [dir[1], -dir[0]] : [-dir[1], dir[0]];   // arc bows upward on screen
        const P0 = [cx - dir[0] * lenWorld / 2, cy - dir[1] * lenWorld / 2];
        const P2 = [cx + dir[0] * lenWorld / 2, cy + dir[1] * lenWorld / 2];
        const P1 = [cx + perp[0] * arc, cy + perp[1] * arc];
        const bez = (t) => {
          const mt = 1 - t;
          return [
            mt * mt * P0[0] + 2 * mt * t * P1[0] + t * t * P2[0],
            mt * mt * P0[1] + 2 * mt * t * P1[1] + t * t * P2[1],
          ];
        };
        ctx.save();
        ctx.globalAlpha = 0.72;
        let travelled = 0;
        for (let i = 0; i < label.length; i++) {
          const t = total <= 0 ? 0.5 : (travelled + widths[i] / 2) / total;
          travelled += widths[i];
          const [wx, wy] = bez(t);
          const [ax, ay] = bez(Math.max(0, t - 0.02));
          const [bx, by] = bez(Math.min(1, t + 0.02));
          const rot = Math.atan2(by - ay, bx - ax);
          const pt = this.worldToScreen(wx, wy);
          ctx.save();
          ctx.translate(pt.x, pt.y);
          ctx.rotate(rot);
          ctx.scale(scaleFit, scaleFit);
          ctx.strokeStyle = "rgba(238,228,196,0.55)";
          ctx.lineWidth = Math.max(2, fs * 0.10);
          ctx.fillStyle = "rgba(45,35,18,0.92)";
          ctx.strokeText(label[i], 0, 0);
          ctx.fillText(label[i], 0, 0);
          ctx.restore();
        }
        ctx.restore();
      }
    }

    _realmAxis(sim, fid) {
      // mean + principal axis (PCA) of the realm's land cells
      let n = 0, sx = 0, sy = 0;
      const owned = [];
      for (const c of this.world.landCells) {
        const st = sim.provinceState[this.provinces[c.prov].id];
        if (st.controller !== fid) continue;
        owned.push(c);
        sx += c.x; sy += c.y; n++;
      }
      if (!n) return null;
      const cx = sx / n, cy = sy / n;
      let sxx = 0, syy = 0, sxy = 0;
      for (const c of owned) {
        const dx = c.x - cx, dy = c.y - cy;
        sxx += dx * dx; syy += dy * dy; sxy += dx * dy;
      }
      sxx /= n; syy /= n; sxy /= n;
      let angle = 0.5 * Math.atan2(2 * sxy, sxx - syy);
      // keep text readable: clamp slope, never upside down
      if (angle > Math.PI / 2) angle -= Math.PI;
      if (angle < -Math.PI / 2) angle += Math.PI;
      angle = Math.max(-0.45, Math.min(0.45, angle));
      const spread = Math.sqrt(Math.max(sxx, syy)) * 2.4 + 60;
      return { cx, cy, angle, spread, count: n };
    }

    screenToWorld(sx, sy) {
      const z = this.view.zoom * (this.canvas.width / this.W);
      return {
        x: (sx - this.canvas.width / 2) / z + this.view.x,
        y: (sy - this.canvas.height / 2) / z + this.view.y,
      };
    }

    /* ================= interaction (unchanged behaviour) ================= */

    attach(container, { onHover, onClick, onViewChange }) {
      let dragging = false, moved = false, lastX = 0, lastY = 0;
      const dpr = window.devicePixelRatio || 1;

      const toWorld = (ev) => {
        const rect = this.canvas.getBoundingClientRect();
        return this.screenToWorld((ev.clientX - rect.left) * dpr, (ev.clientY - rect.top) * dpr);
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

/* Layered CK2-style campaign map.
   The raw heightmap is invisible data for elevation shading. The unique-RGB
   province map is invisible data for hover/click lookups. The player sees a
   painted biome terrain layer with political/culture/religion overlays, labels,
   rivers, borders, and selection outlines drawn on top. */
(function () {
  "use strict";

  const RENDER_W = 1024, RENDER_H = 683;
  const SEA = -1;
  const HEIGHTMAP_URL = "assets/heightmaps/world_heightmap_3072x2048_16bit.png";
  const PROVINCE_MAP_URL = "assets/provinces/world_provinces_unique_rgb_3072x2048.png";
  const DEFINITIONS_URL = "assets/provinces/world_province_definitions.csv";
  const ADJACENCY_URL = "assets/provinces/world_province_adjacency.csv";

  const TERRAIN_GLYPHS = {
    mountain_pass: "▲", mine_hills: "▲", bog_forest: "♣", canal_farmland: "≈",
    river_city: "⌂", charter_city: "⌂", river_port: "⌂", frontier_farms: "·",
    sacred_battlefield: "✦", steppe_market: "☾",
  };

  const REGION_TINTS = {
    REG_ROV_BASIN: [16, 26, 0], REG_CAIRN_MARCH: [-8, 16, -4],
    REG_GREYHOOK: [10, 8, 8], REG_TALUUN_STEPPE: [24, 14, -16],
    REG_MAREN_COAST: [-8, 12, 18], REG_QERESH_DRYLANDS: [28, 12, -24],
    REG_FENWARD: [-20, 24, -8], REG_BANNERFIELDS: [18, 18, -8],
  };

  class LayeredWorldMap extends WG.WorldMap {
    constructor(canvas, seed) {
      super(canvas, seed);
      this.layerStatus = "loading";
      this.renderW = RENDER_W; this.renderH = RENDER_H;
      this.definitions = new Map();
      this.rgbToProvinceId = new Map();
      this.seedProvinceById = new Map(seed.provinces.map((p) => [p.id, p]));
      this.provinceIndexById = new Map(seed.provinces.map((p, i) => [p.id, i]));
      this._rgbOwner = null;
      this._renderProvinceIds = null;
      this._heightData = null;
      this._provinceData = null;
      this._provinceCanvas = null;
      this._heightCanvas = null;
      this._image = null;
      this.ready = this._loadLayers().then(() => {
        this.layerStatus = "ready";
        this.W = this.provinceMapWidth || this.W;
        this.H = this.provinceMapHeight || this.H;
        this.view = { x: this.W / 2, y: this.H / 2, zoom: 0.9 };
        this._computeRgbOwnership();
        this._computeRgbCoastDistance();
        this._computeCsvAdjacency();
        this._computeRgbDecorations();
        this.markDirty();
      }).catch((err) => {
        console.warn("Layered map assets unavailable; using generated map fallback.", err);
        this.layerStatus = "fallback";
      });
    }

    async _loadLayers() {
      const [heightImg, provinceImg, definitionsText, adjacencyText] = await Promise.all([
        this._loadImage(HEIGHTMAP_URL), this._loadImage(PROVINCE_MAP_URL),
        fetch(DEFINITIONS_URL).then((r) => { if (!r.ok) throw new Error(DEFINITIONS_URL); return r.text(); }),
        fetch(ADJACENCY_URL).then((r) => { if (!r.ok) throw new Error(ADJACENCY_URL); return r.text(); }),
      ]);
      this._adjacencyText = adjacencyText;
      this._parseDefinitions(definitionsText);
      this.provinceMapWidth = provinceImg.naturalWidth;
      this.provinceMapHeight = provinceImg.naturalHeight;
      this.heightMapWidth = heightImg.naturalWidth;
      this.heightMapHeight = heightImg.naturalHeight;
      this._heightCanvas = this._imageCanvas(heightImg);
      this._provinceCanvas = this._imageCanvas(provinceImg);
      this._heightData = this._heightCanvas.getContext("2d", { willReadFrequently: true })
        .getImageData(0, 0, this.heightMapWidth, this.heightMapHeight).data;
      this._provinceData = this._provinceCanvas.getContext("2d", { willReadFrequently: true })
        .getImageData(0, 0, this.provinceMapWidth, this.provinceMapHeight).data;
    }

    _loadImage(src) {
      return new Promise((resolve, reject) => {
        const img = new Image();
        img.onload = () => resolve(img);
        img.onerror = () => reject(new Error(`Could not load ${src}`));
        img.src = src;
      });
    }

    _imageCanvas(img) {
      const c = document.createElement("canvas");
      c.width = img.naturalWidth; c.height = img.naturalHeight;
      c.getContext("2d", { willReadFrequently: true }).drawImage(img, 0, 0);
      return c;
    }

    _parseCsv(text) {
      const rows = [];
      let row = [], field = "", quoted = false;
      for (let i = 0; i < text.length; i++) {
        const ch = text[i], next = text[i + 1];
        if (quoted && ch === '"' && next === '"') { field += '"'; i++; }
        else if (ch === '"') quoted = !quoted;
        else if (!quoted && ch === ',') { row.push(field); field = ""; }
        else if (!quoted && (ch === '\n' || ch === '\r')) {
          if (ch === '\r' && next === '\n') i++;
          row.push(field); field = "";
          if (row.some((v) => v !== "")) rows.push(row);
          row = [];
        } else field += ch;
      }
      row.push(field); if (row.some((v) => v !== "")) rows.push(row);
      return rows;
    }

    _parseDefinitions(text) {
      const rows = this._parseCsv(text);
      const header = rows.shift();
      const idx = Object.fromEntries(header.map((h, i) => [h, i]));
      for (const row of rows) {
        const id = row[idx.province_id];
        const def = {
          id, red: Number(row[idx.red]), green: Number(row[idx.green]), blue: Number(row[idx.blue]),
          name: row[idx.common_name], localName: row[idx.local_name], imperialName: row[idx.old_imperial_name],
          religiousName: row[idx.religious_name], enemyName: row[idx.enemy_name], region: row[idx.region_id],
          controller: row[idx.controller], terrain: row[idx.terrain], resource: row[idx.primary_resource],
          roads: Number(row[idx.road_level] || 0), port: Number(row[idx.port_level] || 0),
          fort: Number(row[idx.fort_level] || 0), manaSite: Number(row[idx.mana_site_level] || 0),
          value: Number(row[idx.strategic_value] || 0), x: Number(row[idx.center_x]), y: Number(row[idx.center_y]),
        };
        this.definitions.set(id, def);
        this.rgbToProvinceId.set(`${def.red},${def.green},${def.blue}`, id);
      }
    }

    _computeRgbOwnership() {
      this._rgbOwner = new Int16Array(RENDER_W * RENDER_H).fill(SEA);
      this._renderProvinceIds = new Array(RENDER_W * RENDER_H).fill(null);
      for (let gy = 0; gy < RENDER_H; gy++) {
        for (let gx = 0; gx < RENDER_W; gx++) {
          const id = this._provinceIdAtPixel(
            Math.floor((gx + 0.5) / RENDER_W * this.provinceMapWidth),
            Math.floor((gy + 0.5) / RENDER_H * this.provinceMapHeight));
          this._renderProvinceIds[gy * RENDER_W + gx] = id;
          const idx = this.provinceIndexById.get(id);
          if (idx !== undefined) this._rgbOwner[gy * RENDER_W + gx] = idx;
        }
      }
      this.cellOwner = this._rgbOwner;
    }

    _computeRgbCoastDistance() {
      const max = 65535;
      this.coastDistance = new Uint16Array(RENDER_W * RENDER_H).fill(max);
      const queue = new Int32Array(RENDER_W * RENDER_H);
      let head = 0, tail = 0;
      for (let y = 0; y < RENDER_H; y++) for (let x = 0; x < RENDER_W; x++) {
        const i = y * RENDER_W + x, o = this._renderProvinceIds[i];
        for (let d = 0; d < 4; d++) {
          const nx = x + [1, -1, 0, 0][d], ny = y + [0, 0, 1, -1][d];
          if (nx < 0 || ny < 0 || nx >= RENDER_W || ny >= RENDER_H) continue;
          const n = this._renderProvinceIds[ny * RENDER_W + nx];
          if ((!o && n) || (o && !n)) {
            this.coastDistance[i] = 0; queue[tail++] = i; break;
          }
        }
      }
      while (head < tail) {
        const i = queue[head++], x = i % RENDER_W, y = Math.floor(i / RENDER_W), next = this.coastDistance[i] + 1;
        for (let d = 0; d < 4; d++) {
          const nx = x + [1, -1, 0, 0][d], ny = y + [0, 0, 1, -1][d];
          if (nx < 0 || ny < 0 || nx >= RENDER_W || ny >= RENDER_H) continue;
          const ni = ny * RENDER_W + nx;
          if (next < this.coastDistance[ni]) { this.coastDistance[ni] = next; queue[tail++] = ni; }
        }
      }
    }

    _computeCsvAdjacency() {
      const adj = {};
      this.provinces.forEach((p) => { adj[p.id] = new Set(); });
      for (const [a, b] of this._parseCsv(this._adjacencyText).slice(1)) {
        if (adj[a] && adj[b]) { adj[a].add(b); adj[b].add(a); }
      }
      for (const key of Object.keys(adj)) this.adjacency[key] = [...adj[key]];
      this._ensureAdj("PROV_WHITE_MARE", "PROV_OPEN_GATE");
      this._ensureAdj("PROV_WHITE_MARE", "PROV_NINTH_BANNER");
    }

    _computeRgbDecorations() {
      this.borderSegs = {}; this.glyphPoints = {};
      const candidates = {};
      this.provinces.forEach((p) => { this.borderSegs[p.id] = []; this.glyphPoints[p.id] = []; candidates[p.id] = []; });
      const sx = this.W / RENDER_W, sy = this.H / RENDER_H;
      for (let y = 0; y < RENDER_H; y++) for (let x = 0; x < RENDER_W; x++) {
        const o = this._rgbOwner[y * RENDER_W + x];
        if (o < 0) continue;
        const id = this.provinces[o].id;
        const right = x + 1 < RENDER_W ? this._rgbOwner[y * RENDER_W + x + 1] : SEA;
        const down = y + 1 < RENDER_H ? this._rgbOwner[(y + 1) * RENDER_W + x] : SEA;
        if (right !== o) this._addBorder(id, right, (x + 1) * sx, y * sy, (x + 1) * sx, (y + 1) * sy);
        if (down !== o) this._addBorder(id, down, x * sx, (y + 1) * sy, (x + 1) * sx, (y + 1) * sy);
        if (x % 12 === 6 && y % 12 === 6 && this.coastDistance[y * RENDER_W + x] > 2) {
          const h = this._hash2(x + o * 97, y - o * 131);
          if (h > 0.82) candidates[id].push([(x + this._hash2(x, y) - 0.5) * sx, (y + this._hash2(x + 19, y) - 0.5) * sy, h]);
        }
      }
      for (const p of this.provinces) {
        const min = p.terrain === "mountain_pass" ? 120 : 86;
        for (const c of candidates[p.id].sort((a, b) => b[2] - a[2])) {
          if (this.glyphPoints[p.id].every(([x, y]) => (x - c[0]) ** 2 + (y - c[1]) ** 2 >= min ** 2)) this.glyphPoints[p.id].push(c);
        }
      }
    }

    _addBorder(id, other, x1, y1, x2, y2) {
      this.borderSegs[id].push([x1, y1, x2, y2]);
      if (other >= 0) this.borderSegs[this.provinces[other].id].push([x1, y1, x2, y2]);
    }

    _provinceIdAtPixel(px, py) {
      if (!this._provinceData || px < 0 || py < 0 || px >= this.provinceMapWidth || py >= this.provinceMapHeight) return null;
      const off = (py * this.provinceMapWidth + px) * 4;
      return this.rgbToProvinceId.get(`${this._provinceData[off]},${this._provinceData[off + 1]},${this._provinceData[off + 2]}`) || null;
    }

    provinceIdAtPixel(px, py) { return this._provinceIdAtPixel(px, py); }

    provinceAt(worldX, worldY) {
      if (this.layerStatus !== "ready") return super.provinceAt(worldX, worldY);
      const px = Math.floor(worldX / this.W * this.provinceMapWidth);
      const py = Math.floor(worldY / this.H * this.provinceMapHeight);
      const id = this._provinceIdAtPixel(px, py);
      return this.seedProvinceById.get(id) || null;
    }

    _heightAt(px, py) {
      if (!this._heightData) return 0.45;
      const hx = Math.max(0, Math.min(this.heightMapWidth - 1, Math.floor(px / this.provinceMapWidth * this.heightMapWidth)));
      const hy = Math.max(0, Math.min(this.heightMapHeight - 1, Math.floor(py / this.provinceMapHeight * this.heightMapHeight)));
      return this._heightData[(hy * this.heightMapWidth + hx) * 4] / 255;
    }

    _biomeColor(prov, height) {
      const terrain = prov && prov.terrain;
      let rgb;
      if (!prov) rgb = [55, 92, 116];
      else if (terrain === "bog_forest") rgb = [45, 80, 45];
      else if (terrain === "canal_farmland" || terrain === "river_city") rgb = [95, 135, 65];
      else if (terrain === "frontier_farms" || terrain === "sacred_battlefield") rgb = [85, 115, 70];
      else if (terrain === "steppe_market") rgb = [145, 130, 75];
      else if (terrain === "mountain_pass" || terrain === "mine_hills") rgb = [105, 105, 100];
      else if (terrain === "river_port") rgb = [70, 115, 95];
      else if (terrain === "charter_city") rgb = [105, 120, 78];
      else rgb = [100, 120, 75];
      const rt = REGION_TINTS[prov && prov.region] || [0, 0, 0];
      rgb = [rgb[0] + rt[0], rgb[1] + rt[1], rgb[2] + rt[2]];
      if (height > 0.70) rgb = [rgb[0] * 0.65 + 155 * 0.35, rgb[1] * 0.65 + 150 * 0.35, rgb[2] * 0.65 + 140 * 0.35];
      if (height > 0.86) rgb = [rgb[0] * 0.55 + 220 * 0.45, rgb[1] * 0.55 + 220 * 0.45, rgb[2] * 0.55 + 215 * 0.45];
      return rgb;
    }

    _paintWorld(sim) {
      if (this.layerStatus !== "ready") return super._paintWorld(sim);
      if (!this._image) { this._image = document.createElement("canvas"); this._image.width = RENDER_W; this._image.height = RENDER_H; }
      const ictx = this._image.getContext("2d");
      const img = ictx.createImageData(RENDER_W, RENDER_H), data = img.data;
      const factionRGB = {}, cultureRGB = {}, religionRGB = {};
      for (const f of this.seed.factions) {
        factionRGB[f.id] = this._hex(f.color);
        cultureRGB[f.id] = this._hex(this.seed.cultureColors[f.culture] || "#888070");
        religionRGB[f.id] = this._hex(this.seed.religionColors[f.religion] || "#888070");
      }
      for (let y = 0; y < RENDER_H; y++) for (let x = 0; x < RENDER_W; x++) {
        const i = y * RENDER_W + x, off = i * 4, owner = this._rgbOwner[i], provinceId = this._renderProvinceIds[i];
        const px = Math.floor((x + 0.5) / RENDER_W * this.provinceMapWidth), py = Math.floor((y + 0.5) / RENDER_H * this.provinceMapHeight);
        const h = this._heightAt(px, py), wx = x / RENDER_W * this.W, wy = y / RENDER_H * this.H;
        const grain = (this.noise.fbm(wx * 0.012, wy * 0.012, 3) - 0.5) * 20;
        let rgb;
        if (!provinceId) {
          const shelf = Math.max(0, 1 - Math.min(1, this.coastDistance[i] / 28));
          rgb = [38 + shelf * 45 + grain, 56 + shelf * 60 + grain, 78 + shelf * 62 + grain];
        } else {
          const prov = owner >= 0 ? this.provinces[owner] : this.definitions.get(provinceId);
          const state = owner >= 0 && sim ? sim.provinceState[prov.id] : null;
          const controller = state ? state.controller : prov.controller;
          rgb = this._biomeColor(prov, h);
          let tint = factionRGB[controller] || [120, 120, 120], mix = 0.50;
          if (this.mapMode === "culture") tint = cultureRGB[controller] || tint;
          else if (this.mapMode === "religion") tint = religionRGB[controller] || tint;
          else if (this.mapMode === "terrain") mix = 0;
          else if (this.mapMode === "devastation") { const d = state ? Math.min(1, state.devastation / 80) : 0; tint = [140, 47, 34]; mix = 0.10 + d * 0.62; }
          rgb = [rgb[0] * (1 - mix) + tint[0] * mix, rgb[1] * (1 - mix) + tint[1] * mix, rgb[2] * (1 - mix) + tint[2] * mix];
          if (this.mapMode === "political" && state && state.occupier && state.occupier !== controller && ((x + y) % 8) < 4) {
            const occ = factionRGB[state.occupier] || [200, 200, 200]; rgb = [rgb[0] * 0.35 + occ[0] * 0.65, rgb[1] * 0.35 + occ[1] * 0.65, rgb[2] * 0.35 + occ[2] * 0.65];
          }
          const shade = 0.76 + h * 0.42 + grain / 255;
          rgb = [rgb[0] * shade, rgb[1] * shade, rgb[2] * shade];
          let border = false, realmBorder = false;
          for (let d = 0; d < 4; d++) {
            const nx = x + [1, -1, 0, 0][d], ny = y + [0, 0, 1, -1][d];
            if (nx < 0 || ny < 0 || nx >= RENDER_W || ny >= RENDER_H) continue;
            const nid = this._renderProvinceIds[ny * RENDER_W + nx];
            if (nid !== provinceId) { border = true; if (nid) {
              const nOwner = this._rgbOwner[ny * RENDER_W + nx];
              const np = nOwner >= 0 ? this.provinces[nOwner] : this.definitions.get(nid);
              const ns = nOwner >= 0 && sim ? sim.provinceState[np.id] : null;
              if ((ns ? ns.controller : np.controller) !== controller) realmBorder = true;
            }}
          }
          if (realmBorder) rgb = rgb.map((v) => v * 0.40); else if (border) rgb = rgb.map((v) => v * 0.70);
        }
        data[off] = rgb[0]; data[off + 1] = rgb[1]; data[off + 2] = rgb[2]; data[off + 3] = 255;
      }
      ictx.putImageData(img, 0, 0);
      this._dirty = false;
    }
  }

  window.WG = window.WG || {};
  window.WG.LayeredWorldMap = LayeredWorldMap;
})();

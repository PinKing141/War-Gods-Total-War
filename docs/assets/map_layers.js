/* Layered CK2-style campaign map.
   The heightmap is terrain data, the unique-RGB province map is interaction
   data, and the visible canvas is a painted strategic map. */
(function () {
  "use strict";

  const RENDER_W = 1536, RENDER_H = 1024;
  const SEA = -1;
  const HEIGHTMAP_URL = "assets/heightmaps/world_heightmap_3072x2048_16bit.png";
  const PROVINCE_MAP_URL = "assets/provinces/world_provinces_unique_rgb_3072x2048.png";
  const DEFINITIONS_URL = "assets/provinces/world_province_definitions.csv";
  const ADJACENCY_URL = "assets/provinces/world_province_adjacency.csv";

  const LOCAL_FACTIONS = {
    FAC_QERESH_LOCAL: {
      id: "FAC_QERESH_LOCAL", name: "Qeresh Well Courts", shortName: "Qeresh",
      identity: "water-law oasis courts", culture: "CULT_QERESH",
      religion: "REL_SALT_WITNESS", government: "well_court",
      color: "#b79045", charge: "bell",
    },
    FAC_FENWARD_LOCAL: {
      id: "FAC_FENWARD_LOCAL", name: "Fenward Marsh Holds", shortName: "Fenward",
      identity: "wet forest and marsh frontier", culture: "mixed_frontier",
      religion: "REL_HEARTH_BELOW", government: "marsh_holds",
      color: "#4f7d55", charge: "cairn",
    },
    FAC_OSTREN_LOCAL: {
      id: "FAC_OSTREN_LOCAL", name: "Ostren Bannerfield Estates", shortName: "Ostren",
      identity: "grain estate cavalry country", culture: "CULT_OSTREN",
      religion: "REL_NINE_BANNERS", government: "estate_league",
      color: "#7c9653", charge: "banners",
    },
  };

  const TERRAIN_INFO = {
    river_city: { label: "River City", base: [112, 130, 84] },
    canal_farmland: { label: "Canal Farmland", base: [103, 142, 67] },
    charter_city: { label: "Charter City", base: [116, 113, 91] },
    frontier_farms: { label: "Frontier Farms", base: [97, 121, 73] },
    sacred_battlefield: { label: "Sacred Battlefield", base: [117, 108, 77] },
    river_port: { label: "River Port", base: [72, 116, 100] },
    bog_forest: { label: "Bog Forest", base: [43, 78, 45] },
    steppe_market: { label: "Steppe Market", base: [148, 130, 73] },
    dryland_plateau: { label: "Dryland Plateau", base: [154, 124, 73] },
    oasis_salt_road: { label: "Oasis Salt Road", base: [137, 139, 82] },
    grain_estate: { label: "Grain Estate", base: [125, 150, 73] },
    iron_hills: { label: "Iron Hills", base: [112, 106, 88] },
    mine_hills: { label: "Mine Hills", base: [104, 102, 92] },
    mountain_pass: { label: "Mountain Pass", base: [103, 101, 97] },
  };

  const TERRAIN_GLYPHS = {
    mountain_pass: "▲", mine_hills: "▲", iron_hills: "▲",
    bog_forest: "♣", canal_farmland: "≈", oasis_salt_road: "≈",
    river_city: "⌂", charter_city: "⌂", river_port: "⌂",
    frontier_farms: "·", grain_estate: "·",
    sacred_battlefield: "✦", steppe_market: "☾",
  };

  const REGION_TINTS = {
    REG_ROV_BASIN: [16, 24, 0],
    REG_CAIRN_MARCH: [-8, 16, -4],
    REG_GREYHOOK: [8, 7, 6],
    REG_TALUUN_STEPPE: [22, 13, -15],
    REG_MAREN_COAST: [-8, 12, 18],
    REG_QERESH_WELLS: [28, 13, -25],
    REG_FENWARD: [-20, 25, -8],
    REG_BANNERFIELDS: [18, 18, -8],
  };

  const REGION_LABELS = {
    REG_ROV_BASIN: "Rov Basin",
    REG_CAIRN_MARCH: "Cairn March",
    REG_GREYHOOK: "Greyhook Spine",
    REG_TALUUN_STEPPE: "Taluun Steppe",
    REG_MAREN_COAST: "Maren Coast",
    REG_QERESH_WELLS: "Qeresh Wells",
    REG_FENWARD: "Fenward",
    REG_BANNERFIELDS: "Bannerfields",
  };

  class LayeredWorldMap extends WG.WorldMap {
    constructor(canvas, seed) {
      super(canvas, seed);
      this.layerStatus = "loading";
      this.renderW = RENDER_W;
      this.renderH = RENDER_H;
      this.generatedAdjacency = this._cloneAdjacency(this.adjacency);
      this.seedProvinceById = new Map(seed.provinces.map((p) => [p.id, p]));
      this.seedProvinceIds = new Set(seed.provinces.map((p) => p.id));
      this.mapProvinces = [];
      this.provinceById = new Map();
      this.mapProvinceIndexById = new Map();
      this.rgbToProvinceIndex = new Map();
      this.factionById = new Map(seed.factions.map((f) => [f.id, f]));
      for (const f of Object.values(LOCAL_FACTIONS)) this.factionById.set(f.id, f);
      this.provinceAdjacency = {};
      this.realmLabelPoints = [];
      this._adjacencyText = "";
      this._heightData = null;
      this._provinceData = null;
      this._renderProvinceIndex = null;
      this._renderHeight = null;
      this._renderShade = null;
      this._renderSlope = null;

      this.ready = this._loadLayers().then(() => {
        this.layerStatus = "ready";
        this.W = this.provinceMapWidth;
        this.H = this.provinceMapHeight;
        this.view = { x: this.W / 2, y: this.H / 2, zoom: 0.9 };
        this.provinces = this.mapProvinces;
        this._buildRenderSources();
        this._computeLayerCoastDistance();
        this._buildCsvAdjacency();
        this._computeLayerDecorations();
        this._buildRealmLabels();
        this.cellOwner = this._renderProvinceIndex;
        this.markDirty();
      }).catch((err) => {
        console.warn("Layered map assets unavailable; using generated map fallback.", err);
        this.layerStatus = "fallback";
      });
    }

    _cloneAdjacency(adj) {
      const out = {};
      for (const [id, list] of Object.entries(adj || {})) out[id] = [...list];
      return out;
    }

    async _loadLayers() {
      const [heightImg, provinceImg, definitionsText, adjacencyText] = await Promise.all([
        this._loadImage(HEIGHTMAP_URL),
        this._loadImage(PROVINCE_MAP_URL),
        fetch(DEFINITIONS_URL).then((r) => {
          if (!r.ok) throw new Error(DEFINITIONS_URL);
          return r.text();
        }),
        fetch(ADJACENCY_URL).then((r) => {
          if (!r.ok) throw new Error(ADJACENCY_URL);
          return r.text();
        }),
      ]);

      this._adjacencyText = adjacencyText;
      this._parseDefinitions(definitionsText);
      this.provinceMapWidth = provinceImg.naturalWidth;
      this.provinceMapHeight = provinceImg.naturalHeight;
      this.heightMapWidth = heightImg.naturalWidth;
      this.heightMapHeight = heightImg.naturalHeight;

      const heightCanvas = this._imageCanvas(heightImg);
      const provinceCanvas = this._imageCanvas(provinceImg);
      this._heightData = heightCanvas.getContext("2d", { willReadFrequently: true })
        .getImageData(0, 0, this.heightMapWidth, this.heightMapHeight).data;
      this._provinceData = provinceCanvas.getContext("2d", { willReadFrequently: true })
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
      c.width = img.naturalWidth;
      c.height = img.naturalHeight;
      c.getContext("2d", { willReadFrequently: true }).drawImage(img, 0, 0);
      return c;
    }

    _parseCsv(text) {
      const rows = [];
      let row = [], field = "", quoted = false;
      for (let i = 0; i < text.length; i++) {
        const ch = text[i], next = text[i + 1];
        if (quoted && ch === '"' && next === '"') {
          field += '"';
          i++;
        } else if (ch === '"') {
          quoted = !quoted;
        } else if (!quoted && ch === ",") {
          row.push(field);
          field = "";
        } else if (!quoted && (ch === "\n" || ch === "\r")) {
          if (ch === "\r" && next === "\n") i++;
          row.push(field);
          field = "";
          if (row.some((v) => v !== "")) rows.push(row);
          row = [];
        } else {
          field += ch;
        }
      }
      row.push(field);
      if (row.some((v) => v !== "")) rows.push(row);
      return rows;
    }

    _parseDefinitions(text) {
      const rows = this._parseCsv(text);
      const header = rows.shift().map((h) => h.replace(/^\ufeff/, ""));
      const idx = Object.fromEntries(header.map((h, i) => [h, i]));
      for (const row of rows) {
        const id = row[idx.province_id];
        const seedProv = this.seedProvinceById.get(id);
        const def = {
          id,
          index: Number(row[idx.province_index]),
          red: Number(row[idx.red]),
          green: Number(row[idx.green]),
          blue: Number(row[idx.blue]),
          name: row[idx.common_name],
          localName: row[idx.local_name],
          imperialName: row[idx.old_imperial_name],
          religiousName: row[idx.religious_name],
          enemyName: row[idx.enemy_name],
          region: row[idx.region_id],
          regionName: REGION_LABELS[row[idx.region_id]] || row[idx.region_id],
          controller: row[idx.controller],
          terrain: row[idx.terrain],
          resource: row[idx.primary_resource],
          roads: Number(row[idx.road_level] || 0),
          port: Number(row[idx.port_level] || 0),
          fort: Number(row[idx.fort_level] || 0),
          manaSite: Number(row[idx.mana_site_level] || 0),
          value: Number(row[idx.strategic_value] || 0),
          x: Number(row[idx.center_x]),
          y: Number(row[idx.center_y]),
          pixelArea: Number(row[idx.pixel_area] || 0),
          isSeedFrontier: row[idx.is_seed_frontier] === "yes",
          mapOnly: !seedProv,
        };
        this.mapProvinceIndexById.set(id, this.mapProvinces.length);
        this.provinceById.set(id, def);
        this.rgbToProvinceIndex.set(this._rgbKey(def.red, def.green, def.blue), this.mapProvinces.length);
        this.mapProvinces.push(def);
      }
    }

    _rgbKey(r, g, b) {
      return (r << 16) | (g << 8) | b;
    }

    _provinceIndexAtPixel(px, py) {
      if (!this._provinceData || px < 0 || py < 0 ||
          px >= this.provinceMapWidth || py >= this.provinceMapHeight) return SEA;
      const off = (py * this.provinceMapWidth + px) * 4;
      const key = this._rgbKey(
        this._provinceData[off],
        this._provinceData[off + 1],
        this._provinceData[off + 2]);
      const idx = this.rgbToProvinceIndex.get(key);
      return idx === undefined ? SEA : idx;
    }

    _heightAtMapPixel(px, py) {
      if (!this._heightData) return 0.45;
      const hx = Math.max(0, Math.min(this.heightMapWidth - 1,
        Math.floor(px / this.provinceMapWidth * this.heightMapWidth)));
      const hy = Math.max(0, Math.min(this.heightMapHeight - 1,
        Math.floor(py / this.provinceMapHeight * this.heightMapHeight)));
      return this._heightData[(hy * this.heightMapWidth + hx) * 4] / 255;
    }

    _buildRenderSources() {
      const total = RENDER_W * RENDER_H;
      this._renderProvinceIndex = new Int32Array(total).fill(SEA);
      this._renderHeight = new Float32Array(total);
      this._renderShade = new Float32Array(total);
      this._renderSlope = new Float32Array(total);

      for (let y = 0; y < RENDER_H; y++) {
        const py = Math.floor((y + 0.5) / RENDER_H * this.provinceMapHeight);
        for (let x = 0; x < RENDER_W; x++) {
          const px = Math.floor((x + 0.5) / RENDER_W * this.provinceMapWidth);
          const i = y * RENDER_W + x;
          this._renderProvinceIndex[i] = this._provinceIndexAtPixel(px, py);
          this._renderHeight[i] = this._heightAtMapPixel(px, py);
        }
      }

      for (let y = 0; y < RENDER_H; y++) {
        for (let x = 0; x < RENDER_W; x++) {
          const i = y * RENDER_W + x;
          const xl = Math.max(0, x - 1), xr = Math.min(RENDER_W - 1, x + 1);
          const yu = Math.max(0, y - 1), yd = Math.min(RENDER_H - 1, y + 1);
          const dx = this._renderHeight[y * RENDER_W + xr] - this._renderHeight[y * RENDER_W + xl];
          const dy = this._renderHeight[yd * RENDER_W + x] - this._renderHeight[yu * RENDER_W + x];
          const slope = Math.min(1, Math.sqrt(dx * dx + dy * dy) * 7.5);
          this._renderSlope[i] = slope;
          this._renderShade[i] = Math.max(0.56, Math.min(1.28,
            0.85 + this._renderHeight[i] * 0.26 + (-dx * 4.2 - dy * 2.8) - slope * 0.16));
        }
      }
    }

    _computeLayerCoastDistance() {
      const max = 65535;
      this.coastDistance = new Uint16Array(RENDER_W * RENDER_H).fill(max);
      const queue = new Int32Array(RENDER_W * RENDER_H);
      let head = 0, tail = 0;
      for (let y = 0; y < RENDER_H; y++) {
        for (let x = 0; x < RENDER_W; x++) {
          const i = y * RENDER_W + x;
          const here = this._renderProvinceIndex[i];
          for (let d = 0; d < 4; d++) {
            const nx = x + [1, -1, 0, 0][d], ny = y + [0, 0, 1, -1][d];
            if (nx < 0 || ny < 0 || nx >= RENDER_W || ny >= RENDER_H) continue;
            const there = this._renderProvinceIndex[ny * RENDER_W + nx];
            if ((here === SEA && there !== SEA) || (here !== SEA && there === SEA)) {
              this.coastDistance[i] = 0;
              queue[tail++] = i;
              break;
            }
          }
        }
      }
      while (head < tail) {
        const i = queue[head++];
        const x = i % RENDER_W, y = Math.floor(i / RENDER_W);
        const next = this.coastDistance[i] + 1;
        for (let d = 0; d < 4; d++) {
          const nx = x + [1, -1, 0, 0][d], ny = y + [0, 0, 1, -1][d];
          if (nx < 0 || ny < 0 || nx >= RENDER_W || ny >= RENDER_H) continue;
          const ni = ny * RENDER_W + nx;
          if (next < this.coastDistance[ni]) {
            this.coastDistance[ni] = next;
            queue[tail++] = ni;
          }
        }
      }
    }

    _buildCsvAdjacency() {
      const full = {};
      const sim = {};
      for (const p of this.mapProvinces) full[p.id] = new Set();
      for (const id of this.seedProvinceIds) sim[id] = new Set();

      for (const row of this._parseCsv(this._adjacencyText).slice(1)) {
        const a = row[0], b = row[1];
        if (full[a] && full[b]) {
          full[a].add(b);
          full[b].add(a);
        }
        if (this.seedProvinceIds.has(a) && this.seedProvinceIds.has(b)) {
          sim[a].add(b);
          sim[b].add(a);
        }
      }

      this.provinceAdjacency = {};
      for (const [id, set] of Object.entries(full)) this.provinceAdjacency[id] = [...set];

      this._projectSeedAdjacency(sim, 2);
      for (const id of this.seedProvinceIds) {
        if (sim[id].size === 0) this._connectNearestSeedProvinces(sim, id, 2);
      }
      this.adjacency = {};
      for (const [id, set] of Object.entries(sim)) this.adjacency[id] = [...set];
      this._ensureAdj("PROV_WHITE_MARE", "PROV_OPEN_GATE");
      this._ensureAdj("PROV_WHITE_MARE", "PROV_NINTH_BANNER");
      this._ensureAdj("PROV_NINTH_BANNER", "PROV_THIRD_CHARTER");
      this._ensureAdj("PROV_RED_BOG", "PROV_SEVRIN_CANAL");
    }

    _projectSeedAdjacency(sim, maxSteps) {
      for (const start of this.seedProvinceIds) {
        const queue = [[start, 0]];
        const seen = new Set([start]);
        for (let qi = 0; qi < queue.length; qi++) {
          const [id, steps] = queue[qi];
          if (steps > 0 && this.seedProvinceIds.has(id)) {
            sim[start].add(id);
            sim[id].add(start);
            continue;
          }
          if (steps >= maxSteps) continue;
          for (const next of this.provinceAdjacency[id] || []) {
            if (seen.has(next)) continue;
            seen.add(next);
            queue.push([next, steps + 1]);
          }
        }
      }
    }

    _connectNearestSeedProvinces(sim, id, count) {
      const p = this.provinceById.get(id);
      if (!p) return;
      const nearest = [...this.seedProvinceIds]
        .filter((other) => other !== id && this.provinceById.has(other))
        .map((other) => {
          const q = this.provinceById.get(other);
          return [other, (p.x - q.x) ** 2 + (p.y - q.y) ** 2];
        })
        .sort((a, b) => a[1] - b[1])
        .slice(0, count);
      for (const [other] of nearest) {
        sim[id].add(other);
        sim[other].add(id);
      }
    }

    _computeLayerDecorations() {
      this.borderSegs = {};
      this.glyphPoints = {};
      const candidates = {};
      for (const p of this.mapProvinces) {
        this.borderSegs[p.id] = [];
        this.glyphPoints[p.id] = [];
        candidates[p.id] = [];
      }
      const sx = this.W / RENDER_W, sy = this.H / RENDER_H;
      for (let y = 0; y < RENDER_H; y++) {
        for (let x = 0; x < RENDER_W; x++) {
          const i = y * RENDER_W + x;
          const idx = this._renderProvinceIndex[i];
          if (idx === SEA) continue;
          const id = this.mapProvinces[idx].id;
          const right = x + 1 < RENDER_W ? this._renderProvinceIndex[y * RENDER_W + x + 1] : SEA;
          const down = y + 1 < RENDER_H ? this._renderProvinceIndex[(y + 1) * RENDER_W + x] : SEA;
          if (right !== idx) this._addBorder(id, right, (x + 1) * sx, y * sy, (x + 1) * sx, (y + 1) * sy);
          if (down !== idx) this._addBorder(id, down, x * sx, (y + 1) * sy, (x + 1) * sx, (y + 1) * sy);

          const p = this.mapProvinces[idx];
          if (!TERRAIN_GLYPHS[p.terrain] || this.coastDistance[i] <= 2) continue;
          if (x % 14 === 7 && y % 14 === 7) {
            const h = this._hash2(x + idx * 97, y - idx * 131);
            if (h > 0.80) {
              candidates[id].push([
                (x + this._hash2(x, y) - 0.5) * sx,
                (y + this._hash2(x + 19, y - 23) - 0.5) * sy,
                h,
              ]);
            }
          }
        }
      }

      for (const p of this.mapProvinces) {
        const min = p.terrain === "mountain_pass" ? 92 :
          p.terrain === "bog_forest" ? 74 : 82;
        const cap = p.isSeedFrontier ? 18 : p.pixelArea > 9000 ? 7 : 3;
        for (const cand of candidates[p.id].sort((a, b) => b[2] - a[2])) {
          if (this.glyphPoints[p.id].length >= cap) break;
          if (this.glyphPoints[p.id].every(([x, y]) =>
              (x - cand[0]) ** 2 + (y - cand[1]) ** 2 >= min ** 2)) {
            this.glyphPoints[p.id].push(cand);
          }
        }
      }
    }

    _addBorder(id, otherIdx, x1, y1, x2, y2) {
      this.borderSegs[id].push([x1, y1, x2, y2]);
      if (otherIdx !== SEA) {
        const otherId = this.mapProvinces[otherIdx].id;
        this.borderSegs[otherId].push([x1, y1, x2, y2]);
      }
    }

    _buildRealmLabels() {
      const groups = new Map();
      for (const p of this.mapProvinces) {
        const g = groups.get(p.controller) || { area: 0, x: 0, y: 0, count: 0 };
        const w = Math.max(1, p.pixelArea);
        g.area += w;
        g.x += p.x * w;
        g.y += p.y * w;
        g.count += 1;
        groups.set(p.controller, g);
      }
      this.realmLabelPoints = [...groups.entries()].map(([fid, g]) => {
        const f = this.factionById.get(fid) || this._fallbackFaction(fid);
        return {
          factionId: fid,
          name: (f.shortName || f.name || fid).toUpperCase(),
          x: g.x / g.area,
          y: g.y / g.area,
          count: g.count,
          area: g.area,
        };
      });
    }

    _fallbackFaction(id) {
      const color = this._colorFromString(id);
      return { id, name: id.replace(/^FAC_/, "").replace(/_/g, " "), shortName: id, color, charge: "peak" };
    }

    _colorFromString(text) {
      let h = 0;
      for (let i = 0; i < text.length; i++) h = (h * 31 + text.charCodeAt(i)) >>> 0;
      const r = 88 + (h & 63), g = 88 + ((h >> 6) & 63), b = 88 + ((h >> 12) & 63);
      return "#" + [r, g, b].map((v) => v.toString(16).padStart(2, "0")).join("");
    }

    _hex(hex) {
      if (!hex || !/^#[0-9a-f]{6}$/i.test(hex)) return [130, 130, 120];
      return [
        parseInt(hex.slice(1, 3), 16),
        parseInt(hex.slice(3, 5), 16),
        parseInt(hex.slice(5, 7), 16),
      ];
    }

    _hash2(x, y) {
      const s = Math.sin(x * 127.1 + y * 311.7) * 43758.5453123;
      return s - Math.floor(s);
    }

    province(id) {
      return this.provinceById.get(id) || this.seedProvinceById.get(id) || null;
    }

    faction(id) {
      return this.factionById.get(id) || this._fallbackFaction(id);
    }

    terrainInfo(id) {
      return TERRAIN_INFO[id] || {
        label: String(id || "unknown").replace(/_/g, " ").replace(/\b\w/g, (m) => m.toUpperCase()),
        base: [120, 120, 90],
      };
    }

    provinceState(province, sim) {
      const id = typeof province === "string" ? province : province.id;
      const p = typeof province === "string" ? this.province(id) : province;
      if (sim && sim.provinceState[id]) return sim.provinceState[id];
      return {
        controller: p ? p.controller : null,
        occupier: null,
        devastation: 0,
        garrison: p ? Math.round(160 + p.fort * 130) : 0,
        pop: p ? Math.max(900, Math.round(2200 + p.value * 120 + p.pixelArea * 0.18)) : 0,
        staticMapProvince: true,
      };
    }

    provinceIdAtPixel(px, py) {
      const idx = this._provinceIndexAtPixel(px, py);
      return idx === SEA ? null : this.mapProvinces[idx].id;
    }

    provinceAt(worldX, worldY) {
      if (this.layerStatus !== "ready") return super.provinceAt(worldX, worldY);
      const px = Math.floor(worldX / this.W * this.provinceMapWidth);
      const py = Math.floor(worldY / this.H * this.provinceMapHeight);
      const id = this.provinceIdAtPixel(px, py);
      return id ? this.provinceById.get(id) : null;
    }

    _biomeColor(prov, height, slope) {
      const info = this.terrainInfo(prov && prov.terrain);
      let rgb = info.base.slice();
      const tint = REGION_TINTS[prov && prov.region] || [0, 0, 0];
      rgb = [rgb[0] + tint[0], rgb[1] + tint[1], rgb[2] + tint[2]];

      if (prov && prov.terrain === "bog_forest") {
        rgb = [rgb[0] * 0.78, rgb[1] * 0.92, rgb[2] * 0.78];
      } else if (prov && prov.terrain === "grain_estate") {
        rgb = [rgb[0] * 1.05 + 8, rgb[1] * 1.05 + 6, rgb[2] * 0.90];
      } else if (prov && (prov.terrain === "dryland_plateau" || prov.terrain === "oasis_salt_road")) {
        rgb = [rgb[0] * 1.08 + 10, rgb[1] * 0.99, rgb[2] * 0.82];
      }

      if (height > 0.68 || slope > 0.22) {
        const rock = Math.min(0.52, Math.max(0, (height - 0.62) * 1.45 + slope * 0.65));
        rgb = [
          rgb[0] * (1 - rock) + 142 * rock,
          rgb[1] * (1 - rock) + 137 * rock,
          rgb[2] * (1 - rock) + 127 * rock,
        ];
      }
      if (height > 0.86) {
        const snow = Math.min(0.55, (height - 0.86) * 3.4);
        rgb = [
          rgb[0] * (1 - snow) + 226 * snow,
          rgb[1] * (1 - snow) + 226 * snow,
          rgb[2] * (1 - snow) + 218 * snow,
        ];
      }
      return rgb;
    }

    _paintWorld(sim) {
      if (this.layerStatus !== "ready") return super._paintWorld(sim);
      if (!this._image) {
        this._image = document.createElement("canvas");
        this._image.width = RENDER_W;
        this._image.height = RENDER_H;
      }
      const ictx = this._image.getContext("2d");
      const img = ictx.createImageData(RENDER_W, RENDER_H);
      const data = img.data;
      const factionRGB = {}, cultureRGB = {}, religionRGB = {};
      for (const [fid, f] of this.factionById) {
        factionRGB[fid] = this._hex(f.color);
        cultureRGB[fid] = this._hex(this.seed.cultureColors[f.culture] || "#8f8970");
        religionRGB[fid] = this._hex(this.seed.religionColors[f.religion] || "#888070");
      }

      for (let y = 0; y < RENDER_H; y++) {
        for (let x = 0; x < RENDER_W; x++) {
          const i = y * RENDER_W + x;
          const off = i * 4;
          const idx = this._renderProvinceIndex[i];
          const h = this._renderHeight[i];
          const slope = this._renderSlope[i];
          const wx = x / RENDER_W * this.W, wy = y / RENDER_H * this.H;
          const grain = (this.noise.fbm(wx * 0.010, wy * 0.010, 3) - 0.5) * 18;
          let rgb;

          if (idx === SEA) {
            const shelf = Math.max(0, 1 - Math.min(1, this.coastDistance[i] / 38));
            const depth = Math.max(0, 0.55 - h);
            rgb = [
              28 + shelf * 44 - depth * 10 + grain * 0.6,
              47 + shelf * 57 - depth * 6 + grain * 0.6,
              72 + shelf * 61 + grain * 0.7,
            ];
            if (this.coastDistance[i] <= 2) {
              rgb = [rgb[0] * 0.68 + 154 * 0.32, rgb[1] * 0.68 + 187 * 0.32, rgb[2] * 0.68 + 184 * 0.32];
            }
          } else {
            const prov = this.mapProvinces[idx];
            const state = this.provinceState(prov, sim);
            const controller = state.controller || prov.controller;
            rgb = this._biomeColor(prov, h, slope);
            let tint = factionRGB[controller] || this._hex(this.faction(controller).color);
            let mix = 0.34;
            if (this.mapMode === "culture") {
              tint = cultureRGB[controller] || tint;
              mix = 0.42;
            } else if (this.mapMode === "religion") {
              tint = religionRGB[controller] || tint;
              mix = 0.42;
            } else if (this.mapMode === "terrain") {
              mix = 0;
            } else if (this.mapMode === "devastation") {
              const d = Math.min(1, (state.devastation || 0) / 80);
              tint = [140, 47, 34];
              mix = 0.08 + d * 0.64;
            }
            rgb = [
              rgb[0] * (1 - mix) + tint[0] * mix,
              rgb[1] * (1 - mix) + tint[1] * mix,
              rgb[2] * (1 - mix) + tint[2] * mix,
            ];

            if (this.mapMode === "political" && state.occupier &&
                state.occupier !== controller && ((x + y) % 8) < 4) {
              const occ = factionRGB[state.occupier] || [200, 200, 200];
              rgb = [rgb[0] * 0.35 + occ[0] * 0.65, rgb[1] * 0.35 + occ[1] * 0.65, rgb[2] * 0.35 + occ[2] * 0.65];
            }

            const shade = this._renderShade[i] + grain / 255;
            rgb = [rgb[0] * shade, rgb[1] * shade, rgb[2] * shade];

            let border = false, realmBorder = false;
            for (let d = 0; d < 4; d++) {
              const nx = x + [1, -1, 0, 0][d], ny = y + [0, 0, 1, -1][d];
              if (nx < 0 || ny < 0 || nx >= RENDER_W || ny >= RENDER_H) continue;
              const nIdx = this._renderProvinceIndex[ny * RENDER_W + nx];
              if (nIdx !== idx) {
                border = true;
                if (nIdx !== SEA) {
                  const np = this.mapProvinces[nIdx];
                  const ns = this.provinceState(np, sim);
                  if ((ns.controller || np.controller) !== controller) realmBorder = true;
                }
              }
            }
            if (realmBorder) rgb = rgb.map((v) => v * 0.43);
            else if (border) rgb = rgb.map((v) => v * 0.72);
          }

          data[off] = Math.max(0, Math.min(255, rgb[0]));
          data[off + 1] = Math.max(0, Math.min(255, rgb[1]));
          data[off + 2] = Math.max(0, Math.min(255, rgb[2]));
          data[off + 3] = 255;
        }
      }
      ictx.putImageData(img, 0, 0);
      this._dirty = false;
    }

    render(sim) {
      if (this.layerStatus !== "ready") return super.render(sim);
      if (this._dirty) this._paintWorld(sim);
      const ctx = this.ctx;
      const { width, height } = this.canvas;
      ctx.save();
      ctx.fillStyle = "#1f2d36";
      ctx.fillRect(0, 0, width, height);

      const tl = this.worldToScreen(0, 0);
      const z = tl.z;
      ctx.imageSmoothingEnabled = true;
      ctx.imageSmoothingQuality = "high";
      ctx.drawImage(this._image, tl.x, tl.y, this.W * z, this.H * z);

      this._drawFrontierWaterlines(ctx, z);
      this._drawTerrainGlyphs(ctx, z);
      this._drawSelectedOutline(ctx, z);
      this._drawProvinceLabels(ctx, z);
      if (this.mapMode === "political") this._drawRealmLabels(ctx, z);
      ctx.restore();
    }

    _drawFrontierWaterlines(ctx, z) {
      const paths = [
        ["PROV_RED_BOG", "PROV_ROV_HALEM", "PROV_SEVRIN_CANAL", "PROV_BLUE_CHAIN"],
        ["PROV_NINTH_BANNER", "PROV_ROV_HALEM", "PROV_THIRD_CHARTER"],
      ];
      ctx.save();
      ctx.lineCap = "round";
      ctx.lineJoin = "round";
      for (const ids of paths) {
        const pts = ids.map((id) => this.provinceById.get(id)).filter(Boolean);
        if (pts.length < 2) continue;
        ctx.beginPath();
        pts.forEach((p, i) => {
          const pt = this.worldToScreen(p.x, p.y);
          if (i === 0) ctx.moveTo(pt.x, pt.y);
          else ctx.lineTo(pt.x, pt.y);
        });
        ctx.strokeStyle = "rgba(54, 93, 125, 0.58)";
        ctx.lineWidth = Math.max(1.2, 2.2 * z);
        ctx.stroke();
        ctx.strokeStyle = "rgba(132, 178, 185, 0.35)";
        ctx.lineWidth = Math.max(0.7, 0.9 * z);
        ctx.stroke();
      }
      ctx.restore();
    }

    _drawTerrainGlyphs(ctx, z) {
      if (this.view.zoom < 0.75) return;
      ctx.save();
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.font = `${Math.max(8, 13 * z)}px Georgia, serif`;
      ctx.fillStyle = "rgba(22, 18, 10, 0.28)";
      for (const p of this.mapProvinces) {
        const glyph = TERRAIN_GLYPHS[p.terrain];
        if (!glyph) continue;
        if (!p.isSeedFrontier && this.view.zoom < 1.35 && p.value < 88) continue;
        for (const [gx, gy] of this.glyphPoints[p.id] || []) {
          const pt = this.worldToScreen(gx, gy);
          if (pt.x < -20 || pt.y < -20 || pt.x > this.canvas.width + 20 || pt.y > this.canvas.height + 20) continue;
          ctx.fillText(glyph, pt.x, pt.y);
        }
      }
      ctx.restore();
    }

    _drawSelectedOutline(ctx, z) {
      if (!this.selected || !this.borderSegs[this.selected]) return;
      ctx.save();
      ctx.strokeStyle = "rgba(238, 214, 140, 0.96)";
      ctx.lineWidth = Math.max(1.5, 2.7 * z);
      ctx.beginPath();
      for (const [x1, y1, x2, y2] of this.borderSegs[this.selected]) {
        const a = this.worldToScreen(x1, y1), b = this.worldToScreen(x2, y2);
        ctx.moveTo(a.x, a.y);
        ctx.lineTo(b.x, b.y);
      }
      ctx.stroke();
      ctx.restore();
    }

    _drawProvinceLabels(ctx, z) {
      ctx.save();
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      for (const p of this.mapProvinces) {
        const seed = p.isSeedFrontier || this.seedProvinceIds.has(p.id);
        const selected = this.selected === p.id;
        const major = p.value >= 90 || p.pixelArea > 9500;
        if (!seed && !selected && !(this.view.zoom > 1.35 && major) &&
            !(this.view.zoom > 2.25 && p.pixelArea > 3200)) continue;
        const pt = this.worldToScreen(p.x, p.y);
        if (pt.x < -90 || pt.y < -30 || pt.x > this.canvas.width + 90 || pt.y > this.canvas.height + 30) continue;
        const size = seed || selected ? Math.max(9, 15 * z) : Math.max(7, 10.5 * z);
        ctx.font = `${seed || selected ? 700 : 600} ${size}px 'Iowan Old Style', 'Palatino Linotype', Georgia, serif`;
        ctx.fillStyle = seed || selected ? "rgba(24, 18, 8, 0.90)" : "rgba(24, 18, 8, 0.70)";
        ctx.strokeStyle = "rgba(244, 232, 200, 0.58)";
        ctx.lineWidth = seed || selected ? 3 : 2;
        const label = p.name.toUpperCase();
        ctx.save();
        ctx.letterSpacing = `${seed ? 1.4 * z : 0.8 * z}px`;
        ctx.strokeText(label, pt.x, pt.y + (seed ? 24 : 16) * z);
        ctx.fillText(label, pt.x, pt.y + (seed ? 24 : 16) * z);
        ctx.restore();
      }
      ctx.restore();
    }

    _drawRealmLabels(ctx, z) {
      ctx.save();
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      for (const r of this.realmLabelPoints) {
        if (r.count < 6 && this.view.zoom > 1.25) continue;
        if (r.count < 2 && this.view.zoom <= 1.25) continue;
        const pt = this.worldToScreen(r.x, r.y);
        if (pt.x < -180 || pt.y < -60 || pt.x > this.canvas.width + 180 || pt.y > this.canvas.height + 60) continue;
        const size = Math.max(12, Math.min(34, (12 + Math.sqrt(r.count) * 3.5) * z));
        ctx.font = `700 italic ${size}px 'Iowan Old Style', 'Palatino Linotype', Georgia, serif`;
        ctx.save();
        ctx.letterSpacing = `${Math.max(1, 4 * z)}px`;
        ctx.globalAlpha = 0.48;
        ctx.strokeStyle = "rgba(12, 9, 4, 0.88)";
        ctx.lineWidth = Math.max(2, 3.2 * z);
        ctx.fillStyle = "rgba(246, 233, 198, 0.92)";
        ctx.strokeText(r.name, pt.x, pt.y);
        ctx.fillText(r.name, pt.x, pt.y);
        ctx.restore();
      }
      ctx.restore();
    }

    setMode(mode) {
      this.mapMode = mode;
      this.markDirty();
    }
  }

  window.WG = window.WG || {};
  window.WG.LayeredWorldMap = LayeredWorldMap;
  window.WG.WORLD_TERRAIN_INFO = TERRAIN_INFO;
})();

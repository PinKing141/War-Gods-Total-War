import { RiverEditor } from "./river_editor.js";
import { RiverExporter } from "./river_exporter.js";
import { HydrologySimulator } from "./hydrology_simulator.js";
import { RiverValidator } from "./river_validator.js";

const MAP_SIZE = { width: 3072, height: 2048 };
const PREVIEW_SCALE = 2;
const SIMULATOR_DEFAULTS = {
  minFlow: 18,
  maxRivers: 40,
  gridStep: 16,
  smoothing: 1,
  minLength: 140,
  sourceSpacing: 90,
  pointDensity: 1,
  seed: 1,
};
const ASSETS = {
  terrain: "../../assets/terrain_masks/previews/terrain_masks_combined_preview_3072x2048.png",
  heightmap: "../../assets/heightmaps/world_heightmap_3072x2048_16bit.png",
  province: "../../assets/provinces/world_provinces_unique_rgb_3072x2048.png",
  definitions: "../../assets/provinces/world_province_definitions.csv",
  adjacency: "../../assets/provinces/world_province_adjacency.csv",
  riverPaths: "../../assets/rivers/river_paths.json",
};

const MASK_URLS = {
  water: "../../assets/terrain_masks/masks_3072x2048/water_mask.png",
  land: "../../assets/terrain_masks/masks_3072x2048/land_mask.png",
  mountain: "../../assets/terrain_masks/masks_3072x2048/mountain_mask.png",
  highland: "../../assets/terrain_masks/masks_3072x2048/highland_mask.png",
  lowland: "../../assets/terrain_masks/masks_3072x2048/lowland_mask.png",
  fertile_lowland: "../../assets/terrain_masks/masks_3072x2048/fertile_lowland_mask.png",
  forest: "../../assets/terrain_masks/masks_3072x2048/forest_mask.png",
  marsh: "../../assets/terrain_masks/masks_3072x2048/marsh_mask.png",
  farmland: "../../assets/terrain_masks/masks_3072x2048/farmland_mask.png",
  dryland: "../../assets/terrain_masks/masks_3072x2048/dryland_mask.png",
  steppe: "../../assets/terrain_masks/masks_3072x2048/steppe_mask.png",
  oasis_wetland: "../../assets/terrain_masks/masks_3072x2048/oasis_wetland_mask.png",
  bare_rock: "../../assets/terrain_masks/masks_3072x2048/bare_rock_mask.png",
  snow_peak: "../../assets/terrain_masks/masks_3072x2048/snow_peak_mask.png",
  coast: "../../assets/terrain_masks/masks_3072x2048/coast_mask.png",
  pass: "../../assets/terrain_masks/masks_3072x2048/pass_mask.png",
};

const MASK_COLORS = {
  water: [82, 164, 208],
  land: [180, 160, 92],
  mountain: [214, 208, 188],
  lowland: [152, 199, 88],
  marsh: [76, 185, 151],
  farmland: [185, 211, 84],
};

class RiverWorkbench {
  constructor() {
    this.canvas = document.getElementById("river-canvas");
    this.ctx = this.canvas.getContext("2d");
    this.statusEl = document.getElementById("status");
    this.cursorEl = document.getElementById("cursor-readout");
    this.selectionEl = document.getElementById("selection-readout");
    this.form = document.getElementById("river-form");
    this.validationEl = document.getElementById("validation-list");
    this.metricsEl = document.getElementById("river-metrics");
    this.simReportEl = document.getElementById("sim-report");

    this.images = {};
    this.maskData = {};
    this.maskOverlays = {};
    this.overlayLayers = new Set();
    this.overlayCanvases = {};
    this.heightData = null;
    this.provinceRgba = null;
    this.provinceColorToId = new Map();
    this.provinceIds = new Set();
    this.existingRiverPaths = null;
    this.simulator = null;
    this.lastSimulation = null;
    this.baseLayer = "terrain";
    this.activeMasks = new Set();
    this.view = { x: MAP_SIZE.width / 2, y: MAP_SIZE.height / 2, scale: 0.3 };
    this.drag = null;
    this.pendingRender = false;
    this.updatingForm = false;

    this.editor = new RiverEditor({ mapSize: MAP_SIZE });
    this.exporter = new RiverExporter({
      mapSize: MAP_SIZE,
      widthForRiver: (river) => this.editor.widthForRiver(river),
    });
    this.validator = null;
    this.editor.onChange = () => this.onEditorChange();
  }

  async init() {
    this.bindControls();
    this.resize();
    window.addEventListener("resize", () => this.resize());
    await this.loadAssets();
    this.simulator = new HydrologySimulator({
      mapSize: MAP_SIZE,
      heightData: this.heightData,
      masks: this.maskData,
      provinceIdAt: (x, y) => this.provinceIdAt(x, y),
    });
    this.validator = new RiverValidator({
      mapSize: MAP_SIZE,
      provinceIds: this.provinceIds,
      heightAt: (x, y) => this.heightAt(x, y),
      waterAt: (x, y) => this.maskAt("water", x, y),
    });
    this.setStatus("Assets loaded. Manual editor ready.");
    this.onEditorChange();
    this.render();
  }

  bindControls() {
    document.querySelectorAll("[name='base-layer']").forEach((input) => {
      input.addEventListener("change", () => {
        this.baseLayer = input.value;
        this.requestRender();
      });
    });
    document.querySelectorAll("[data-mask-layer]").forEach((input) => {
      input.addEventListener("change", () => {
        if (input.checked) this.activeMasks.add(input.dataset.maskLayer);
        else this.activeMasks.delete(input.dataset.maskLayer);
        this.requestRender();
      });
    });
    document.querySelectorAll("[data-overlay-layer]").forEach((input) => {
      input.addEventListener("change", () => {
        if (input.checked) this.overlayLayers.add(input.dataset.overlayLayer);
        else this.overlayLayers.delete(input.dataset.overlayLayer);
        this.requestRender();
      });
    });
    document.getElementById("tool-buttons").addEventListener("click", (event) => {
      const button = event.target.closest("[data-tool]");
      if (!button) return;
      this.editor.setTool(button.dataset.tool);
      this.syncToolButtons();
    });
    document.getElementById("btn-new-river").addEventListener("click", () => this.editor.createRiver());
    document.getElementById("btn-delete-river").addEventListener("click", () => this.editor.deleteSelectedRiver());
    document.getElementById("btn-reverse-river").addEventListener("click", () => this.editor.reverseSelectedRiver());
    document.getElementById("btn-add-river-points").addEventListener("click", () => this.addMorePointsToSelectedRiver());
    document.getElementById("btn-load-existing").addEventListener("click", () => this.loadExistingRivers());
    document.getElementById("btn-run-simulator").addEventListener("click", () => this.runSimulator());
    document.getElementById("btn-randomize-simulator").addEventListener("click", () => this.randomizeSimulator());
    document.getElementById("btn-reset-simulator").addEventListener("click", () => this.resetSimulatorSettings());
    document.getElementById("btn-clear-simulation").addEventListener("click", () => this.clearSimulation());
    document.getElementById("btn-save-project").addEventListener("click", () => this.exporter.exportProject(this.editor));
    document.getElementById("btn-load-project").addEventListener("click", () => document.getElementById("project-file").click());
    document.getElementById("project-file").addEventListener("change", (event) => this.loadProjectFile(event));
    document.getElementById("btn-export-paths").addEventListener("click", () => this.exporter.exportRiverPaths(this.editor.rivers));
    document.getElementById("btn-export-csv").addEventListener("click", () => this.exporter.exportWaterwaysCsv(this.editor.rivers));
    document.getElementById("btn-export-masks").addEventListener("click", () => this.exporter.exportAllMasks(this.editor.rivers));

    this.form.addEventListener("input", () => this.updateRiverFromForm());
    this.form.addEventListener("change", () => this.updateRiverFromForm());
    this.canvas.addEventListener("pointerdown", (event) => this.onPointerDown(event));
    this.canvas.addEventListener("pointermove", (event) => this.onPointerMove(event));
    this.canvas.addEventListener("pointerup", () => this.endDrag());
    this.canvas.addEventListener("pointercancel", () => this.endDrag());
    this.canvas.addEventListener("wheel", (event) => this.onWheel(event), { passive: false });
  }

  async loadAssets() {
    const [terrain, heightmap, province, definitionsText, existing] = await Promise.all([
      this.loadImage(ASSETS.terrain),
      this.loadImage(ASSETS.heightmap),
      this.loadImage(ASSETS.province),
      fetch(ASSETS.definitions).then((response) => response.text()),
      this.loadOptionalJson(ASSETS.riverPaths),
      fetch(ASSETS.adjacency).catch(() => null),
    ]);
    this.images.terrain = terrain;
    this.images.heightmap = heightmap;
    this.images.province = province;
    this.existingRiverPaths = existing;
    this.buildProvinceLookup(definitionsText, province);
    this.heightData = this.grayscaleDataFromImage(heightmap);

    const maskEntries = await Promise.all(Object.entries(MASK_URLS).map(async ([name, url]) => [
      name,
      await this.loadImage(url),
    ]));
    for (const [name, image] of maskEntries) {
      this.images[name] = image;
      this.maskData[name] = this.grayscaleDataFromImage(image);
    }
    this.images["height-relief"] = this.buildHeightReliefCanvas();
    this.overlayCanvases["height-contours"] = this.buildHeightContourOverlay();
  }

  loadImage(src) {
    return new Promise((resolve, reject) => {
      const image = new Image();
      image.onload = () => resolve(image);
      image.onerror = () => reject(new Error(`Could not load ${src}`));
      image.src = src;
    });
  }

  async loadOptionalJson(src) {
    try {
      const response = await fetch(src);
      if (!response.ok) return null;
      return await response.json();
    } catch (_) {
      return null;
    }
  }

  grayscaleDataFromImage(image) {
    const canvas = document.createElement("canvas");
    canvas.width = MAP_SIZE.width;
    canvas.height = MAP_SIZE.height;
    const ctx = canvas.getContext("2d", { willReadFrequently: true });
    ctx.drawImage(image, 0, 0, MAP_SIZE.width, MAP_SIZE.height);
    const rgba = ctx.getImageData(0, 0, MAP_SIZE.width, MAP_SIZE.height).data;
    const out = new Uint8Array(MAP_SIZE.width * MAP_SIZE.height);
    for (let i = 0; i < out.length; i++) out[i] = rgba[i * 4];
    return out;
  }

  rgbaDataFromImage(image) {
    const canvas = document.createElement("canvas");
    canvas.width = MAP_SIZE.width;
    canvas.height = MAP_SIZE.height;
    const ctx = canvas.getContext("2d", { willReadFrequently: true });
    ctx.drawImage(image, 0, 0, MAP_SIZE.width, MAP_SIZE.height);
    return ctx.getImageData(0, 0, MAP_SIZE.width, MAP_SIZE.height).data;
  }

  buildHeightReliefCanvas() {
    const canvas = document.createElement("canvas");
    const width = Math.floor(MAP_SIZE.width / PREVIEW_SCALE);
    const height = Math.floor(MAP_SIZE.height / PREVIEW_SCALE);
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext("2d");
    const image = ctx.createImageData(width, height);
    const water = this.maskData.water;
    const land = this.maskData.land;

    for (let y = 0; y < height; y++) {
      const sy = Math.min(MAP_SIZE.height - 1, y * PREVIEW_SCALE);
      const row = sy * MAP_SIZE.width;
      const rowUp = Math.max(0, sy - PREVIEW_SCALE) * MAP_SIZE.width;
      const rowDown = Math.min(MAP_SIZE.height - 1, sy + PREVIEW_SCALE) * MAP_SIZE.width;
      for (let x = 0; x < width; x++) {
        const sx = Math.min(MAP_SIZE.width - 1, x * PREVIEW_SCALE);
        const sourceIndex = row + sx;
        const left = this.heightData[row + Math.max(0, sx - PREVIEW_SCALE)] / 255;
        const right = this.heightData[row + Math.min(MAP_SIZE.width - 1, sx + PREVIEW_SCALE)] / 255;
        const up = this.heightData[rowUp + sx] / 255;
        const down = this.heightData[rowDown + sx] / 255;
        const heightValue = this.heightData[sourceIndex] / 255;
        const shade = this.clamp(0.72 + (left - right) * 2.4 + (up - down) * 1.9, 0.38, 1.22);
        const waterValue = water ? water[sourceIndex] / 255 : 0;
        const landValue = land ? land[sourceIndex] / 255 : 1;
        const color = waterValue > 0.36 || landValue < 0.30
          ? this.heightWaterColor(heightValue, waterValue)
          : this.heightLandColor(heightValue);
        const off = (y * width + x) * 4;
        image.data[off] = this.clamp(Math.round(color[0] * shade), 0, 255);
        image.data[off + 1] = this.clamp(Math.round(color[1] * shade), 0, 255);
        image.data[off + 2] = this.clamp(Math.round(color[2] * shade), 0, 255);
        image.data[off + 3] = 255;
      }
    }

    ctx.putImageData(image, 0, 0);
    return canvas;
  }

  buildHeightContourOverlay() {
    const canvas = document.createElement("canvas");
    const width = Math.floor(MAP_SIZE.width / PREVIEW_SCALE);
    const height = Math.floor(MAP_SIZE.height / PREVIEW_SCALE);
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext("2d");
    const image = ctx.createImageData(width, height);
    const interval = 12;
    const water = this.maskData.water;

    for (let y = 0; y < height - 1; y++) {
      const sy = Math.min(MAP_SIZE.height - 1, y * PREVIEW_SCALE);
      const row = sy * MAP_SIZE.width;
      for (let x = 0; x < width - 1; x++) {
        const sx = Math.min(MAP_SIZE.width - 1, x * PREVIEW_SCALE);
        const sourceIndex = row + sx;
        if (water && water[sourceIndex] > 96) continue;
        const heightValue = this.heightData[sourceIndex];
        const contour = Math.floor(heightValue / interval);
        const east = row + Math.min(MAP_SIZE.width - 1, sx + PREVIEW_SCALE);
        const south = Math.min(MAP_SIZE.height - 1, sy + PREVIEW_SCALE) * MAP_SIZE.width + sx;
        if (contour === Math.floor(this.heightData[east] / interval) && contour === Math.floor(this.heightData[south] / interval)) continue;
        const major = contour % 4 === 0;
        const off = (y * width + x) * 4;
        image.data[off] = major ? 255 : 230;
        image.data[off + 1] = major ? 218 : 185;
        image.data[off + 2] = major ? 124 : 100;
        image.data[off + 3] = major ? 118 : 72;
      }
    }

    ctx.putImageData(image, 0, 0);
    return canvas;
  }

  heightLandColor(height) {
    if (height < 0.24) return this.lerpColor([69, 95, 58], [109, 132, 72], height / 0.24);
    if (height < 0.48) return this.lerpColor([109, 132, 72], [139, 123, 80], (height - 0.24) / 0.24);
    if (height < 0.70) return this.lerpColor([139, 123, 80], [154, 149, 132], (height - 0.48) / 0.22);
    if (height < 0.86) return this.lerpColor([154, 149, 132], [197, 196, 184], (height - 0.70) / 0.16);
    return this.lerpColor([197, 196, 184], [244, 244, 235], (height - 0.86) / 0.14);
  }

  heightWaterColor(height, waterValue) {
    return this.lerpColor([17, 44, 74], [52, 103, 135], this.clamp(height * 0.9 + waterValue * 0.18, 0, 1));
  }

  lerpColor(a, b, t) {
    const f = this.clamp(t, 0, 1);
    return [
      a[0] + (b[0] - a[0]) * f,
      a[1] + (b[1] - a[1]) * f,
      a[2] + (b[2] - a[2]) * f,
    ];
  }

  buildProvinceLookup(definitionsText, provinceImage) {
    const rows = this.parseCsv(definitionsText);
    const header = (rows.shift() || []).map((item) => item.replace(/^\ufeff/, ""));
    const idx = Object.fromEntries(header.map((name, index) => [name, index]));
    this.provinceIds = new Set();
    this.provinceColorToId = new Map();
    for (const row of rows) {
      const id = row[idx.province_id] || row[1];
      if (!id) continue;
      this.provinceIds.add(id);
      const red = Number(row[idx.red]);
      const green = Number(row[idx.green]);
      const blue = Number(row[idx.blue]);
      if (Number.isFinite(red) && Number.isFinite(green) && Number.isFinite(blue)) {
        this.provinceColorToId.set((red << 16) | (green << 8) | blue, id);
      }
    }
    this.provinceRgba = this.rgbaDataFromImage(provinceImage);
  }

  parseCsv(text) {
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
        if (row.some((item) => item !== "")) rows.push(row);
        row = [];
        field = "";
      } else {
        field += ch;
      }
    }
    row.push(field);
    if (row.some((item) => item !== "")) rows.push(row);
    if (rows[0]) rows[0][0] = rows[0][0].replace(/^\ufeff/, "");
    return rows;
  }

  resize() {
    const rect = this.canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    this.canvas.width = Math.max(1, Math.floor(rect.width * dpr));
    this.canvas.height = Math.max(1, Math.floor(rect.height * dpr));
    if (!this.didFit) {
      this.fitView();
      this.didFit = true;
    }
    this.requestRender();
  }

  fitView() {
    const fit = Math.min(this.canvas.width / MAP_SIZE.width, this.canvas.height / MAP_SIZE.height) * 0.96;
    this.view = { x: MAP_SIZE.width / 2, y: MAP_SIZE.height / 2, scale: fit || 0.3 };
  }

  render() {
    this.pendingRender = false;
    const ctx = this.ctx;
    ctx.fillStyle = "#101820";
    ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
    this.drawBaseLayer(ctx);
    this.drawMaskLayers(ctx);
    this.drawOverlayLayers(ctx);
    this.drawRivers(ctx);
  }

  drawBaseLayer(ctx) {
    const image = this.images[this.baseLayer] || this.images.terrain;
    if (!image) return;
    const a = this.worldToScreen(0, 0);
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = "high";
    ctx.drawImage(image, a.x, a.y, MAP_SIZE.width * this.view.scale, MAP_SIZE.height * this.view.scale);
  }

  drawMaskLayers(ctx) {
    for (const name of this.activeMasks) {
      const overlay = this.maskOverlays[name] || this.buildMaskOverlay(name);
      if (!overlay) continue;
      this.maskOverlays[name] = overlay;
      const a = this.worldToScreen(0, 0);
      ctx.drawImage(overlay, a.x, a.y, MAP_SIZE.width * this.view.scale, MAP_SIZE.height * this.view.scale);
    }
  }

  drawOverlayLayers(ctx) {
    for (const name of this.overlayLayers) {
      const overlay = this.overlayCanvases[name];
      if (!overlay) continue;
      const a = this.worldToScreen(0, 0);
      ctx.drawImage(overlay, a.x, a.y, MAP_SIZE.width * this.view.scale, MAP_SIZE.height * this.view.scale);
    }
  }

  buildMaskOverlay(name) {
    const mask = this.maskData[name];
    const color = MASK_COLORS[name];
    if (!mask || !color) return null;
    const canvas = document.createElement("canvas");
    canvas.width = MAP_SIZE.width;
    canvas.height = MAP_SIZE.height;
    const ctx = canvas.getContext("2d");
    const image = ctx.createImageData(MAP_SIZE.width, MAP_SIZE.height);
    for (let i = 0; i < mask.length; i++) {
      const off = i * 4;
      image.data[off] = color[0];
      image.data[off + 1] = color[1];
      image.data[off + 2] = color[2];
      image.data[off + 3] = Math.round(Math.pow(mask[i] / 255, 0.85) * 178);
    }
    ctx.putImageData(image, 0, 0);
    return canvas;
  }

  drawRivers(ctx) {
    for (const river of this.editor.rivers) {
      const selected = river.id === this.editor.selectedRiverId;
      this.drawRiverPath(ctx, river, selected);
      this.drawRiverPoints(ctx, river, selected);
    }
  }

  drawRiverPath(ctx, river, selected) {
    if (!river.points || river.points.length < 2) return;
    ctx.save();
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.strokeStyle = selected ? "rgba(246, 214, 112, 0.98)" : "rgba(80, 177, 224, 0.92)";
    ctx.lineWidth = Math.max(2, this.editor.widthForRiver(river) * this.view.scale);
    ctx.shadowColor = "rgba(0,0,0,0.55)";
    ctx.shadowBlur = selected ? 7 : 4;
    ctx.beginPath();
    river.points.forEach(([x, y], index) => {
      const pt = this.worldToScreen(x, y);
      if (index === 0) ctx.moveTo(pt.x, pt.y);
      else ctx.lineTo(pt.x, pt.y);
    });
    ctx.stroke();
    ctx.restore();
  }

  drawRiverPoints(ctx, river, selected) {
    if (!selected) return;
    river.points.forEach(([x, y], index) => {
      const pt = this.worldToScreen(x, y);
      const active = index === this.editor.selectedPointIndex;
      ctx.save();
      ctx.beginPath();
      ctx.arc(pt.x, pt.y, active ? 6 : 4.5, 0, Math.PI * 2);
      ctx.fillStyle = active ? "#f6d670" : "#eff5ff";
      ctx.strokeStyle = "#1a1207";
      ctx.lineWidth = 2;
      ctx.fill();
      ctx.stroke();
      ctx.restore();
    });
  }

  onPointerDown(event) {
    this.canvas.setPointerCapture(event.pointerId);
    const world = this.eventToWorld(event);
    if (event.button !== 0) {
      this.drag = { type: "pan", sx: event.clientX, sy: event.clientY, x: this.view.x, y: this.view.y };
      return;
    }

    if (this.editor.tool === "add-point") {
      this.editor.addPoint([world.x, world.y]);
      return;
    }

    const hitPoint = this.findPointNear(event);
    if (this.editor.tool === "delete-point") {
      if (hitPoint) this.editor.deletePoint(hitPoint.river.id, hitPoint.index);
      return;
    }

    if (hitPoint) {
      this.editor.selectRiver(hitPoint.river.id, hitPoint.index);
      this.drag = { type: "point", riverId: hitPoint.river.id, index: hitPoint.index };
      return;
    }

    const hitRiver = this.findRiverNear(event);
    if (hitRiver) {
      this.editor.selectRiver(hitRiver.id);
    } else {
      this.drag = { type: "pan", sx: event.clientX, sy: event.clientY, x: this.view.x, y: this.view.y };
    }
  }

  onPointerMove(event) {
    const world = this.eventToWorld(event);
    const elevation = this.heightAt(world.x, world.y);
    const water = this.maskAt("water", world.x, world.y);
    this.cursorEl.textContent = `x ${Math.round(world.x)}, y ${Math.round(world.y)}, h ${elevation.toFixed(3)}${water > 0.32 ? ", water" : ""}`;
    if (!this.drag) return;
    if (this.drag.type === "point") {
      this.editor.selectedRiverId = this.drag.riverId;
      this.editor.selectedPointIndex = this.drag.index;
      this.editor.moveSelectedPoint([world.x, world.y]);
    } else if (this.drag.type === "pan") {
      const dpr = window.devicePixelRatio || 1;
      this.view.x = this.drag.x - (event.clientX - this.drag.sx) * dpr / this.view.scale;
      this.view.y = this.drag.y - (event.clientY - this.drag.sy) * dpr / this.view.scale;
      this.requestRender();
    }
  }

  onWheel(event) {
    event.preventDefault();
    const before = this.eventToWorld(event);
    const factor = event.deltaY < 0 ? 1.12 : 1 / 1.12;
    this.view.scale = Math.max(0.08, Math.min(3.2, this.view.scale * factor));
    const rect = this.canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    const sx = (event.clientX - rect.left) * dpr;
    const sy = (event.clientY - rect.top) * dpr;
    this.view.x = before.x - (sx - this.canvas.width / 2) / this.view.scale;
    this.view.y = before.y - (sy - this.canvas.height / 2) / this.view.scale;
    this.requestRender();
  }

  endDrag() {
    this.drag = null;
  }

  eventToWorld(event) {
    const rect = this.canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    const sx = (event.clientX - rect.left) * dpr;
    const sy = (event.clientY - rect.top) * dpr;
    return this.screenToWorld(sx, sy);
  }

  worldToScreen(x, y) {
    return {
      x: (x - this.view.x) * this.view.scale + this.canvas.width / 2,
      y: (y - this.view.y) * this.view.scale + this.canvas.height / 2,
    };
  }

  screenToWorld(x, y) {
    return {
      x: (x - this.canvas.width / 2) / this.view.scale + this.view.x,
      y: (y - this.canvas.height / 2) / this.view.scale + this.view.y,
    };
  }

  findPointNear(event) {
    const threshold = 11 * (window.devicePixelRatio || 1);
    let best = null;
    for (const river of this.editor.rivers) {
      river.points.forEach(([x, y], index) => {
        const pt = this.worldToScreen(x, y);
        const pos = this.eventToScreen(event);
        const dist = Math.hypot(pt.x - pos.x, pt.y - pos.y);
        if (dist <= threshold && (!best || dist < best.dist)) best = { river, index, dist };
      });
    }
    return best;
  }

  findRiverNear(event) {
    const pos = this.eventToScreen(event);
    const threshold = 10 * (window.devicePixelRatio || 1);
    let best = null;
    for (const river of this.editor.rivers) {
      for (let i = 1; i < river.points.length; i++) {
        const a = this.worldToScreen(river.points[i - 1][0], river.points[i - 1][1]);
        const b = this.worldToScreen(river.points[i][0], river.points[i][1]);
        const dist = this.distanceToSegment(pos, a, b);
        if (dist <= threshold && (!best || dist < best.dist)) best = { river, dist };
      }
    }
    return best && best.river;
  }

  eventToScreen(event) {
    const rect = this.canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    return { x: (event.clientX - rect.left) * dpr, y: (event.clientY - rect.top) * dpr };
  }

  distanceToSegment(p, a, b) {
    const dx = b.x - a.x;
    const dy = b.y - a.y;
    if (dx === 0 && dy === 0) return Math.hypot(p.x - a.x, p.y - a.y);
    const t = Math.max(0, Math.min(1, ((p.x - a.x) * dx + (p.y - a.y) * dy) / (dx * dx + dy * dy)));
    return Math.hypot(p.x - (a.x + t * dx), p.y - (a.y + t * dy));
  }

  syncToolButtons() {
    document.querySelectorAll("[data-tool]").forEach((button) => {
      button.classList.toggle("active", button.dataset.tool === this.editor.tool);
    });
  }

  onEditorChange() {
    this.syncToolButtons();
    this.syncForm();
    this.renderValidation();
    this.renderMetrics();
    this.updateSelectionText();
    this.requestRender();
  }

  syncForm() {
    const river = this.editor.selectedRiver();
    this.updatingForm = true;
    for (const field of this.form.querySelectorAll("[data-field]")) {
      field.disabled = !river;
      const name = field.dataset.field;
      if (!river) {
        if (field.type === "checkbox") field.checked = false;
        else field.value = "";
        continue;
      }
      if (field.type === "checkbox") field.checked = Boolean(river[name]);
      else if (Array.isArray(river[name])) field.value = river[name].join("; ");
      else field.value = river[name] ?? "";
    }
    this.updatingForm = false;
  }

  updateRiverFromForm() {
    if (this.updatingForm) return;
    const patch = {};
    for (const field of this.form.querySelectorAll("[data-field]")) {
      const name = field.dataset.field;
      if (field.type === "checkbox") patch[name] = field.checked;
      else if (name === "connected_provinces" || name === "crossings") patch[name] = this.listFromText(field.value);
      else if (name === "width_class") patch[name] = Number(field.value);
      else patch[name] = field.value.trim();
    }
    this.editor.updateSelectedRiver(patch);
  }

  listFromText(text) {
    return String(text || "").split(/[;,\n]/).map((item) => item.trim()).filter(Boolean);
  }

  updateSelectionText() {
    const river = this.editor.selectedRiver();
    this.selectionEl.textContent = river
      ? `${river.id} - ${river.points.length} point${river.points.length === 1 ? "" : "s"}`
      : "No river selected";
  }

  renderValidation() {
    if (!this.validator) {
      this.validationEl.innerHTML = "";
      return;
    }
    const warnings = this.validator.validate(this.editor.rivers);
    this.validationEl.innerHTML = warnings.map((warning) =>
      `<div class="validation-item ${warning.severity === "ok" ? "ok" : ""}"><b>${this.escapeHtml(warning.riverId)}</b><br>${this.escapeHtml(warning.message)}</div>`
    ).join("");
  }

  async loadProjectFile(event) {
    const file = event.target.files && event.target.files[0];
    if (!file) return;
    const text = await file.text();
    this.editor.loadProject(JSON.parse(text));
    event.target.value = "";
    this.setStatus(`Loaded ${file.name}.`);
  }

  loadExistingRivers() {
    if (!this.existingRiverPaths) {
      this.setStatus("No existing river_paths.json was found.");
      return;
    }
    this.editor.importRiverPaths(this.existingRiverPaths);
    this.setStatus("Loaded existing river_paths.json.");
  }

  addMorePointsToSelectedRiver() {
    const added = this.editor.addMorePointsToSelectedRiver();
    if (!added) {
      this.setStatus("Select a river with at least two points first.");
      return;
    }
    const river = this.editor.selectedRiver();
    this.setStatus(`Added ${added} intermediate point${added === 1 ? "" : "s"} to ${river.id}.`);
  }

  async runSimulator() {
    if (!this.simulator) {
      this.setStatus("Simulator is not ready yet.");
      return;
    }
    const options = this.simulatorOptions();
    const replace = document.getElementById("sim-replace").checked;
    const runButton = document.getElementById("btn-run-simulator");
    runButton.disabled = true;
    this.setStatus("Running deterministic hydrology simulator...");
    this.simReportEl.textContent = "Calculating flow accumulation and tracing rivers...";
    await new Promise((resolve) => requestAnimationFrame(resolve));
    try {
      let result = this.simulator.run(options);
      let usedOptions = options;
      if (result.rivers.length === 0) {
        const fallback = this.relaxedSimulatorOptions(options);
        const fallbackResult = this.simulator.run(fallback);
        if (fallbackResult.rivers.length > 0) {
          result = fallbackResult;
          usedOptions = fallback;
          this.applySimulatorOptions(fallback);
          result.diagnostics.auto_relaxed = true;
        }
      }
      this.lastSimulation = result;
      this.editor.importGeneratedRivers(result.rivers, { replace });
      this.renderSimulationReport(result);
      if (result.rivers.length === 0) {
        this.setStatus("Simulator found 0 rivers. Lower Min Flow, Min Length, or Source Spacing.");
      } else {
        const relaxed = result.diagnostics && result.diagnostics.auto_relaxed ? " after relaxing strict settings" : "";
        this.setStatus(`Simulator generated ${result.rivers.length} editable draft river${result.rivers.length === 1 ? "" : "s"} with seed ${usedOptions.seed}${relaxed}.`);
      }
    } catch (error) {
      console.error(error);
      this.lastSimulation = null;
      this.simReportEl.textContent = error.message || "Simulator failed.";
      this.setStatus(`Simulator failed: ${error.message || "unknown error"}`);
    } finally {
      runButton.disabled = false;
    }
  }

  randomizeSimulator() {
    const input = document.getElementById("sim-seed");
    const next = this.randomSeed();
    input.value = String(next);
    this.runSimulator();
  }

  resetSimulatorSettings() {
    this.applySimulatorOptions(SIMULATOR_DEFAULTS);
    this.simReportEl.textContent = "Simulator settings reset.";
    this.setStatus("Simulator settings reset to fuller-network defaults.");
  }

  applySimulatorOptions(options) {
    const fields = {
      "sim-min-flow": options.minFlow,
      "sim-max-rivers": options.maxRivers,
      "sim-grid-step": options.gridStep,
      "sim-smoothing": options.smoothing,
      "sim-min-length": options.minLength,
      "sim-source-spacing": options.sourceSpacing,
      "sim-point-density": options.pointDensity,
      "sim-seed": options.seed,
    };
    for (const [id, value] of Object.entries(fields)) {
      const input = document.getElementById(id);
      if (input && value !== undefined) input.value = String(value);
    }
  }

  relaxedSimulatorOptions(options) {
    return {
      ...options,
      minFlow: Math.min(Number(options.minFlow) || SIMULATOR_DEFAULTS.minFlow, SIMULATOR_DEFAULTS.minFlow),
      maxRivers: Math.max(Number(options.maxRivers) || SIMULATOR_DEFAULTS.maxRivers, SIMULATOR_DEFAULTS.maxRivers),
      minLength: Math.min(Number(options.minLength) || SIMULATOR_DEFAULTS.minLength, SIMULATOR_DEFAULTS.minLength),
      sourceSpacing: Math.min(Number(options.sourceSpacing) || SIMULATOR_DEFAULTS.sourceSpacing, SIMULATOR_DEFAULTS.sourceSpacing),
    };
  }

  randomSeed() {
    if (window.crypto && window.crypto.getRandomValues) {
      const data = new Uint32Array(1);
      window.crypto.getRandomValues(data);
      return data[0] % 999999 + 1;
    }
    return Date.now() % 999999 + 1;
  }

  clearSimulation() {
    this.editor.clearGeneratedRivers();
    this.lastSimulation = null;
    this.simReportEl.textContent = "Simulated drafts cleared.";
    this.setStatus("Cleared simulated draft rivers.");
  }

  simulatorOptions() {
    return {
      minFlow: Number(document.getElementById("sim-min-flow").value),
      maxRivers: Number(document.getElementById("sim-max-rivers").value),
      gridStep: Number(document.getElementById("sim-grid-step").value),
      smoothing: Number(document.getElementById("sim-smoothing").value),
      minLength: Number(document.getElementById("sim-min-length").value),
      sourceSpacing: Number(document.getElementById("sim-source-spacing").value),
      pointDensity: Number(document.getElementById("sim-point-density").value),
      seed: Number(document.getElementById("sim-seed").value),
    };
  }

  renderSimulationReport(result) {
    const d = result.diagnostics || {};
    this.simReportEl.innerHTML = [
      `rivers: ${result.rivers.length}`,
      `requested: ${d.requested_rivers || result.settings.maxRivers || "?"}`,
      `grid: ${(d.grid_size || []).join(" x ")}`,
      `cell: ${d.sampled_cell_size || "?"}px`,
      `min length: ${d.min_length_px || "?"}px`,
      `source gap: ${d.source_spacing_px || "?"}px`,
      `max flow: ${d.max_flow_accumulation || 0}`,
      `sources: ${d.candidate_sources || 0}`,
      `basins: ${d.drainage_basins || 0}`,
      `point density: ${d.point_density || 1}`,
      `avg points: ${d.average_points_per_river || 0}`,
      `seed: ${d.variant_seed || 1}`,
      d.auto_relaxed ? "auto relaxed: yes" : "",
    ].filter(Boolean).map((line) => `<div>${this.escapeHtml(line)}</div>`).join("");
  }

  renderMetrics() {
    const river = this.editor.selectedRiver();
    const metrics = river && river.metrics ? river.metrics : null;
    if (!metrics || Object.keys(metrics).length === 0) {
      this.metricsEl.innerHTML = "<div>No simulator metrics for this river.</div>";
      return;
    }
    const fields = [
      ["Sinuosity", "sinuosity"],
      ["Target", "target_sinuosity"],
      ["Gradient", "gradient"],
      ["Avg Slope", "average_slope"],
      ["Avg Elev", "average_elevation"],
      ["Drop", "elevation_drop"],
      ["Stream", "stream_order"],
      ["Discharge", "discharge_estimate"],
      ["Source", "source_score"],
      ["Mouth", "mouth_score"],
      ["Terrain", "terrain_fit_score"],
      ["Meander", "meander_potential"],
      ["Uphill", "uphill_error_score"],
      ["Navigate", "navigability_score"],
      ["Floodplain", "floodplain_fertility"],
      ["Crossing", "crossing_difficulty"],
      ["Port", "port_candidate_score"],
      ["Canal", "canal_feasibility"],
      ["Marsh", "marsh_risk"],
      ["Choke", "strategic_chokepoint_score"],
    ];
    this.metricsEl.innerHTML = fields.map(([label, key]) =>
      `<div><b>${label}</b> ${this.escapeHtml(metrics[key] ?? "")}</div>`).join("");
  }

  heightAt(x, y) {
    if (!this.heightData) return 0;
    const px = Math.max(0, Math.min(MAP_SIZE.width - 1, Math.round(x)));
    const py = Math.max(0, Math.min(MAP_SIZE.height - 1, Math.round(y)));
    return this.heightData[py * MAP_SIZE.width + px] / 255;
  }

  maskAt(name, x, y) {
    const data = this.maskData[name];
    if (!data) return 0;
    const px = Math.max(0, Math.min(MAP_SIZE.width - 1, Math.round(x)));
    const py = Math.max(0, Math.min(MAP_SIZE.height - 1, Math.round(y)));
    return data[py * MAP_SIZE.width + px] / 255;
  }

  provinceIdAt(x, y) {
    if (!this.provinceRgba) return "";
    const px = Math.max(0, Math.min(MAP_SIZE.width - 1, Math.round(x)));
    const py = Math.max(0, Math.min(MAP_SIZE.height - 1, Math.round(y)));
    const off = (py * MAP_SIZE.width + px) * 4;
    const key = (this.provinceRgba[off] << 16) | (this.provinceRgba[off + 1] << 8) | this.provinceRgba[off + 2];
    return this.provinceColorToId.get(key) || "";
  }

  requestRender() {
    if (this.pendingRender) return;
    this.pendingRender = true;
    requestAnimationFrame(() => this.render());
  }

  setStatus(text) {
    this.statusEl.textContent = text;
  }

  escapeHtml(value) {
    return String(value).replace(/[&<>"]/g, (ch) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[ch]));
  }

  clamp(value, min, max) {
    return Math.max(min, Math.min(max, value));
  }
}

const app = new RiverWorkbench();
app.init().catch((error) => {
  console.error(error);
  app.setStatus(error.message || "River Workbench failed to load.");
});

window.__riverWorkbench = app;

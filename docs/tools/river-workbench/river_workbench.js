import { RiverEditor } from "./river_editor.js";
import { RiverExporter } from "./river_exporter.js";
import { HydrologySimulator } from "./hydrology_simulator.js";
import { RiverValidator } from "./river_validator.js";

const MAP_SIZE = { width: 3072, height: 2048 };
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
    document.getElementById("tool-buttons").addEventListener("click", (event) => {
      const button = event.target.closest("[data-tool]");
      if (!button) return;
      this.editor.setTool(button.dataset.tool);
      this.syncToolButtons();
    });
    document.getElementById("btn-new-river").addEventListener("click", () => this.editor.createRiver());
    document.getElementById("btn-delete-river").addEventListener("click", () => this.editor.deleteSelectedRiver());
    document.getElementById("btn-reverse-river").addEventListener("click", () => this.editor.reverseSelectedRiver());
    document.getElementById("btn-load-existing").addEventListener("click", () => this.loadExistingRivers());
    document.getElementById("btn-run-simulator").addEventListener("click", () => this.runSimulator());
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
    this.cursorEl.textContent = `x ${Math.round(world.x)}, y ${Math.round(world.y)}`;
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

  async runSimulator() {
    if (!this.simulator) {
      this.setStatus("Simulator is not ready yet.");
      return;
    }
    const options = this.simulatorOptions();
    const replace = document.getElementById("sim-replace").checked;
    this.setStatus("Running deterministic hydrology simulator...");
    await new Promise((resolve) => requestAnimationFrame(resolve));
    const result = this.simulator.run(options);
    this.lastSimulation = result;
    this.editor.importGeneratedRivers(result.rivers, { replace });
    this.renderSimulationReport(result);
    this.setStatus(`Simulator generated ${result.rivers.length} editable draft river${result.rivers.length === 1 ? "" : "s"}.`);
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
    };
  }

  renderSimulationReport(result) {
    const d = result.diagnostics || {};
    this.simReportEl.innerHTML = [
      `rivers: ${result.rivers.length}`,
      `grid: ${(d.grid_size || []).join(" x ")}`,
      `cell: ${d.sampled_cell_size || "?"}px`,
      `max flow: ${d.max_flow_accumulation || 0}`,
      `sources: ${d.candidate_sources || 0}`,
      `basins: ${d.drainage_basins || 0}`,
    ].map((line) => `<div>${this.escapeHtml(line)}</div>`).join("");
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
}

const app = new RiverWorkbench();
app.init().catch((error) => {
  console.error(error);
  app.setStatus(error.message || "River Workbench failed to load.");
});

window.__riverWorkbench = app;

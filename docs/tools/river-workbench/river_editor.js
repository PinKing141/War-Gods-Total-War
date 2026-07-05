const RIVER_TYPES = [
  "major_river",
  "tributary",
  "canal",
  "marsh_channel",
  "oasis_wadi",
  "delta",
  "lake_outlet",
  "endorheic_stream",
];

const WIDTH_BY_CLASS = {
  1: 5,
  2: 8,
  3: 12,
  4: 17,
  5: 24,
};

export class RiverEditor {
  constructor({ mapSize }) {
    this.mapSize = mapSize;
    this.rivers = [];
    this.selectedRiverId = null;
    this.selectedPointIndex = null;
    this.tool = "select";
    this.nextRiverNumber = 1;
    this.onChange = () => {};
  }

  selectedRiver() {
    return this.rivers.find((river) => river.id === this.selectedRiverId) || null;
  }

  setTool(tool) {
    this.tool = tool;
    this.selectedPointIndex = null;
    this._emit();
  }

  createRiver() {
    const number = this.nextRiverNumber++;
    const river = {
      id: `RIV_CUSTOM_${String(number).padStart(3, "0")}`,
      name: `New River ${number}`,
      type: "tributary",
      width_class: 2,
      navigable: false,
      source_province: "",
      mouth: "",
      connected_provinces: [],
      crossings: [],
      notes: "",
      points: [],
    };
    this.rivers.push(river);
    this.selectedRiverId = river.id;
    this.selectedPointIndex = null;
    this.tool = "add-point";
    this._emit();
    return river;
  }

  deleteSelectedRiver() {
    if (!this.selectedRiverId) return;
    this.rivers = this.rivers.filter((river) => river.id !== this.selectedRiverId);
    this.selectedRiverId = this.rivers[0] ? this.rivers[0].id : null;
    this.selectedPointIndex = null;
    this._emit();
  }

  reverseSelectedRiver() {
    const river = this.selectedRiver();
    if (!river) return;
    river.points.reverse();
    if (this.selectedPointIndex !== null) {
      this.selectedPointIndex = river.points.length - 1 - this.selectedPointIndex;
    }
    this._emit();
  }

  addMorePointsToSelectedRiver() {
    const river = this.selectedRiver();
    if (!river || !river.points || river.points.length < 2) return 0;
    const next = [river.points[0]];
    let added = 0;
    for (let i = 1; i < river.points.length; i++) {
      const a = river.points[i - 1];
      const b = river.points[i];
      next.push(this._clampPoint([(a[0] + b[0]) / 2, (a[1] + b[1]) / 2]));
      next.push(b);
      added++;
    }
    river.points = next;
    this.selectedPointIndex = null;
    this._emit();
    return added;
  }

  addPoint(point) {
    let river = this.selectedRiver();
    if (!river) river = this.createRiver();
    river.points.push(this._clampPoint(point));
    this.selectedPointIndex = river.points.length - 1;
    this._emit();
  }

  moveSelectedPoint(point) {
    const river = this.selectedRiver();
    if (!river || this.selectedPointIndex === null) return;
    river.points[this.selectedPointIndex] = this._clampPoint(point);
    this._emit();
  }

  deletePoint(riverId, pointIndex) {
    const river = this.rivers.find((item) => item.id === riverId);
    if (!river || pointIndex < 0 || pointIndex >= river.points.length) return;
    river.points.splice(pointIndex, 1);
    this.selectedRiverId = river.id;
    this.selectedPointIndex = null;
    this._emit();
  }

  selectRiver(riverId, pointIndex = null) {
    this.selectedRiverId = riverId;
    this.selectedPointIndex = pointIndex;
    this._emit();
  }

  updateSelectedRiver(patch) {
    const river = this.selectedRiver();
    if (!river) return;
    const previousId = river.id;
    Object.assign(river, patch);
    if (patch.id && previousId === this.selectedRiverId) this.selectedRiverId = patch.id;
    this._emit();
  }

  loadProject(project) {
    const rivers = Array.isArray(project.rivers) ? project.rivers : [];
    this.rivers = rivers.map((river, index) => this.normalizeRiver(river, index));
    this.selectedRiverId = this.rivers[0] ? this.rivers[0].id : null;
    this.selectedPointIndex = null;
    this.nextRiverNumber = this._nextNumber();
    this._emit();
  }

  importRiverPaths(data) {
    const rivers = Array.isArray(data.rivers) ? data.rivers : [];
    this.rivers = rivers.map((river, index) => this.normalizeRiver(river, index));
    this.selectedRiverId = this.rivers[0] ? this.rivers[0].id : null;
    this.selectedPointIndex = null;
    this.nextRiverNumber = this._nextNumber();
    this._emit();
  }

  importGeneratedRivers(rivers, { replace = true } = {}) {
    const normalized = (Array.isArray(rivers) ? rivers : []).map((river, index) => this.normalizeRiver(river, index));
    this.rivers = replace
      ? normalized
      : [...this.rivers.filter((river) => river.generated_by !== "hydrology_simulator"), ...normalized];
    this.selectedRiverId = this.rivers[0] ? this.rivers[0].id : null;
    this.selectedPointIndex = null;
    this.nextRiverNumber = this._nextNumber();
    this._emit();
  }

  clearGeneratedRivers() {
    this.rivers = this.rivers.filter((river) => river.generated_by !== "hydrology_simulator");
    this.selectedRiverId = this.rivers[0] ? this.rivers[0].id : null;
    this.selectedPointIndex = null;
    this._emit();
  }

  normalizeRiver(river, index = 0) {
    const widthClass = Number(river.width_class || this.widthClassFromWidth(river.width) || 2);
    return {
      id: String(river.id || `RIV_IMPORTED_${String(index + 1).padStart(3, "0")}`),
      name: String(river.name || `Imported River ${index + 1}`),
      type: RIVER_TYPES.includes(river.type) ? river.type : "tributary",
      width_class: Math.max(1, Math.min(5, widthClass || 2)),
      navigable: Boolean(river.navigable),
      source_province: String(river.source_province || ""),
      mouth: String(river.mouth || ""),
      connected_provinces: this._arrayField(river.connected_provinces),
      crossings: this._arrayField(river.crossings),
      notes: String(river.notes || ""),
      points: this._normalizePoints(river.points),
      generated_by: river.generated_by || "",
      metrics: river.metrics && typeof river.metrics === "object" ? { ...river.metrics } : {},
    };
  }

  widthForRiver(river) {
    return WIDTH_BY_CLASS[Number(river.width_class)] || WIDTH_BY_CLASS[2];
  }

  widthClassFromWidth(width) {
    const value = Number(width);
    if (!Number.isFinite(value)) return 2;
    if (value <= 6) return 1;
    if (value <= 10) return 2;
    if (value <= 14) return 3;
    if (value <= 20) return 4;
    return 5;
  }

  toProject() {
    return {
      version: 1,
      tool: "river-workbench",
      map_size: [this.mapSize.width, this.mapSize.height],
      saved_at: new Date().toISOString(),
      rivers: this.rivers.map((river) => ({ ...river, points: river.points.map((pt) => [pt[0], pt[1]]) })),
    };
  }

  _normalizePoints(points) {
    if (!Array.isArray(points)) return [];
    return points
      .map((point) => {
        if (Array.isArray(point)) return [Number(point[0]), Number(point[1])];
        return [Number(point.x), Number(point.y)];
      })
      .filter(([x, y]) => Number.isFinite(x) && Number.isFinite(y))
      .map((point) => this._clampPoint(point));
  }

  _arrayField(value) {
    if (Array.isArray(value)) return value.map((item) => String(item).trim()).filter(Boolean);
    if (!value) return [];
    return String(value).split(/[;,]/).map((item) => item.trim()).filter(Boolean);
  }

  _clampPoint(point) {
    const x = Math.max(0, Math.min(this.mapSize.width, Number(point[0])));
    const y = Math.max(0, Math.min(this.mapSize.height, Number(point[1])));
    return [Math.round(x * 100) / 100, Math.round(y * 100) / 100];
  }

  _nextNumber() {
    let highest = 0;
    for (const river of this.rivers) {
      const match = /(\d+)$/.exec(river.id || "");
      if (match) highest = Math.max(highest, Number(match[1]));
    }
    return highest + 1;
  }

  _emit() {
    this.onChange(this);
  }
}

export { RIVER_TYPES, WIDTH_BY_CLASS };

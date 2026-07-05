const VALID_TYPES = new Set([
  "major_river",
  "tributary",
  "canal",
  "marsh_channel",
  "oasis_wadi",
  "delta",
  "lake_outlet",
  "endorheic_stream",
]);

export class RiverValidator {
  constructor({ mapSize, provinceIds, heightAt, waterAt }) {
    this.mapSize = mapSize;
    this.provinceIds = provinceIds;
    this.heightAt = heightAt;
    this.waterAt = waterAt;
  }

  validate(rivers) {
    const warnings = [];
    const seen = new Set();
    if (!rivers.length) {
      warnings.push({ severity: "warning", riverId: "Project", message: "No rivers have been created yet." });
    }

    for (const river of rivers) {
      const label = river.id || river.name || "Unnamed river";
      if (!river.id) warnings.push({ severity: "warning", riverId: label, message: "River has no id." });
      if (river.id && seen.has(river.id)) warnings.push({ severity: "warning", riverId: label, message: "River id is duplicated." });
      if (river.id) seen.add(river.id);
      if (!river.name) warnings.push({ severity: "warning", riverId: label, message: "River has no name." });
      if (!VALID_TYPES.has(river.type)) warnings.push({ severity: "warning", riverId: label, message: "River type is not recognized." });
      if (!Number.isInteger(Number(river.width_class)) || Number(river.width_class) < 1 || Number(river.width_class) > 5) {
        warnings.push({ severity: "warning", riverId: label, message: "Width class should be 1 to 5." });
      }
      if (!river.points || river.points.length < 2) {
        warnings.push({ severity: "warning", riverId: label, message: "River has fewer than 2 points." });
      }
      this._validatePoints(river, label, warnings);
      this._validateProvinces(river, label, warnings);
      this._validateFlow(river, label, warnings);
      this._validateMouth(river, label, warnings);
      this._validateMetrics(river, label, warnings);
    }

    if (!warnings.length) {
      warnings.push({ severity: "ok", riverId: "Project", message: "No basic validation warnings." });
    }
    return warnings;
  }

  _validatePoints(river, label, warnings) {
    for (const point of river.points || []) {
      const [x, y] = point;
      if (x < 0 || y < 0 || x > this.mapSize.width || y > this.mapSize.height) {
        warnings.push({ severity: "warning", riverId: label, message: "River has a point outside the map bounds." });
        return;
      }
    }
  }

  _validateProvinces(river, label, warnings) {
    const all = [...(river.connected_provinces || [])];
    if (river.source_province) all.push(river.source_province);
    for (const provinceId of all) {
      if (!this.provinceIds.has(provinceId)) {
        warnings.push({ severity: "warning", riverId: label, message: `Unknown province reference: ${provinceId}.` });
      }
    }
  }

  _validateFlow(river, label, warnings) {
    if (!this.heightAt || !river.points || river.points.length < 2 || river.type === "canal") return;
    let uphill = 0;
    for (let i = 1; i < river.points.length; i++) {
      const previous = this.heightAt(river.points[i - 1][0], river.points[i - 1][1]);
      const next = this.heightAt(river.points[i][0], river.points[i][1]);
      if (next > previous + 0.045) uphill++;
    }
    if (uphill > Math.max(1, river.points.length * 0.25)) {
      warnings.push({ severity: "warning", riverId: label, message: "River appears to flow uphill too often. Try reversing or moving points." });
    }
  }

  _validateMouth(river, label, warnings) {
    if (!river.points || river.points.length < 2) return;
    if (!river.mouth && ["major_river", "delta", "lake_outlet"].includes(river.type)) {
      warnings.push({ severity: "warning", riverId: label, message: "Major or mouth-bearing river has no mouth value." });
    }
    if (!this.waterAt || !["major_river", "delta", "lake_outlet"].includes(river.type)) return;
    const end = river.points[river.points.length - 1];
    let nearWater = false;
    for (let dy = -28; dy <= 28; dy += 14) {
      for (let dx = -28; dx <= 28; dx += 14) {
        if (this.waterAt(end[0] + dx, end[1] + dy) > 0.32) nearWater = true;
      }
    }
    if (!nearWater) {
      warnings.push({ severity: "warning", riverId: label, message: "River mouth is not near the water mask." });
    }
  }

  _validateMetrics(river, label, warnings) {
    const m = river.metrics || {};
    if (!m || Object.keys(m).length === 0) return;
    if (Number(m.uphill_error_score) > 0.28) {
      warnings.push({ severity: "warning", riverId: label, message: "Simulator detected too many uphill segments." });
    }
    if (Number(m.terrain_fit_score) < 0.36) {
      warnings.push({ severity: "warning", riverId: label, message: "Terrain fit score is low for this route." });
    }
    if (river.type === "canal" && Number(m.sinuosity) > 1.12) {
      warnings.push({ severity: "warning", riverId: label, message: "Canal sinuosity is high; canals should be fairly straight." });
    }
    if (river.type !== "canal" && Number(m.sinuosity) < 1.04 && (river.points || []).length > 3) {
      warnings.push({ severity: "warning", riverId: label, message: "River is very straight; consider naturalizing bends." });
    }
    if (river.navigable && Number(m.navigability_score) < 0.48) {
      warnings.push({ severity: "warning", riverId: label, message: "River is marked navigable but simulator navigability is low." });
    }
  }
}

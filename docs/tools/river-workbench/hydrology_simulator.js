const NEIGHBORS = [
  [-1, -1, Math.SQRT2], [0, -1, 1], [1, -1, Math.SQRT2],
  [-1, 0, 1],                    [1, 0, 1],
  [-1, 1, Math.SQRT2],  [0, 1, 1],  [1, 1, Math.SQRT2],
];

export class HydrologySimulator {
  constructor({ mapSize, heightData, masks, provinceIdAt }) {
    this.mapSize = mapSize;
    this.heightData = heightData;
    this.masks = masks || {};
    this.provinceIdAt = provinceIdAt || (() => "");
  }

  run(options = {}) {
    const smoothing = Number(options.smoothing);
    const settings = {
      gridStep: this._clamp(Number(options.gridStep) || 16, 8, 32),
      minFlow: Math.max(4, Number(options.minFlow) || 18),
      maxRivers: this._clamp(Number(options.maxRivers) || 40, 1, 200),
      smoothing: this._clamp(Number.isFinite(smoothing) ? smoothing : 1, 0, 3),
      minLength: this._clamp(Number(options.minLength) || 140, 60, 900),
      sourceSpacing: this._clamp(Number(options.sourceSpacing) || 90, 32, 360),
      pointDensity: this._clamp(Number(options.pointDensity) || 1, 1, 6),
      seed: Math.max(1, Math.floor(Number(options.seed) || 1)),
    };
    const grid = this._buildGrid(settings.gridStep);
    this._prepareElevation(grid, settings.smoothing);
    this._calculateSlope(grid);
    this._calculateFlowDirection(grid);
    this._calculateFlowAccumulation(grid);
    this._calculateWatersheds(grid);

    const rivers = this._traceRivers(grid, settings)
      .map((river, index) => this._finalizeRiver(river, index, grid, settings))
      .filter(Boolean);
    const totalPoints = rivers.reduce((sum, river) => sum + river.points.length, 0);

    return {
      settings,
      rivers,
      diagnostics: {
        requested_rivers: settings.maxRivers,
        grid_size: [grid.w, grid.h],
        sampled_cell_size: settings.gridStep,
        min_length_px: settings.minLength,
        source_spacing_px: settings.sourceSpacing,
        max_flow_accumulation: Math.round(grid.maxAccumulation * 100) / 100,
        candidate_sources: grid.candidateCount || 0,
        drainage_basins: grid.basinSizes.size,
        point_density: settings.pointDensity,
        total_points: totalPoints,
        average_points_per_river: rivers.length ? Math.round(totalPoints / rivers.length) : 0,
        variant_seed: settings.seed,
      },
    };
  }

  _buildGrid(step) {
    const w = Math.floor(this.mapSize.width / step);
    const h = Math.floor(this.mapSize.height / step);
    const total = w * h;
    const grid = {
      step, w, h, total,
      height: new Float32Array(total),
      elevation: new Float32Array(total),
      slope: new Float32Array(total),
      accumulation: new Float32Array(total),
      precipitation: new Float32Array(total),
      sourceScore: new Float32Array(total),
      flowDir: new Int32Array(total).fill(-1),
      outlet: new Int32Array(total).fill(-1),
      land: new Uint8Array(total),
      masks: {},
      basinSizes: new Map(),
      maxAccumulation: 0,
    };

    for (const name of [
      "water", "land", "coast", "mountain", "highland", "lowland",
      "fertile_lowland", "farmland", "forest", "marsh", "dryland",
      "steppe", "oasis_wetland", "bare_rock", "snow_peak", "pass",
    ]) {
      grid.masks[name] = new Float32Array(total);
    }

    for (let gy = 0; gy < h; gy++) {
      for (let gx = 0; gx < w; gx++) {
        const i = gy * w + gx;
        const wx = Math.min(this.mapSize.width - 1, Math.round((gx + 0.5) * step));
        const wy = Math.min(this.mapSize.height - 1, Math.round((gy + 0.5) * step));
        const height = this._heightAt(wx, wy);
        grid.height[i] = height;
        for (const [name, data] of Object.entries(grid.masks)) data[i] = this._maskAt(name, wx, wy);
        const water = grid.masks.water[i];
        const land = grid.masks.land[i];
        grid.land[i] = land > 0.34 && water < 0.52 ? 1 : 0;
      }
    }
    return grid;
  }

  _prepareElevation(grid, smoothing) {
    for (let i = 0; i < grid.total; i++) {
      const m = this._cellMasks(grid, i);
      let elevation = grid.height[i];
      if (!grid.land[i]) elevation = -0.25 - m.water * 0.18;
      else {
        elevation += m.mountain * 0.075 + m.snow_peak * 0.07 + m.highland * 0.025;
        elevation -= m.lowland * 0.035 + m.marsh * 0.045 + m.oasis_wetland * 0.035 + m.coast * 0.055;
        elevation += m.bare_rock * 0.018;
      }
      grid.elevation[i] = elevation;
      grid.precipitation[i] = this._precipitationScore(m);
      grid.sourceScore[i] = this._sourceScore(m, elevation);
    }

    let current = grid.elevation;
    for (let pass = 0; pass < smoothing; pass++) {
      const next = new Float32Array(grid.total);
      for (let y = 0; y < grid.h; y++) {
        for (let x = 0; x < grid.w; x++) {
          const i = y * grid.w + x;
          if (!grid.land[i]) {
            next[i] = current[i];
            continue;
          }
          let sum = current[i] * 2;
          let count = 2;
          for (const [dx, dy] of NEIGHBORS) {
            const n = this._idx(grid, x + dx, y + dy);
            if (n < 0 || !grid.land[n]) continue;
            sum += current[n];
            count += 1;
          }
          const m = this._cellMasks(grid, i);
          const preserve = this._clamp(m.mountain * 0.55 + m.snow_peak * 0.65 + m.coast * 0.70, 0, 0.78);
          next[i] = current[i] * preserve + (sum / count) * (1 - preserve);
        }
      }
      current = next;
    }
    grid.elevation = current;
  }

  _calculateSlope(grid) {
    for (let y = 0; y < grid.h; y++) {
      for (let x = 0; x < grid.w; x++) {
        const i = y * grid.w + x;
        const l = grid.elevation[this._idxClamped(grid, x - 1, y)];
        const r = grid.elevation[this._idxClamped(grid, x + 1, y)];
        const u = grid.elevation[this._idxClamped(grid, x, y - 1)];
        const d = grid.elevation[this._idxClamped(grid, x, y + 1)];
        grid.slope[i] = Math.min(1, Math.hypot(r - l, d - u) * 3.8);
      }
    }
  }

  _calculateFlowDirection(grid) {
    for (let y = 0; y < grid.h; y++) {
      for (let x = 0; x < grid.w; x++) {
        const i = y * grid.w + x;
        if (!grid.land[i]) continue;
        let best = -1;
        let bestScore = grid.elevation[i] - 0.002;
        let bestWater = -1;
        for (const [dx, dy, dist] of NEIGHBORS) {
          const n = this._idx(grid, x + dx, y + dy);
          if (n < 0) continue;
          const water = grid.masks.water[n] + grid.masks.coast[n] * 0.5;
          if (!grid.land[n] && water > bestWater) {
            best = n;
            bestWater = water;
            bestScore = -1;
            continue;
          }
          if (!grid.land[n]) continue;
          const valleyBonus = grid.masks.lowland[n] * 0.015 + grid.masks.marsh[n] * 0.02 + grid.masks.coast[n] * 0.025;
          const score = grid.elevation[n] + dist * 0.0008 - valleyBonus;
          if (score < bestScore) {
            best = n;
            bestScore = score;
          }
        }
        grid.flowDir[i] = best;
      }
    }
  }

  _calculateFlowAccumulation(grid) {
    const cells = [];
    for (let i = 0; i < grid.total; i++) {
      if (grid.land[i]) {
        grid.accumulation[i] = grid.precipitation[i];
        cells.push(i);
      }
    }
    cells.sort((a, b) => grid.elevation[b] - grid.elevation[a]);
    for (const i of cells) {
      const to = grid.flowDir[i];
      if (to >= 0 && grid.land[to]) grid.accumulation[to] += grid.accumulation[i];
      if (grid.accumulation[i] > grid.maxAccumulation) grid.maxAccumulation = grid.accumulation[i];
    }
  }

  _calculateWatersheds(grid) {
    for (let i = 0; i < grid.total; i++) {
      if (!grid.land[i]) continue;
      const outlet = this._followOutlet(grid, i);
      grid.outlet[i] = outlet;
      grid.basinSizes.set(outlet, (grid.basinSizes.get(outlet) || 0) + 1);
    }
  }

  _traceRivers(grid, settings) {
    const candidates = [];
    const maxAccum = Math.max(settings.minFlow, grid.maxAccumulation);
    for (let i = 0; i < grid.total; i++) {
      if (!grid.land[i]) continue;
      if (grid.accumulation[i] < settings.minFlow) continue;
      if (grid.masks.water[i] > 0.2 || grid.masks.coast[i] > 0.65) continue;
      const sourceScore = grid.sourceScore[i];
      if (sourceScore < 0.22 && grid.elevation[i] < 0.30) continue;
      const accumScore = Math.sqrt(grid.accumulation[i] / maxAccum);
      const baseScore = sourceScore * 1.9 + accumScore * 0.9 + grid.elevation[i] * 0.55 - grid.slope[i] * 0.12;
      const variant = (this._hash(i, settings.seed) - 0.5) * 0.18 * (0.45 + accumScore);
      candidates.push({ i, score: baseScore + variant });
    }
    candidates.sort((a, b) => b.score - a.score);
    grid.candidateCount = candidates.length;

    const used = new Set();
    const sourceTaken = [];
    const traced = [];
    const minSourceGap = Math.max(2, Math.round(settings.sourceSpacing / grid.step));

    for (const candidate of candidates) {
      if (traced.length >= settings.maxRivers) break;
      if (used.has(candidate.i)) continue;
      const [cx, cy] = this._xy(grid, candidate.i);
      if (sourceTaken.some(([x, y]) => Math.hypot(cx - x, cy - y) < minSourceGap)) continue;
      const cells = this._traceFromSource(grid, candidate.i, used);
      const worldLength = this._cellPathWorldLength(grid, cells);
      if (cells.length < 8 || worldLength < settings.minLength) continue;
      for (const cell of cells) used.add(cell);
      sourceTaken.push([cx, cy]);
      traced.push({ cells, sourceCell: candidate.i, worldLength });
    }
    return traced;
  }

  _traceFromSource(grid, start, used) {
    const cells = [];
    const seen = new Set();
    let current = start;
    const maxSteps = grid.w + grid.h;
    for (let step = 0; step < maxSteps; step++) {
      if (current < 0 || seen.has(current)) break;
      cells.push(current);
      seen.add(current);
      const next = grid.flowDir[current];
      if (next < 0) break;
      if (!grid.land[next]) {
        cells.push(next);
        break;
      }
      if (used.has(next) && cells.length > 10) {
        cells.push(next);
        break;
      }
      current = next;
    }
    return cells;
  }

  _finalizeRiver(trace, index, grid, settings = {}) {
    const rawPoints = this._cellsToWorldPoints(grid, trace.cells, settings);
    const meandered = this._meanderPoints(rawPoints, trace.cells, grid, settings);
    const smoothed = this._smoothPoints(meandered, 1);
    const shaped = this._naturalizeSinuosity(smoothed, trace.cells, grid, settings);
    const points = this._densifyPoints(shaped, settings)
      .map((point) => [Math.round(point[0]), Math.round(point[1])]);
    if (points.length < 2) return null;
    const metrics = this._riverMetrics(points, trace.cells, grid, settings);
    const widthClass = this._widthClass(metrics);
    const type = this._riverType(metrics, widthClass);
    const id = `SIM_RIVER_${String(index + 1).padStart(3, "0")}`;
    const connected = this._connectedProvinces(points);
    return {
      id,
      name: `Simulated River ${index + 1}`,
      type,
      width_class: widthClass,
      navigable: metrics.navigability_score >= 0.58,
      source_province: this.provinceIdAt(points[0][0], points[0][1]) || "",
      mouth: this._mouthLabel(metrics),
      connected_provinces: connected,
      crossings: [],
      notes: `Generated by the deterministic hydrology simulator with seed ${settings.seed || 1}. Review and edit before final export.`,
      points,
      generated_by: "hydrology_simulator",
      metrics,
    };
  }

  _riverMetrics(points, cells, grid, settings = {}) {
    const length = this._worldLength(points);
    const straight = Math.max(1, Math.hypot(points.at(-1)[0] - points[0][0], points.at(-1)[1] - points[0][1]));
    const sourceCell = cells[0];
    const mouthCell = cells[cells.length - 1];
    const sourceElevation = grid.height[sourceCell];
    const mouthElevation = Math.max(0, grid.height[mouthCell]);
    const elevationDrop = Math.max(0, sourceElevation - mouthElevation);
    const gradient = elevationDrop / Math.max(1, length);
    const avg = (fn) => cells.reduce((sum, cell) => sum + fn(cell), 0) / Math.max(1, cells.length);
    const elevations = cells.map((cell) => grid.height[cell]);
    const averageElevation = elevations.reduce((sum, elevation) => sum + elevation, 0) / Math.max(1, elevations.length);
    const minElevation = elevations.reduce((best, elevation) => Math.min(best, elevation), 1);
    const maxElevation = elevations.reduce((best, elevation) => Math.max(best, elevation), 0);
    const maxAccum = cells.reduce((best, cell) => Math.max(best, grid.accumulation[cell]), 0);
    const slopeAverage = avg((cell) => grid.slope[cell]);
    const lowland = avg((cell) => grid.masks.lowland[cell]);
    const farmland = avg((cell) => grid.masks.farmland[cell] + grid.masks.fertile_lowland[cell] * 0.6);
    const marsh = avg((cell) => grid.masks.marsh[cell]);
    const dryland = avg((cell) => grid.masks.dryland[cell] + grid.masks.steppe[cell] * 0.4);
    const mountain = avg((cell) => grid.masks.mountain[cell] + grid.masks.bare_rock[cell] * 0.6);
    const oasis = avg((cell) => grid.masks.oasis_wetland[cell]);
    const coast = Math.max(grid.masks.coast[mouthCell], grid.masks.water[mouthCell]);
    let uphill = 0;
    for (let i = 1; i < cells.length; i++) {
      if (grid.height[cells[i]] > grid.height[cells[i - 1]] + 0.035) uphill++;
    }

    const meanderPotential = this._clamp(lowland * 0.42 + farmland * 0.23 + marsh * 0.28 + oasis * 0.18 - slopeAverage * 0.45 - mountain * 0.22, 0, 1);
    const terrainFit = this._clamp(0.46 + lowland * 0.22 + marsh * 0.18 + farmland * 0.14 + oasis * 0.12 - mountain * 0.22 - dryland * 0.08, 0, 1);
    const mouthScore = this._clamp(coast * 0.75 + grid.masks.marsh[mouthCell] * 0.30 + grid.masks.oasis_wetland[mouthCell] * 0.20, 0, 1);
    const discharge = Math.round(maxAccum * grid.step * grid.step);
    const streamOrder = this._streamOrder(maxAccum, grid.maxAccumulation);
    const navigability = this._clamp((streamOrder - 2) / 3 + mouthScore * 0.25 + lowland * 0.18 - gradient * 900 - mountain * 0.18, 0, 1);
    const crossingDifficulty = this._clamp((streamOrder / 5) * 0.52 + slopeAverage * 1.7 + mountain * 0.25 - lowland * 0.18, 0, 1);
    const portCandidate = this._clamp(navigability * 0.55 + mouthScore * 0.35 + farmland * 0.10, 0, 1);
    const canalFeasibility = this._clamp(lowland * 0.35 + farmland * 0.24 + dryland * 0.10 - mountain * 0.45 - slopeAverage * 0.55, 0, 1);
    const floodplainFertility = this._clamp(lowland * 0.36 + farmland * 0.34 + marsh * 0.18 + oasis * 0.20 - dryland * 0.08, 0, 1);
    const marshRisk = this._clamp(marsh * 0.65 + lowland * 0.16 + (slopeAverage < 0.08 ? 0.10 : 0), 0, 1);
    const strategicChokepoint = this._clamp(crossingDifficulty * 0.42 + portCandidate * 0.22 + mountain * 0.20 + mouthScore * 0.16, 0, 1);
    const root = grid.outlet[sourceCell];
    const basinSize = grid.basinSizes.get(root) || cells.length;
    const targetSinuosity = this._targetSinuosity(cells, grid);
    return {
      sinuosity: this._round(length / straight, 3),
      target_sinuosity: this._round(targetSinuosity, 3),
      length_px: Math.round(length),
      straight_length_px: Math.round(straight),
      source_elevation: this._round(sourceElevation, 4),
      mouth_elevation: this._round(mouthElevation, 4),
      average_elevation: this._round(averageElevation, 4),
      min_elevation: this._round(minElevation, 4),
      max_elevation: this._round(maxElevation, 4),
      elevation_drop: this._round(elevationDrop, 4),
      gradient: this._round(gradient, 6),
      average_slope: this._round(slopeAverage, 4),
      uphill_error_score: this._round(uphill / Math.max(1, cells.length - 1), 3),
      meander_potential: this._round(meanderPotential, 3),
      terrain_fit_score: this._round(terrainFit, 3),
      source_score: this._round(grid.sourceScore[sourceCell], 3),
      mouth_score: this._round(mouthScore, 3),
      stream_order: streamOrder,
      discharge_estimate: discharge,
      width_class_score: streamOrder,
      navigability_score: this._round(navigability, 3),
      tributary_join_quality: this._round(this._tributaryJoinQuality(cells, grid), 3),
      watershed_id: root >= 0 ? `BASIN_${root}` : "BASIN_EDGE",
      drainage_basin_cells: basinSize,
      floodplain_fertility: this._round(floodplainFertility, 3),
      crossing_difficulty: this._round(crossingDifficulty, 3),
      bridge_ford_candidate_score: this._round(1 - crossingDifficulty * 0.68 + lowland * 0.18, 3),
      port_candidate_score: this._round(portCandidate, 3),
      canal_feasibility: this._round(canalFeasibility, 3),
      marsh_risk: this._round(marshRisk, 3),
      strategic_chokepoint_score: this._round(strategicChokepoint, 3),
      endorheic_score: this._round(mouthScore < 0.25 ? this._clamp(1 - coast - gradient * 1200, 0, 1) : 0, 3),
      variant_seed: settings.seed || 1,
    };
  }

  _riverType(metrics, widthClass) {
    if (metrics.mouth_score > 0.62 && metrics.discharge_estimate > 28000 && metrics.gradient < 0.00018) return "delta";
    if (metrics.marsh_risk > 0.52 && metrics.gradient < 0.00024) return "marsh_channel";
    if (metrics.canal_feasibility > 0.58 && metrics.mouth_score < 0.25 && metrics.gradient < 0.00012) return "oasis_wadi";
    if (metrics.mouth_score < 0.25 && metrics.endorheic_score > 0.35) return "endorheic_stream";
    if (metrics.mouth_score < 0.25) return "tributary";
    return widthClass >= 4 ? "major_river" : "tributary";
  }

  _mouthLabel(metrics) {
    if (metrics.mouth_score >= 0.35) return "water_or_coast";
    if (metrics.tributary_join_quality >= 0.42) return "joins_downstream_river";
    if (metrics.endorheic_score >= 0.35) return "inland_basin";
    if (metrics.marsh_risk >= 0.45) return "marsh_or_wetland";
    return "unresolved_basin";
  }

  _widthClass(metrics) {
    if (metrics.stream_order >= 5 || metrics.discharge_estimate > 85000) return 5;
    if (metrics.stream_order >= 4 || metrics.discharge_estimate > 42000) return 4;
    if (metrics.stream_order >= 3 || metrics.discharge_estimate > 18000) return 3;
    if (metrics.stream_order >= 2 || metrics.discharge_estimate > 8500) return 2;
    return 1;
  }

  _streamOrder(accumulation, maxAccumulation) {
    const ratio = accumulation / Math.max(1, maxAccumulation);
    if (ratio > 0.58) return 5;
    if (ratio > 0.31) return 4;
    if (ratio > 0.14) return 3;
    if (ratio > 0.055) return 2;
    return 1;
  }

  _cellsToWorldPoints(grid, cells, settings = {}) {
    const sampled = [];
    const density = this._clamp(Number(settings.pointDensity) || 1, 1, 6);
    const stride = Math.max(1, Math.floor((42 / density) / grid.step));
    for (let i = 0; i < cells.length; i += stride) sampled.push(this._cellCenter(grid, cells[i]));
    const last = this._cellCenter(grid, cells[cells.length - 1]);
    const end = sampled[sampled.length - 1];
    if (!end || end[0] !== last[0] || end[1] !== last[1]) sampled.push(last);
    return sampled;
  }

  _densifyPoints(points, settings = {}) {
    const density = this._clamp(Number(settings.pointDensity) || 1, 1, 6);
    if (density <= 1 || points.length < 2) return points;
    const targetSegment = this._clamp(38 / density, 5, 38);
    const out = [points[0]];
    for (let i = 1; i < points.length; i++) {
      const a = points[i - 1];
      const b = points[i];
      const distance = Math.hypot(b[0] - a[0], b[1] - a[1]);
      const steps = Math.max(1, Math.ceil(distance / targetSegment));
      for (let step = 1; step <= steps; step++) {
        const t = step / steps;
        out.push([
          a[0] + (b[0] - a[0]) * t,
          a[1] + (b[1] - a[1]) * t,
        ]);
      }
    }
    return out;
  }

  _meanderPoints(points, cells, grid, settings = {}) {
    if (points.length < 3) return points;
    const seed = settings.seed || 1;
    return points.map((point, i) => {
      if (i === 0 || i === points.length - 1) return point;
      const prev = points[i - 1], next = points[i + 1];
      const dx = next[0] - prev[0], dy = next[1] - prev[1];
      const len = Math.hypot(dx, dy) || 1;
      const nx = -dy / len, ny = dx / len;
      const cell = cells[Math.min(cells.length - 1, Math.round(i / Math.max(1, points.length - 1) * (cells.length - 1)))];
      const meander = this._meanderPotentialAt(grid, cell);
      const t = i / Math.max(1, points.length - 1);
      const falloff = Math.sin(t * Math.PI);
      const phase = i * 1.37 + this._hash(cell + seed * 13, i + seed) * Math.PI * 2;
      const bend = Math.sin(phase) * 0.72 + Math.sin(phase * 0.53 + 1.9) * 0.28;
      const amp = grid.step * (0.52 + meander * 1.90) * bend * falloff;
      const candidate = [point[0] + nx * amp, point[1] + ny * amp];
      if (!this._canBendTo(candidate, cell, grid, meander)) return point;
      return candidate;
    });
  }

  _naturalizeSinuosity(points, cells, grid, settings = {}) {
    if (points.length < 4) return points;
    const seed = settings.seed || 1;
    const target = this._targetSinuosity(cells, grid);
    let out = points.map((point) => [point[0], point[1]]);
    for (let pass = 0; pass < 5; pass++) {
      const current = this._sinuosity(out);
      if (current >= target * 0.985) break;
      const pressure = this._clamp((target - current) * 8.4, 0.34, 1.55);
      out = out.map((point, i) => {
        if (i === 0 || i === out.length - 1) return point;
        const prev = out[Math.max(0, i - 2)];
        const next = out[Math.min(out.length - 1, i + 2)];
        const dx = next[0] - prev[0], dy = next[1] - prev[1];
        const len = Math.hypot(dx, dy) || 1;
        const nx = -dy / len, ny = dx / len;
        const cell = cells[Math.min(cells.length - 1, Math.round(i / Math.max(1, out.length - 1) * (cells.length - 1)))];
        const t = i / Math.max(1, out.length - 1);
        const falloff = Math.sin(t * Math.PI);
        const meander = this._meanderPotentialAt(grid, cell);
        const phase = i * 0.94 + pass * 1.71 + this._hash(cell + seed * 19, pass + seed + 17) * Math.PI * 2;
        const wave = Math.sin(phase) * 0.66 + Math.sin(phase * 0.47 + 2.2) * 0.34;
        const amp = grid.step * (1.45 + meander * 4.4 + pass * 0.55) * pressure * falloff * wave;
        const candidate = [point[0] + nx * amp, point[1] + ny * amp];
        if (!this._canBendTo(candidate, cell, grid, meander)) return point;
        return candidate;
      });
      out = this._relaxTinyKinks(out, cells, grid);
    }
    return out;
  }

  _targetSinuosity(cells, grid) {
    const avg = (name) => cells.reduce((sum, cell) => sum + grid.masks[name][cell], 0) / Math.max(1, cells.length);
    const slope = cells.reduce((sum, cell) => sum + grid.slope[cell], 0) / Math.max(1, cells.length);
    const maxAccum = cells.reduce((best, cell) => Math.max(best, grid.accumulation[cell]), 0);
    const discharge = Math.sqrt(maxAccum / Math.max(1, grid.maxAccumulation));
    const target =
      1.065 +
      avg("lowland") * 0.16 +
      avg("fertile_lowland") * 0.10 +
      avg("farmland") * 0.08 +
      avg("forest") * 0.055 +
      avg("marsh") * 0.28 +
      avg("oasis_wetland") * 0.18 +
      discharge * 0.075 -
      avg("mountain") * 0.07 -
      avg("bare_rock") * 0.05 -
      avg("dryland") * 0.035 -
      slope * 0.22;
    return this._clamp(target, 1.055, 1.58);
  }

  _relaxTinyKinks(points, cells, grid) {
    if (points.length < 5) return points;
    return points.map((point, i) => {
      if (i === 0 || i === points.length - 1) return point;
      const prev = points[i - 1], next = points[i + 1];
      const candidate = [
        point[0] * 0.64 + (prev[0] + next[0]) * 0.18,
        point[1] * 0.64 + (prev[1] + next[1]) * 0.18,
      ];
      const cell = cells[Math.min(cells.length - 1, Math.round(i / Math.max(1, points.length - 1) * (cells.length - 1)))];
      if (!this._canBendTo(candidate, cell, grid, this._meanderPotentialAt(grid, cell))) return point;
      return candidate;
    });
  }

  _canBendTo(point, cell, grid, meander) {
    const [x, y] = point;
    if (x < 0 || y < 0 || x > this.mapSize.width || y > this.mapSize.height) return false;
    const water = this._maskAt("water", x, y);
    if (water > 0.36 && grid.masks.water[cell] < 0.25) return false;
    const mountain = this._maskAt("mountain", x, y);
    if (mountain > 0.76 && grid.masks.mountain[cell] < 0.42 && meander > 0.18) return false;
    const heightJump = Math.abs(this._heightAt(x, y) - grid.height[cell]);
    return heightJump < 0.30;
  }

  _smoothPoints(points, passes) {
    let out = points;
    for (let pass = 0; pass < passes; pass++) {
      if (out.length < 3) return out;
      const next = [out[0]];
      for (let i = 1; i < out.length; i++) {
        const a = out[i - 1], b = out[i];
        next.push([a[0] * 0.72 + b[0] * 0.28, a[1] * 0.72 + b[1] * 0.28]);
        next.push([a[0] * 0.28 + b[0] * 0.72, a[1] * 0.28 + b[1] * 0.72]);
      }
      next[next.length - 1] = out[out.length - 1];
      out = next;
    }
    return out;
  }

  _followOutlet(grid, start) {
    const seen = new Set();
    let current = start;
    for (let i = 0; i < grid.w + grid.h; i++) {
      if (current < 0 || seen.has(current)) return current;
      seen.add(current);
      const next = grid.flowDir[current];
      if (next < 0 || !grid.land[next]) return current;
      current = next;
    }
    return current;
  }

  _connectedProvinces(points) {
    const ids = new Set();
    const stride = Math.max(1, Math.floor(points.length / 24));
    for (let i = 0; i < points.length; i += stride) {
      const id = this.provinceIdAt(points[i][0], points[i][1]);
      if (id) ids.add(id);
    }
    const last = points[points.length - 1];
    const endId = this.provinceIdAt(last[0], last[1]);
    if (endId) ids.add(endId);
    return [...ids];
  }

  _tributaryJoinQuality(cells, grid) {
    const end = cells[cells.length - 1];
    if (grid.masks.water[end] > 0.35 || grid.masks.coast[end] > 0.35) return 1;
    const endAccum = grid.accumulation[end];
    const startAccum = grid.accumulation[cells[0]];
    return this._clamp((endAccum - startAccum) / Math.max(1, endAccum), 0, 1);
  }

  _sourceScore(m, elevation) {
    return this._clamp(
      elevation * 0.70 +
      m.mountain * 0.48 +
      m.highland * 0.30 +
      m.snow_peak * 0.58 +
      m.forest * 0.22 +
      m.marsh * 0.14 +
      m.oasis_wetland * 0.20 -
      m.dryland * 0.18 -
      m.water * 0.90,
      0,
      1.5,
    );
  }

  _precipitationScore(m) {
    return this._clamp(
      1 +
      m.snow_peak * 1.55 +
      m.mountain * 0.66 +
      m.highland * 0.34 +
      m.forest * 0.32 +
      m.marsh * 0.42 +
      m.oasis_wetland * 0.38 +
      m.farmland * 0.10 -
      m.dryland * 0.42 -
      m.steppe * 0.16 -
      m.bare_rock * 0.18,
      0.18,
      3.7,
    );
  }

  _meanderPotentialAt(grid, cell) {
    const m = this._cellMasks(grid, cell);
    return this._clamp(
      m.lowland * 0.42 + m.farmland * 0.22 + m.fertile_lowland * 0.18 +
      m.marsh * 0.35 + m.oasis_wetland * 0.20 -
      grid.slope[cell] * 0.70 - m.mountain * 0.26 - m.bare_rock * 0.20,
      0,
      1,
    );
  }

  _cellMasks(grid, i) {
    const out = {};
    for (const [name, data] of Object.entries(grid.masks)) out[name] = data[i] || 0;
    return out;
  }

  _cellPathWorldLength(grid, cells) {
    let total = 0;
    for (let i = 1; i < cells.length; i++) {
      const [ax, ay] = this._xy(grid, cells[i - 1]);
      const [bx, by] = this._xy(grid, cells[i]);
      total += Math.hypot(bx - ax, by - ay) * grid.step;
    }
    return total;
  }

  _worldLength(points) {
    let total = 0;
    for (let i = 1; i < points.length; i++) total += Math.hypot(points[i][0] - points[i - 1][0], points[i][1] - points[i - 1][1]);
    return total;
  }

  _sinuosity(points) {
    if (!points || points.length < 2) return 1;
    const straight = Math.max(1, Math.hypot(points.at(-1)[0] - points[0][0], points.at(-1)[1] - points[0][1]));
    return this._worldLength(points) / straight;
  }

  _cellCenter(grid, i) {
    const [x, y] = this._xy(grid, i);
    return [
      Math.min(this.mapSize.width, (x + 0.5) * grid.step),
      Math.min(this.mapSize.height, (y + 0.5) * grid.step),
    ];
  }

  _heightAt(x, y) {
    if (!this.heightData) return 0;
    const px = Math.max(0, Math.min(this.mapSize.width - 1, Math.round(x)));
    const py = Math.max(0, Math.min(this.mapSize.height - 1, Math.round(y)));
    return this.heightData[py * this.mapSize.width + px] / 255;
  }

  _maskAt(name, x, y) {
    const data = this.masks[name];
    if (!data) return 0;
    const px = Math.max(0, Math.min(this.mapSize.width - 1, Math.round(x)));
    const py = Math.max(0, Math.min(this.mapSize.height - 1, Math.round(y)));
    return data[py * this.mapSize.width + px] / 255;
  }

  _idx(grid, x, y) {
    if (x < 0 || y < 0 || x >= grid.w || y >= grid.h) return -1;
    return y * grid.w + x;
  }

  _idxClamped(grid, x, y) {
    return Math.max(0, Math.min(grid.h - 1, y)) * grid.w + Math.max(0, Math.min(grid.w - 1, x));
  }

  _xy(grid, i) {
    return [i % grid.w, Math.floor(i / grid.w)];
  }

  _hash(a, b) {
    const s = Math.sin(a * 127.1 + b * 311.7) * 43758.5453123;
    return s - Math.floor(s);
  }

  _clamp(value, min, max) {
    return Math.max(min, Math.min(max, value));
  }

  _round(value, places) {
    const pow = 10 ** places;
    return Math.round(value * pow) / pow;
  }
}

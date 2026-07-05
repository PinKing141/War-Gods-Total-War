const MASK_EXPORTS = [
  "river_core_mask",
  "river_mask",
  "river_bank_mask",
  "floodplain_mask",
  "delta_mask",
  "canal_mask",
  "marsh_channel_mask",
  "oasis_wadi_mask",
  "navigable_river_mask",
  "river_crossing_mask",
];

export class RiverExporter {
  constructor({ mapSize, widthForRiver }) {
    this.mapSize = mapSize;
    this.widthForRiver = widthForRiver;
  }

  exportProject(editor) {
    this.downloadText("river_workbench_project.json", JSON.stringify(editor.toProject(), null, 2));
  }

  exportRiverPaths(rivers) {
    const payload = {
      map_size: [this.mapSize.width, this.mapSize.height],
      rivers: rivers.map((river) => this._logicRiver(river)),
    };
    this.downloadText("river_paths.json", JSON.stringify(payload, null, 2));
  }

  exportWaterwaysCsv(rivers) {
    const header = [
      "id",
      "name",
      "type",
      "width_class",
      "width",
      "navigable",
      "source_province",
      "mouth",
      "connected_provinces",
      "crossings",
      "points",
      "sinuosity",
      "target_sinuosity",
      "gradient",
      "average_slope",
      "source_elevation",
      "mouth_elevation",
      "average_elevation",
      "min_elevation",
      "max_elevation",
      "elevation_drop",
      "uphill_error_score",
      "stream_order",
      "discharge_estimate",
      "source_score",
      "mouth_score",
      "terrain_fit_score",
      "meander_potential",
      "navigability_score",
      "tributary_join_quality",
      "floodplain_fertility",
      "crossing_difficulty",
      "bridge_ford_candidate_score",
      "port_candidate_score",
      "canal_feasibility",
      "marsh_risk",
      "strategic_chokepoint_score",
      "endorheic_score",
      "watershed_id",
      "drainage_basin_cells",
      "notes",
    ];
    const rows = rivers.map((river) => [
      river.id,
      river.name,
      river.type,
      river.width_class,
      this.widthForRiver(river),
      river.navigable ? "true" : "false",
      river.source_province || "",
      river.mouth || "",
      (river.connected_provinces || []).join(";"),
      (river.crossings || []).join(";"),
      (river.points || []).map((pt) => `${Math.round(pt[0])}:${Math.round(pt[1])}`).join("|"),
      river.metrics && river.metrics.sinuosity || "",
      river.metrics && river.metrics.target_sinuosity || "",
      river.metrics && river.metrics.gradient || "",
      river.metrics && river.metrics.average_slope || "",
      river.metrics && river.metrics.source_elevation || "",
      river.metrics && river.metrics.mouth_elevation || "",
      river.metrics && river.metrics.average_elevation || "",
      river.metrics && river.metrics.min_elevation || "",
      river.metrics && river.metrics.max_elevation || "",
      river.metrics && river.metrics.elevation_drop || "",
      river.metrics && river.metrics.uphill_error_score || "",
      river.metrics && river.metrics.stream_order || "",
      river.metrics && river.metrics.discharge_estimate || "",
      river.metrics && river.metrics.source_score || "",
      river.metrics && river.metrics.mouth_score || "",
      river.metrics && river.metrics.terrain_fit_score || "",
      river.metrics && river.metrics.meander_potential || "",
      river.metrics && river.metrics.navigability_score || "",
      river.metrics && river.metrics.tributary_join_quality || "",
      river.metrics && river.metrics.floodplain_fertility || "",
      river.metrics && river.metrics.crossing_difficulty || "",
      river.metrics && river.metrics.bridge_ford_candidate_score || "",
      river.metrics && river.metrics.port_candidate_score || "",
      river.metrics && river.metrics.canal_feasibility || "",
      river.metrics && river.metrics.marsh_risk || "",
      river.metrics && river.metrics.strategic_chokepoint_score || "",
      river.metrics && river.metrics.endorheic_score || "",
      river.metrics && river.metrics.watershed_id || "",
      river.metrics && river.metrics.drainage_basin_cells || "",
      river.notes || "",
    ]);
    const csv = [header, ...rows].map((row) => row.map((value) => this._csvCell(value)).join(",")).join("\n");
    this.downloadText("waterways.csv", csv + "\n");
  }

  exportAllMasks(rivers) {
    for (const name of MASK_EXPORTS) {
      const canvas = this.buildMaskCanvas(rivers, name);
      this.downloadCanvas(`${name}.png`, canvas);
    }
  }

  buildMaskCanvas(rivers, maskName) {
    const canvas = document.createElement("canvas");
    canvas.width = this.mapSize.width;
    canvas.height = this.mapSize.height;
    const ctx = canvas.getContext("2d");
    ctx.fillStyle = "#000";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.lineCap = "round";
    ctx.lineJoin = "round";

    for (const river of rivers) {
      const points = river.points || [];
      if (points.length < 2) continue;
      const base = this.widthForRiver(river);
      const style = this._maskStyle(maskName, river, base);
      if (!style) continue;
      ctx.save();
      ctx.strokeStyle = `rgba(255,255,255,${style.alpha})`;
      ctx.lineWidth = style.width;
      if (style.blur) ctx.filter = `blur(${style.blur}px)`;
      ctx.beginPath();
      points.forEach(([x, y], index) => {
        if (index === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      ctx.stroke();
      ctx.restore();
    }

    if (maskName === "river_crossing_mask") this._drawCrossingMask(ctx, rivers);
    return canvas;
  }

  downloadText(filename, text) {
    const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
    this._downloadBlob(filename, blob);
  }

  downloadCanvas(filename, canvas) {
    canvas.toBlob((blob) => {
      if (blob) this._downloadBlob(filename, blob);
    }, "image/png");
  }

  _logicRiver(river) {
    return {
      id: river.id,
      name: river.name,
      type: river.type,
      width_class: Number(river.width_class),
      width: this.widthForRiver(river),
      navigable: Boolean(river.navigable),
      source_province: river.source_province || "",
      mouth: river.mouth || "",
      connected_provinces: river.connected_provinces || [],
      crossings: river.crossings || [],
      notes: river.notes || "",
      generated_by: river.generated_by || "",
      metrics: river.metrics || {},
      points: (river.points || []).map((pt) => [Math.round(pt[0]), Math.round(pt[1])]),
    };
  }

  _maskStyle(maskName, river, baseWidth) {
    if (maskName === "river_core_mask") return { width: Math.max(2, baseWidth * 0.34), alpha: 1 };
    if (maskName === "river_mask") return { width: baseWidth, alpha: 1 };
    if (maskName === "river_bank_mask") return { width: baseWidth + 18, alpha: 0.70, blur: 3 };
    if (maskName === "floodplain_mask") return { width: baseWidth + 72, alpha: 0.46, blur: 8 };
    if (maskName === "delta_mask") return river.type === "delta" ? { width: baseWidth + 42, alpha: 0.88, blur: 5 } : null;
    if (maskName === "canal_mask") return river.type === "canal" ? { width: baseWidth, alpha: 1 } : null;
    if (maskName === "marsh_channel_mask") return river.type === "marsh_channel" ? { width: baseWidth + 10, alpha: 0.92, blur: 2 } : null;
    if (maskName === "oasis_wadi_mask") return river.type === "oasis_wadi" ? { width: baseWidth + 8, alpha: 0.82, blur: 2 } : null;
    if (maskName === "navigable_river_mask") return river.navigable ? { width: baseWidth, alpha: 1 } : null;
    return null;
  }

  _drawCrossingMask(ctx, rivers) {
    ctx.save();
    ctx.fillStyle = "#fff";
    for (const river of rivers) {
      if (!river.crossings || !river.crossings.length || !river.points || !river.points.length) continue;
      const step = Math.max(1, Math.floor(river.points.length / (river.crossings.length + 1)));
      river.crossings.forEach((_, index) => {
        const point = river.points[Math.min(river.points.length - 1, (index + 1) * step)];
        ctx.beginPath();
        ctx.arc(point[0], point[1], Math.max(8, this.widthForRiver(river) * 0.8), 0, Math.PI * 2);
        ctx.fill();
      });
    }
    ctx.restore();
  }

  _csvCell(value) {
    const text = String(value ?? "");
    if (!/[",\n\r]/.test(text)) return text;
    return `"${text.replace(/"/g, '""')}"`;
  }

  _downloadBlob(filename, blob) {
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
}

export { MASK_EXPORTS };

/* Generate province-level river mechanics from river_paths.json.
   This is the data fallback while visible river art stays optional. */
const fs = require("fs");
const path = require("path");

const ROOT = __dirname;
const RIVER_PATHS = path.join(ROOT, "river_paths.json");
const DEFINITIONS = path.join(ROOT, "..", "provinces", "world_province_definitions.csv");
const OUT = path.join(ROOT, "province_river_features.csv");

const COLUMNS = [
  "province_id",
  "river_ids",
  "river_names",
  "primary_river_id",
  "primary_river_name",
  "river_types",
  "max_width_class",
  "has_major_river",
  "has_tributary",
  "has_canal",
  "has_delta",
  "has_marsh_channel",
  "has_wadi",
  "has_floodplain",
  "has_crossing",
  "river_crossing_type",
  "crossing_ids",
  "navigable_river",
  "river_trade_value",
  "river_defense_bonus",
  "river_movement_penalty",
  "supply_bonus",
  "farmland_bonus",
];

function parseCsv(text) {
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

function csv(value) {
  const text = String(value ?? "");
  return /[",\n\r]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}

function splitList(value) {
  if (Array.isArray(value)) return value.map(String).filter(Boolean);
  return String(value || "")
    .split(/[;,|]/)
    .map((v) => v.trim())
    .filter(Boolean);
}

function bool(value) {
  return value === true || value === 1 || value === "1" || String(value).toLowerCase() === "true";
}

function num(value, fallback = 0) {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}

function widthClass(river) {
  const explicit = num(river.width_class || river.widthClass || river.class, NaN);
  if (Number.isFinite(explicit) && explicit > 0) return Math.max(1, Math.min(5, Math.round(explicit)));
  const width = num(river.width, 0);
  if (width >= 22) return 5;
  if (width >= 15) return 4;
  if (width >= 9) return 3;
  if (width >= 5) return 2;
  return 1;
}

function pointsOf(river) {
  return (river.points || river.path || [])
    .map((pt) => Array.isArray(pt)
      ? { x: num(pt[0], NaN), y: num(pt[1], NaN) }
      : { x: num(pt.x, NaN), y: num(pt.y, NaN) })
    .filter((pt) => Number.isFinite(pt.x) && Number.isFinite(pt.y));
}

function loadDefinitions() {
  const rows = parseCsv(fs.readFileSync(DEFINITIONS, "utf8"));
  const header = rows.shift().map((h) => h.replace(/^\ufeff/, ""));
  const idx = Object.fromEntries(header.map((h, i) => [h, i]));
  return rows.map((row) => ({
    id: row[idx.province_id],
    name: row[idx.common_name],
    terrain: row[idx.terrain],
    biome: idx.biome === undefined ? "" : row[idx.biome],
    terrainFeature: idx.terrain_feature === undefined ? row[idx.terrain] : row[idx.terrain_feature],
    roads: num(row[idx.road_level]),
    port: num(row[idx.port_level]),
    fort: num(row[idx.fort_level]),
    value: num(row[idx.strategic_value]),
    x: num(row[idx.center_x], NaN),
    y: num(row[idx.center_y], NaN),
    pixelArea: num(row[idx.pixel_area], 0),
  })).filter((p) => p.id);
}

function newFeature(province) {
  return {
    province,
    rivers: new Map(),
    types: new Set(),
    crossingIds: new Set(),
    crossingTypes: new Set(),
    maxWidthClass: 0,
    floodplainFertility: 0,
    navigable: false,
    hasFloodplain: false,
  };
}

function nearestProvince(point, provinces) {
  let best = null, bestD2 = Infinity;
  for (const p of provinces) {
    if (!Number.isFinite(p.x) || !Number.isFinite(p.y)) continue;
    const d2 = (point.x - p.x) ** 2 + (point.y - p.y) ** 2;
    if (d2 < bestD2) {
      best = p;
      bestD2 = d2;
    }
  }
  if (!best) return null;
  const radius = Math.sqrt(Math.max(1, best.pixelArea) / Math.PI);
  const limit = Math.max(120, radius * 3.1);
  return Math.sqrt(bestD2) <= limit ? best.id : null;
}

function inferredProvinceIds(river, provinces, validIds) {
  const ids = new Set(splitList(river.connected_provinces).filter((id) => validIds.has(id)));
  const pts = pointsOf(river);
  if (pts.length < 2) return ids;

  const samples = [];
  for (let i = 0; i < pts.length - 1; i++) {
    const a = pts[i], b = pts[i + 1];
    const dist = Math.hypot(b.x - a.x, b.y - a.y);
    const steps = Math.max(1, Math.ceil(dist / 72));
    for (let s = 0; s <= steps; s++) {
      const t = s / steps;
      samples.push({ x: a.x + (b.x - a.x) * t, y: a.y + (b.y - a.y) * t });
    }
  }

  for (const sample of samples) {
    const id = nearestProvince(sample, provinces);
    if (id && validIds.has(id)) ids.add(id);
  }
  return ids;
}

function riverType(river) {
  return String(river.type || "tributary").trim().toLowerCase() || "tributary";
}

function isNavigable(river, cls) {
  const score = num(river.metrics && river.metrics.navigability_score, NaN);
  return bool(river.navigable) || score >= 0.65 || riverType(river) === "canal" || cls >= 5;
}

function hasFloodplain(river, cls) {
  const type = riverType(river);
  const fert = num(river.metrics && river.metrics.floodplain_fertility, 0);
  return fert >= 0.05 || cls >= 4 || type === "delta" || type === "marsh_channel" || type === "canal";
}

function explicitCrossingType(crossings) {
  const text = crossings.join(";").toLowerCase();
  if (!text) return "";
  if (text.includes("bridge") || text.includes("brg")) return "bridge";
  if (text.includes("ferry")) return "ferry";
  if (text.includes("ford")) return "ford";
  return "crossing";
}

function inferredCrossingType(river, province, cls) {
  const crossings = splitList(river.crossings);
  const explicit = explicitCrossingType(crossings);
  if (explicit) return explicit;
  const score = num(river.metrics && river.metrics.bridge_ford_candidate_score, 0);
  const roadValue = province.roads + province.port * 0.6 + province.fort * 0.35 + province.value / 120;
  if (score < 0.40 || roadValue < 3.2) return "";
  if (province.roads >= 4 && cls <= 4) return "bridge";
  if (cls >= 4 && province.port >= 1) return "ferry";
  return "ford";
}

function addRiverFeature(feature, river, province) {
  const id = river.id || "RIVER_UNKNOWN";
  const cls = widthClass(river);
  const type = riverType(river);
  const name = river.name || id;
  const metrics = river.metrics || {};
  feature.rivers.set(id, { id, name, cls, type });
  feature.types.add(type);
  feature.maxWidthClass = Math.max(feature.maxWidthClass, cls);
  feature.navigable = feature.navigable || isNavigable(river, cls);
  feature.hasFloodplain = feature.hasFloodplain || hasFloodplain(river, cls);
  feature.floodplainFertility = Math.max(feature.floodplainFertility, num(metrics.floodplain_fertility, 0));

  const crossingType = inferredCrossingType(river, province, cls);
  if (crossingType) {
    feature.crossingTypes.add(crossingType);
    const explicit = splitList(river.crossings);
    if (explicit.length) {
      for (const id of explicit) feature.crossingIds.add(id);
    } else {
      feature.crossingIds.add(`${river.id || "RIVER"}_${province.id}_${crossingType}`.toUpperCase());
    }
  }
}

function choosePrimary(rivers) {
  return [...rivers.values()].sort((a, b) => b.cls - a.cls || a.id.localeCompare(b.id))[0] || null;
}

function scoreFeature(feature) {
  const p = feature.province;
  const rivers = [...feature.rivers.values()];
  const primary = choosePrimary(feature.rivers);
  const hasRiver = rivers.length > 0;
  const hasMajor = feature.types.has("major_river") || feature.maxWidthClass >= 4;
  const hasTributary = feature.types.has("tributary");
  const hasCanal = feature.types.has("canal");
  const hasDelta = feature.types.has("delta");
  const hasMarsh = feature.types.has("marsh_channel");
  const hasWadi = feature.types.has("wadi") || feature.types.has("oasis_wadi");
  const hasCrossing = feature.crossingTypes.size > 0;

  const trade = hasRiver
    ? Math.round(feature.maxWidthClass * 2 + (hasMajor ? 3 : 0) + (feature.navigable ? 5 : 0) +
        (hasCanal ? 4 : 0) + Math.min(3, p.roads) + Math.min(3, p.port))
    : 0;
  const defense = hasRiver
    ? Math.round(Math.min(12, Math.max(0, feature.maxWidthClass * 1.5 + (hasCrossing ? 2 : 0) + (p.fort >= 3 ? 1 : 0))))
    : 0;
  const movement = hasRiver
    ? Math.round(Math.max(1, feature.maxWidthClass + (hasMarsh || hasDelta ? 2 : 0) - (hasCrossing ? 2 : 0)))
    : 0;
  const supply = hasRiver
    ? Math.round((feature.hasFloodplain ? 2 : 0) + (feature.navigable ? 2 : 0) + (hasCanal ? 2 : 0) + Math.min(3, trade / 6))
    : 0;
  const landKey = `${p.biome || ""}_${p.terrainFeature || p.terrain || ""}`;
  const farmland = hasRiver
    ? Math.round((feature.hasFloodplain ? 2 : 0) + feature.floodplainFertility * 12 +
        (hasCanal ? 2 : 0) + (/farm|grain|oasis|lowland|river/.test(landKey) ? 1 : 0))
    : 0;

  return {
    province_id: p.id,
    river_ids: rivers.map((r) => r.id).join(";"),
    river_names: rivers.map((r) => r.name).join(";"),
    primary_river_id: primary ? primary.id : "",
    primary_river_name: primary ? primary.name : "",
    river_types: [...feature.types].sort().join(";"),
    max_width_class: feature.maxWidthClass || "",
    has_major_river: hasMajor,
    has_tributary: hasTributary,
    has_canal: hasCanal,
    has_delta: hasDelta,
    has_marsh_channel: hasMarsh,
    has_wadi: hasWadi,
    has_floodplain: feature.hasFloodplain,
    has_crossing: hasCrossing,
    river_crossing_type: [...feature.crossingTypes].sort().join(";") || "none",
    crossing_ids: [...feature.crossingIds].sort().join(";"),
    navigable_river: feature.navigable,
    river_trade_value: trade,
    river_defense_bonus: defense,
    river_movement_penalty: movement,
    supply_bonus: supply,
    farmland_bonus: farmland,
  };
}

function main() {
  const rivers = JSON.parse(fs.readFileSync(RIVER_PATHS, "utf8")).rivers || [];
  const provinces = loadDefinitions();
  const validIds = new Set(provinces.map((p) => p.id));
  const features = new Map(provinces.map((p) => [p.id, newFeature(p)]));

  for (const river of rivers) {
    const ids = inferredProvinceIds(river, provinces, validIds);
    if (!ids.size) continue;
    for (const id of ids) addRiverFeature(features.get(id), river, features.get(id).province);
  }

  const rows = [COLUMNS.join(",")];
  for (const province of provinces) {
    const scored = scoreFeature(features.get(province.id));
    rows.push(COLUMNS.map((col) => csv(scored[col])).join(","));
  }
  fs.writeFileSync(OUT, rows.join("\n") + "\n");

  const riverProvinces = [...features.values()].filter((f) => f.rivers.size).length;
  console.log(`Wrote ${path.relative(process.cwd(), OUT)} (${riverProvinces} river provinces, ${rivers.length} source rivers).`);
  console.log("No tile grid file was detected; skipped river_tiles.csv for now.");
}

main();

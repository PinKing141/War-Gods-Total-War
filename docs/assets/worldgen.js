/* World geometry, computed once at page load.
   Heightmap (domain-warped fbm + ridged chains + edge falloff) -> sea level
   coastline -> Lloyd-relaxed Voronoi cells over the map -> the nine lore
   provinces grown outward over the land-cell graph -> hydrological rivers ->
   smoothed vector border/coast polylines. Everything is deterministic from a
   pinned world seed, so the continent is the same on every visit; only the
   simulated history varies. */
(function () {
  "use strict";

  const CELL_COUNT = 3200;
  const LLOYD_ITERS = 2;
  const SEA = -1, OUT = -2;

  /* ------------------------------------------------------------------ */
  /* small geometry helpers                                              */
  /* ------------------------------------------------------------------ */

  function circumcenter(ax, ay, bx, by, cx, cy) {
    const dx = bx - ax, dy = by - ay;
    const ex = cx - ax, ey = cy - ay;
    const bl = dx * dx + dy * dy, cl = ex * ex + ey * ey;
    const d = 0.5 / (dx * ey - dy * ex);
    return [ax + (ey * bl - dy * cl) * d, ay + (dx * cl - ex * bl) * d];
  }

  function polygonCentroid(poly) {
    let a = 0, cx = 0, cy = 0;
    for (let i = 0; i < poly.length; i++) {
      const [x1, y1] = poly[i], [x2, y2] = poly[(i + 1) % poly.length];
      const f = x1 * y2 - x2 * y1;
      a += f; cx += (x1 + x2) * f; cy += (y1 + y2) * f;
    }
    if (Math.abs(a) < 1e-9) return poly[0].slice();
    a *= 0.5;
    return [cx / (6 * a), cy / (6 * a)];
  }

  function chaikin(points, iterations, closed) {
    let pts = points;
    for (let it = 0; it < iterations; it++) {
      const out = [];
      const n = pts.length;
      if (n < 3) return pts;
      if (!closed) out.push(pts[0]);
      const last = closed ? n : n - 1;
      for (let i = 0; i < last; i++) {
        const a = pts[i], b = pts[(i + 1) % n];
        out.push([a[0] * 0.75 + b[0] * 0.25, a[1] * 0.75 + b[1] * 0.25]);
        out.push([a[0] * 0.25 + b[0] * 0.75, a[1] * 0.25 + b[1] * 0.75]);
      }
      if (!closed) out.push(pts[n - 1]);
      pts = out;
    }
    return pts;
  }

  function chainSegments(segs) {
    // Join loose [[x1,y1],[x2,y2]] segments into polylines.
    const key = (p) => (Math.round(p[0] * 4) + ":" + Math.round(p[1] * 4));
    const ends = new Map();
    segs.forEach((s, i) => {
      for (const p of [s[0], s[1]]) {
        const k = key(p);
        if (!ends.has(k)) ends.set(k, []);
        ends.get(k).push(i);
      }
    });
    const used = new Uint8Array(segs.length);
    const paths = [];
    for (let i = 0; i < segs.length; i++) {
      if (used[i]) continue;
      used[i] = 1;
      const path = [segs[i][0].slice(), segs[i][1].slice()];
      let grew = true;
      while (grew) {
        grew = false;
        for (const end of [0, 1]) {
          const tip = path[end === 0 ? 0 : path.length - 1];
          const candidates = ends.get(key(tip)) || [];
          for (const ci of candidates) {
            if (used[ci]) continue;
            const s = segs[ci];
            let next = null;
            if (key(s[0]) === key(tip)) next = s[1];
            else if (key(s[1]) === key(tip)) next = s[0];
            if (!next) continue;
            used[ci] = 1;
            if (end === 0) path.unshift(next.slice());
            else path.push(next.slice());
            grew = true;
            break;
          }
        }
      }
      paths.push(path);
    }
    return paths;
  }

  /* ------------------------------------------------------------------ */
  /* the builder                                                         */
  /* ------------------------------------------------------------------ */

  function buildAttempt(seedData, worldSeed) {
    const W = seedData.world.width, H = seedData.world.height;
    const noise = WG.makeNoise(worldSeed);
    const rng = new WG.Rng(worldSeed);
    const provinces = seedData.provinces;

    /* ---- heightmap ---- */
    const warpAmp = 190;
    function elevAt(x, y) {
      const s = 0.0021;
      const wx = x + (noise.fbm(x * 0.0035 + 31.4, y * 0.0035 + 8.2, 3) - 0.5) * warpAmp;
      const wy = y + (noise.fbm(x * 0.0035 - 12.7, y * 0.0035 + 44.1, 3) - 0.5) * warpAmp;
      const base = noise.fbm(wx * s, wy * s, 5);
      const ridge = noise.ridged(wx * s * 1.7 + 100, wy * s * 1.7 + 100, 4);
      // gentle west-side bias so a mountain spine rises near West Gear
      const westBias = Math.max(0, 1 - Math.abs(x - 260) / 700) * 0.22;
      const fx = Math.min(x, W - x) / (W * 0.30);
      const fy = Math.min(y, H - y) / (H * 0.34);
      const falloff = Math.min(1, Math.min(fx, fy));
      const soft = falloff * falloff * (3 - 2 * falloff);
      // large-scale irregularity so the landmass isn't a rounded rectangle:
      // some map edges push far inland, others recede into open sea
      const lobe = 0.62 + noise.fbm(x * 0.0011 + 7.3, y * 0.0013 + 3.9, 3) * 0.85;
      return Math.max(0, Math.min(1, (base * 0.72 + ridge * (0.34 + westBias)) * soft * lobe));
    }
    const SEA_LEVEL = 0.30;

    /* ---- points, frame, Lloyd-relaxed Voronoi ---- */
    let points = [];
    for (let i = 0; i < CELL_COUNT; i++) points.push([rng.float(6, W - 6), rng.float(6, H - 6)]);
    const frame = [];
    const M = 160;                       // frame ring outside the map
    for (let x = -M; x <= W + M; x += 90) { frame.push([x, -M]); frame.push([x, H + M]); }
    for (let y = -M; y <= H + M; y += 90) { frame.push([-M, y]); frame.push([W + M, y]); }
    const nReal = CELL_COUNT;

    let delaunay, centers, cellPoly;
    function triangulate() {
      const all = points.concat(frame);
      delaunay = window.Delaunator.from(all);
      const { triangles } = delaunay;
      centers = new Array(triangles.length / 3);
      for (let t = 0; t < centers.length; t++) {
        const a = all[triangles[3 * t]], b = all[triangles[3 * t + 1]], c = all[triangles[3 * t + 2]];
        centers[t] = circumcenter(a[0], a[1], b[0], b[1], c[0], c[1]);
      }
      // one incoming halfedge per point
      const inedge = new Int32Array(all.length).fill(-1);
      for (let e = 0; e < triangles.length; e++) {
        const endpoint = triangles[e % 3 === 2 ? e - 2 : e + 1];
        if (inedge[endpoint] === -1 || delaunay.halfedges[e] === -1) inedge[endpoint] = e;
      }
      cellPoly = (i) => {
        const poly = [];
        const start = inedge[i];
        if (start === -1) return poly;
        let incoming = start;
        do {
          poly.push(centers[Math.floor(incoming / 3)]);
          const outgoing = incoming % 3 === 2 ? incoming - 2 : incoming + 1;
          incoming = delaunay.halfedges[outgoing];
        } while (incoming !== -1 && incoming !== start);
        return poly;
      };
    }
    triangulate();
    for (let it = 0; it < LLOYD_ITERS; it++) {
      const moved = [];
      for (let i = 0; i < nReal; i++) {
        const poly = cellPoly(i);
        moved.push(poly.length >= 3 ? polygonCentroid(poly) : points[i]);
      }
      points = moved.map(([x, y]) => [Math.max(4, Math.min(W - 4, x)), Math.max(4, Math.min(H - 4, y))]);
      triangulate();
    }

    /* ---- cells ---- */
    const cells = [];
    for (let i = 0; i < nReal; i++) {
      const poly = cellPoly(i);
      const [cx, cy] = poly.length >= 3 ? polygonCentroid(poly) : points[i];
      const e = elevAt(cx, cy);
      cells.push({
        idx: i, x: cx, y: cy, poly,
        elev: e, land: e > SEA_LEVEL,
        neighbors: [], prov: SEA, coastDist: -1, riverAcc: 0,
      });
    }
    // neighbors from Delaunay edges between real points
    const { triangles, halfedges } = delaunay;
    for (let e = 0; e < triangles.length; e++) {
      if (e > halfedges[e] && halfedges[e] !== -1) continue;   // visit each edge once
      const a = triangles[e], b = triangles[e % 3 === 2 ? e - 2 : e + 1];
      if (a < nReal && b < nReal) {
        cells[a].neighbors.push(b);
        cells[b].neighbors.push(a);
      }
    }
    for (const c of cells) if (!c.land) c.prov = SEA;

    /* ---- coast distance (in cells) for shelf shading ---- */
    {
      const queue = [];
      for (const c of cells) {
        const coastal = c.neighbors.some((n) => cells[n].land !== c.land);
        if (coastal) { c.coastDist = 0; queue.push(c.idx); }
      }
      let head = 0;
      while (head < queue.length) {
        const c = cells[queue[head++]];
        for (const n of c.neighbors) {
          if (cells[n].coastDist === -1) {
            cells[n].coastDist = c.coastDist + 1;
            queue.push(n);
          }
        }
      }
    }

    /* ---- anchor snapping ---- */
    const landCells = cells.filter((c) => c.land);
    if (!landCells.length) return null;
    function nearest(x, y, filter) {
      let best = null, bd = Infinity;
      for (const c of landCells) {
        if (filter && !filter(c)) continue;
        const d = (c.x - x) ** 2 + (c.y - y) ** 2;
        if (d < bd) { bd = d; best = c; }
      }
      return best ? { cell: best, dist: Math.sqrt(bd) } : null;
    }
    const anchors = [];
    for (let pi = 0; pi < provinces.length; pi++) {
      const p = provinces[pi];
      let found;
      if (p.id === "PROV_BLUE_CHAIN") {
        found = nearest(p.x, p.y, (c) => c.coastDist <= 1) || nearest(p.x, p.y);
      } else if (p.id === "PROV_WEST_GEAR") {
        // highest cell in the neighbourhood — the pass sits on the spine
        let best = null, bs = -1;
        for (const c of landCells) {
          const d = Math.hypot(c.x - p.x, c.y - p.y);
          if (d > 300) continue;
          const score = c.elev - d / 2200;
          if (score > bs) { bs = score; best = c; }
        }
        found = best ? { cell: best, dist: Math.hypot(best.x - p.x, best.y - p.y) } : nearest(p.x, p.y);
      } else {
        found = nearest(p.x, p.y);
      }
      if (!found || found.dist > 340) return null;
      if (anchors.some((a) => a.cell === found.cell)) return null;  // collision
      anchors.push({ prov: pi, cell: found.cell });
    }

    /* ---- province growth: multi-source Dijkstra over land cells ---- */
    const westGearIdx = provinces.findIndex((p) => p.id === "PROV_WEST_GEAR");
    const dist = new Float64Array(cells.length).fill(Infinity);
    const heap = [];   // simple binary heap of [cost, cellIdx, provIdx]
    function hpush(item) {
      heap.push(item);
      let i = heap.length - 1;
      while (i > 0) {
        const par = (i - 1) >> 1;
        if (heap[par][0] <= heap[i][0]) break;
        [heap[par], heap[i]] = [heap[i], heap[par]]; i = par;
      }
    }
    function hpop() {
      const top = heap[0], end = heap.pop();
      if (heap.length) {
        heap[0] = end;
        let i = 0;
        for (;;) {
          const l = 2 * i + 1, r = l + 1;
          let s = i;
          if (l < heap.length && heap[l][0] < heap[s][0]) s = l;
          if (r < heap.length && heap[r][0] < heap[s][0]) s = r;
          if (s === i) break;
          [heap[s], heap[i]] = [heap[i], heap[s]]; i = s;
        }
      }
      return top;
    }
    for (const a of anchors) { dist[a.cell.idx] = 0; hpush([0, a.cell.idx, a.prov]); }
    while (heap.length) {
      const [d, ci, pi] = hpop();
      if (d > dist[ci]) continue;
      cells[ci].prov = pi;
      const sizeBias = 1 / (0.78 + provinces[pi].value / 300);
      for (const ni of cells[ci].neighbors) {
        const n = cells[ni];
        if (!n.land) continue;
        const mountain = Math.max(0, (n.elev - 0.58) / 0.42);
        const penalty = pi === westGearIdx ? 1 + mountain * 1.2 : 1 + mountain * mountain * 8;
        const step = Math.hypot(n.x - cells[ci].x, n.y - cells[ci].y) * penalty * sizeBias;
        if (d + step < dist[ni]) { dist[ni] = d + step; hpush([d + step, ni, pi]); }
      }
    }
    // stranded islands: hand them to the nearest anchor so no land is unowned
    for (const c of landCells) {
      if (c.prov !== SEA) continue;
      let best = 0, bd = Infinity;
      for (const a of anchors) {
        const d = (a.cell.x - c.x) ** 2 + (a.cell.y - c.y) ** 2;
        if (d < bd) { bd = d; best = a.prov; }
      }
      c.prov = best;
    }
    const sizes = new Array(provinces.length).fill(0);
    for (const c of landCells) sizes[c.prov]++;
    if (sizes.some((s) => s < 5)) return null;

    /* ---- rivers: downhill flow accumulation ---- */
    const bySlope = [...landCells].sort((a, b) => b.elev - a.elev);
    const downhill = new Int32Array(cells.length).fill(-1);
    for (const c of landCells) {
      let best = -1, be = c.elev;
      for (const ni of c.neighbors) {
        if (cells[ni].elev < be) { be = cells[ni].elev; best = ni; }
      }
      downhill[c.idx] = best;
    }
    for (const c of bySlope) {
      c.riverAcc += 1;
      const d = downhill[c.idx];
      if (d !== -1) cells[d].riverAcc += c.riverAcc;
    }
    const riverPaths = [];
    const mouths = landCells
      .filter((c) => c.coastDist === 0 && c.riverAcc > 26)
      .sort((a, b) => b.riverAcc - a.riverAcc);
    const usedMouths = [];
    for (const mouth of mouths) {
      if (riverPaths.length >= 5) break;
      if (usedMouths.some((m) => Math.hypot(m.x - mouth.x, m.y - mouth.y) < 260)) continue;
      // walk upstream along the strongest inflow
      const path = [[mouth.x, mouth.y]];
      let cur = mouth;
      const seen = new Set([mouth.idx]);
      for (;;) {
        let next = null, ba = 12;
        for (const ni of cur.neighbors) {
          const n = cells[ni];
          if (!n.land || seen.has(ni)) continue;
          if (downhill[ni] === cur.idx && n.riverAcc > ba) { ba = n.riverAcc; next = n; }
        }
        if (!next) break;
        seen.add(next.idx);
        path.push([next.x, next.y]);
        cur = next;
      }
      if (path.length >= 5) {
        // extend the mouth into the sea slightly so rivers visibly reach water
        const seaN = mouth.neighbors.map((i) => cells[i]).find((n) => !n.land);
        if (seaN) path.unshift([(mouth.x + seaN.x) / 2, (mouth.y + seaN.y) / 2]);
        riverPaths.push({ path: chaikin(path, 2, false), size: Math.sqrt(mouth.riverAcc) });
        usedMouths.push(mouth);
      }
    }

    /* ---- vector borders & coastline ---- */
    const borderSegsByPair = new Map();  // "a|b" (a<b, prov idx) -> segments
    const coastSegs = [];
    const outlineSegs = provinces.map(() => []);   // full boundary per province
    for (let e = 0; e < triangles.length; e++) {
      const o = halfedges[e];
      if (o !== -1 && e > o) continue;
      const a = triangles[e], b = triangles[e % 3 === 2 ? e - 2 : e + 1];
      if (a >= nReal || b >= nReal) continue;
      const pa = cells[a].land ? cells[a].prov : SEA;
      const pb = cells[b].land ? cells[b].prov : SEA;
      if (pa === pb) continue;
      if (o === -1) continue;
      const seg = [centers[Math.floor(e / 3)], centers[Math.floor(o / 3)]];
      if (Math.hypot(seg[0][0] - seg[1][0], seg[0][1] - seg[1][1]) < 0.01) continue;
      if (pa >= 0) outlineSegs[pa].push(seg);
      if (pb >= 0) outlineSegs[pb].push(seg);
      if (pa === SEA || pb === SEA) { coastSegs.push(seg); continue; }
      const k = Math.min(pa, pb) + "|" + Math.max(pa, pb);
      if (!borderSegsByPair.has(k)) borderSegsByPair.set(k, []);
      borderSegsByPair.get(k).push(seg);
    }
    const borderPaths = [];
    for (const [k, segs] of borderSegsByPair) {
      const [a, b] = k.split("|").map(Number);
      for (const path of chainSegments(segs)) {
        borderPaths.push({ a, b, path: chaikin(path, 2, false) });
      }
    }
    const coastPaths = chainSegments(coastSegs).map((p) => {
      const closed = Math.hypot(p[0][0] - p[p.length - 1][0], p[0][1] - p[p.length - 1][1]) < 3;
      return { path: chaikin(p, 2, closed), closed };
    });
    const provOutlines = outlineSegs.map((segs) =>
      chainSegments(segs).map((p) => {
        const closed = Math.hypot(p[0][0] - p[p.length - 1][0], p[0][1] - p[p.length - 1][1]) < 3;
        return chaikin(p, 2, closed);
      }));

    /* ---- province visual centroids, adjacency, land fraction ---- */
    const adjacency = {};
    provinces.forEach((p) => { adjacency[p.id] = new Set(); });
    for (const c of landCells) {
      for (const ni of c.neighbors) {
        const n = cells[ni];
        if (n.land && n.prov !== c.prov) {
          adjacency[provinces[c.prov].id].add(provinces[n.prov].id);
          adjacency[provinces[n.prov].id].add(provinces[c.prov].id);
        }
      }
    }
    const adjOut = {};
    for (const key of Object.keys(adjacency)) adjOut[key] = [...adjacency[key]];

    const centroids = provinces.map(() => [0, 0, 0]);
    for (const c of landCells) {
      centroids[c.prov][0] += c.x; centroids[c.prov][1] += c.y; centroids[c.prov][2]++;
    }
    // pick the owned cell nearest the mean so anchors always sit inside the realm
    const provinceAnchors = provinces.map((p, pi) => {
      const [sx, sy, n] = centroids[pi];
      const mx = sx / n, my = sy / n;
      let best = null, bd = Infinity;
      for (const c of landCells) {
        if (c.prov !== pi) continue;
        const d = (c.x - mx) ** 2 + (c.y - my) ** 2;
        if (d < bd) { bd = d; best = c; }
      }
      return [best.x, best.y];
    });

    const landFraction = landCells.length / cells.length;
    if (landFraction < 0.34 || landFraction > 0.72) return null;

    /* ---- spatial hash for hit-testing (nearest cell point = Voronoi) ---- */
    const HASH = 64;
    const hashW = Math.ceil(W / HASH), hashH = Math.ceil(H / HASH);
    const buckets = new Array(hashW * hashH);
    for (let i = 0; i < nReal; i++) {
      const bx = Math.min(hashW - 1, Math.max(0, Math.floor(points[i][0] / HASH)));
      const by = Math.min(hashH - 1, Math.max(0, Math.floor(points[i][1] / HASH)));
      const bi = by * hashW + bx;
      (buckets[bi] = buckets[bi] || []).push(i);
    }
    function cellAt(x, y) {
      const bx = Math.min(hashW - 1, Math.max(0, Math.floor(x / HASH)));
      const by = Math.min(hashH - 1, Math.max(0, Math.floor(y / HASH)));
      let best = -1, bd = Infinity;
      for (let dy = -1; dy <= 1; dy++) {
        for (let dx = -1; dx <= 1; dx++) {
          const nx = bx + dx, ny = by + dy;
          if (nx < 0 || ny < 0 || nx >= hashW || ny >= hashH) continue;
          for (const i of (buckets[ny * hashW + nx] || [])) {
            const d = (points[i][0] - x) ** 2 + (points[i][1] - y) ** 2;
            if (d < bd) { bd = d; best = i; }
          }
        }
      }
      return best === -1 ? null : cells[best];
    }

    return {
      W, H, cells, landCells, elevAt, seaLevel: SEA_LEVEL,
      riverPaths, borderPaths, coastPaths, provOutlines,
      adjacency: adjOut, provinceAnchors, cellAt, landFraction,
    };
  }

  function buildWorld(seedData, worldSeed) {
    for (let attempt = 0; attempt < 14; attempt++) {
      const world = buildAttempt(seedData, worldSeed + attempt * 7919);
      if (world) {
        world.seedUsed = worldSeed + attempt * 7919;
        // move province anchor coordinates to their visual centroids so labels,
        // army markers, fx and camera focus all sit inside the real territory
        seedData.provinces.forEach((p, pi) => {
          p.x = Math.round(world.provinceAnchors[pi][0]);
          p.y = Math.round(world.provinceAnchors[pi][1]);
        });
        return world;
      }
    }
    throw new Error("worldgen: no valid world found from seed " + worldSeed);
  }

  window.WG = window.WG || {};
  window.WG.buildWorld = buildWorld;
})();

/* Bootstrap: wire the map, the simulation and the UI together and run the
   observer clock. There is deliberately no other input into the world. */
(async function () {
  "use strict";

  const SPEEDS = [
    { label: "1x", ms: 500 },
    { label: "2x", ms: 250 },
    { label: "3x", ms: 110 },
    { label: "4x", ms: 40 },
  ];

  const seed = window.WG_SEED;
  const canvas = document.getElementById("map");
  // every visit births a different history; pin ?seed=N to replay one
  const params = new URLSearchParams(location.search);
  const useOldMap = params.has("oldMap");

  function loadScript(src) {
    return new Promise((resolve, reject) => {
      const script = document.createElement("script");
      const cacheSep = src.includes("?") ? "&" : "?";
      script.src = `${src}${cacheSep}v=old-map-debug-20260708`;
      script.onload = resolve;
      script.onerror = () => reject(new Error(`Unable to load ${src}`));
      document.body.appendChild(script);
    });
  }

  function proceduralMapCtor() {
    return WG.ProceduralWorldMap || WG.WorldMap || null;
  }

  async function loadProceduralMap() {
    await loadScript("assets/map_procedural_old.js");
    let Ctor = proceduralMapCtor();
    if (!Ctor) {
      await loadScript("assets/map.js");
      Ctor = proceduralMapCtor();
    }
    if (!Ctor) {
      throw new Error("Debug old map constructor is unavailable.");
    }
    return new Ctor(canvas, seed);
  }

  function showMapBootError(err) {
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.parentElement.getBoundingClientRect();
    canvas.width = Math.floor(rect.width * dpr);
    canvas.height = Math.floor(rect.height * dpr);
    canvas.style.width = rect.width + "px";
    canvas.style.height = rect.height + "px";

    const ctx = canvas.getContext("2d");
    ctx.save();
    ctx.fillStyle = "#14262d";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.textAlign = "center";
    ctx.fillStyle = "rgba(246, 233, 198, 0.92)";
    ctx.font = `700 ${Math.max(18, 24 * dpr)}px Georgia, serif`;
    ctx.fillText("Map assets could not load", canvas.width / 2, canvas.height / 2 - 28 * dpr);
    ctx.font = `500 ${Math.max(12, 15 * dpr)}px Georgia, serif`;
    const detail = location.protocol === "file:"
      ? "Open this through the local server: http://127.0.0.1:8765/"
      : String((err && err.message) || err || "Unknown map startup error");
    ctx.fillText(detail, canvas.width / 2, canvas.height / 2 + 8 * dpr);
    ctx.fillStyle = "rgba(238, 214, 140, 0.72)";
    ctx.font = `500 ${Math.max(11, 13 * dpr)}px Georgia, serif`;
    ctx.fillText("Debug old map: add ?oldMap=1", canvas.width / 2, canvas.height / 2 + 34 * dpr);
    ctx.restore();
  }

  function isMemoryStartupError(err) {
    const text = String((err && (err.message || err.name)) || err || "").toLowerCase();
    return text.includes("out of memory") ||
      text.includes("allocation") ||
      text.includes("array buffer") ||
      text.includes("canvas");
  }

  async function createMap() {
    if (useOldMap) {
      return loadProceduralMap();
    }

    try {
      const layered = new WG.LayeredWorldMap(canvas, seed);
      if (layered.ready) await layered.ready;
      return layered;
    } catch (err) {
      if (!isMemoryStartupError(err)) throw err;
      console.warn("Layered map ran out of memory; falling back to the procedural map.", err);
      const fallback = await loadProceduralMap();
      fallback.layerFallbackReason = err;
      return fallback;
    }
  }

  let map;
  try {
    map = await createMap();
  } catch (err) {
    console.error("Map startup failed.", err);
    showMapBootError(err);
    window.__wgLoadError = err;
    return;
  }

  const pinned = params.get("seed");
  const rngSeed = pinned ? Number(pinned) : (Date.now() ^ (Math.random() * 0xffffffff)) >>> 0;
  const sim = new WG.Simulation(seed, rngSeed);
  sim.adjacency = map.adjacency;
  const ui = new WG.UI(sim, map);

  let paused = false;
  let speedIdx = 0;
  let timer = null;
  let overlayDirty = true;
  let paintedVersion = -1;

  function applySpeed() {
    if (timer) { clearInterval(timer); timer = null; }
    if (!paused) {
      timer = setInterval(() => {
        sim.tick();
        if (sim.mapVersion !== paintedVersion) {   // repaint only on real change
          paintedVersion = sim.mapVersion;
          map.markDirty();
        }
        overlayDirty = true;
        ui.renderClock();
        if (sim.date.day === 1) {
          ui.renderShieldStrip();
          if (ui.chronMode === "recap") ui.renderRecapTab();
        }
      }, SPEEDS[speedIdx].ms);
    }
    document.getElementById("btn-pause").textContent = paused ? "▶" : "⏸";
    const pips = document.querySelectorAll("#speed-pips i");
    pips.forEach((pip, i) => pip.classList.toggle("on", i <= speedIdx));
  }

  document.getElementById("btn-pause").addEventListener("click", () => {
    paused = !paused; applySpeed();
  });
  document.getElementById("btn-slower").addEventListener("click", () => {
    speedIdx = Math.max(0, speedIdx - 1); applySpeed();
  });
  document.getElementById("btn-faster").addEventListener("click", () => {
    speedIdx = Math.min(SPEEDS.length - 1, speedIdx + 1); applySpeed();
  });
  window.addEventListener("keydown", (ev) => {
    if (ev.code === "Space" && !ev.target.closest("button")) {
      ev.preventDefault(); paused = !paused; applySpeed();
    }
  });
  document.getElementById("btn-world").addEventListener("click", () => ui.openWorld());
  document.getElementById("map-modes").addEventListener("click", (ev) => {
    const btn = ev.target.closest("[data-mode]");
    if (!btn) return;
    const mode = map.mapMode === btn.dataset.mode ? "neutral" : btn.dataset.mode;
    map.setMode(mode);
    for (const b of document.querySelectorAll("#map-modes [data-mode]")) {
      b.classList.toggle("active", mode === b.dataset.mode);
    }
  });

  function setupMaskDebugPanel() {
    const enabled = params.get("debug") === "masks" || params.has("maskDebug");
    const panel = document.getElementById("mask-debug-panel");
    if (!enabled || !panel || !map.setDebugMask || !map.debugMaskOptions) return;
    panel.innerHTML = map.debugMaskOptions.map((mask) =>
      `<button data-mask="${mask.id}">${mask.label}</button>`).join("");
    panel.classList.remove("hidden");
    panel.addEventListener("click", (ev) => {
      const btn = ev.target.closest("[data-mask]");
      if (!btn) return;
      const active = map.setDebugMask(btn.dataset.mask);
      for (const b of panel.querySelectorAll("[data-mask]")) {
        b.classList.toggle("active", b.dataset.mask === active);
      }
    });
  }
  setupMaskDebugPanel();

  const overlayEl = document.getElementById("overlay");
  let animPauseTimer = null;
  const PROVINCE_CLICK_ZOOM = 1.25;
  function controllerOf(prov) {
    const st = map.provinceState ? map.provinceState(prov, sim) : sim.provinceState[prov.id];
    return (st && st.controller) || prov.controller;
  }

  function clickMapProvince(prov) {
    if (!prov) {
      ui.closePanel();
      return;
    }
    const controller = controllerOf(prov);
    const zoomedIn = map.view.zoom >= PROVINCE_CLICK_ZOOM;
    const drillingIntoSelectedRealm = map.selectedRealm === controller;
    if (!zoomedIn && controller && !drillingIntoSelectedRealm) ui.openRealm(controller);
    else ui.openProvince(prov.id);
  }

  map.attach(document.getElementById("map-wrap"), {
    onHover: (prov, ev, w) => {
      ui.tooltip(prov, ev);
      ui.mapDebug(w);
    },
    onClick: (prov) => clickMapProvince(prov),
    onViewChange: () => {
      overlayDirty = true;
      // suppress marker slide animation while the camera itself moves
      overlayEl.classList.add("no-anim");
      clearTimeout(animPauseTimer);
      animPauseTimer = setTimeout(() => overlayEl.classList.remove("no-anim"), 220);
    },
  });

  function frame() {
    map.render(sim);
    if (overlayDirty) { ui.renderOverlay(); overlayDirty = false; }
    requestAnimationFrame(frame);
  }

  function resize() { map.resize(); map.markDirty(); overlayDirty = true; }
  window.addEventListener("resize", resize);

  resize();
  ui.renderClock();
  ui.renderShieldStrip();
  sim.log(2, "muster",
    `The chronicle opens on the ${seed.world.region}: eight powers, old claims, and no hand to stay them.`,
    {});
  applySpeed();
  frame();

  // expose for debugging / verification only — the page never calls this
  window.__wg = { sim, map, ui, setPaused(v) { paused = v; applySpeed(); } };
})();

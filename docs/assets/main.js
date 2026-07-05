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
  const map = new (WG.LayeredWorldMap || WG.WorldMap)(canvas, seed);
  if (map.ready) await map.ready;
  // every visit births a different history; pin ?seed=N to replay one
  const pinned = new URLSearchParams(location.search).get("seed");
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
        if (sim.date.day === 1) ui.renderShieldStrip();
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
    map.setMode(btn.dataset.mode);
    for (const b of document.querySelectorAll("#map-modes [data-mode]")) {
      b.classList.toggle("active", b === btn);
    }
  });

  const overlayEl = document.getElementById("overlay");
  let animPauseTimer = null;
  map.attach(document.getElementById("map-wrap"), {
    onHover: (prov, ev) => ui.tooltip(prov, ev),
    onClick: (prov) => { if (prov) ui.openProvince(prov.id); },
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

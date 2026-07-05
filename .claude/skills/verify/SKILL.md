# Verify — War Gods Total War

## Web observer app (docs/)

Fully static, plain-script (no modules), so it loads from `file://`.

- Launch: Playwright Chromium at
  `/opt/pw-browsers/chromium-1194/chrome-linux/chrome` (require playwright
  from `/opt/node22/lib/node_modules/playwright`), goto
  `file:///home/user/War-Gods-Total-War/docs/index.html`, viewport 1600x900.
- The page exposes `window.__wg = { sim, map, ui, setPaused }` for
  verification only. Fast-forward with `for (...) sim.tick()` then call
  `map.markDirty(); ui.renderClock(); ui.renderShieldStrip(); ui.renderOverlay()`.
- Flows worth driving: click a province on canvas (compute coords via
  `map.worldToScreen(p.x, p.y) / devicePixelRatio`), click a shield in
  `#shield-strip [data-open-realm=...]`, click `.ruler-card`, switch to the
  Wars tab and click a row, hover for `#tooltip`, drag-pan + wheel-zoom then
  click again.
- Healthy 12-year world: several wars, dozens of battles, sieges, at least one
  cession, 1-2 successions, >0 `magic` events, 0 page errors.
- Regenerate seed after lore CSV edits: `python scripts/export_web_seed.py`.

## Desktop Qt app

- Deps: `pip install -r requirements.txt`; needs
  `apt-get install libegl1 libgl1 libxkbcommon0 libdbus-1-3 libfontconfig1`.
- Run headless with `QT_QPA_PLATFORM=offscreen`; build `MainWindow` around
  `CampaignService(WarfareSimulationApp(...))`, call `service.advance_day()`,
  `window.refresh()`, and `window.grab().save(...)` for a screenshot.

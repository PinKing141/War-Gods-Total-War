# Old map decommission plan

## Decision

Do not delete `docs/assets/map.js` immediately.

The current layered map still depends on the old map file because `WG.LayeredWorldMap` extends `WG.WorldMap` and calls `super(canvas, seed)`. The old file is acting as the base camera/input/map utility class as well as the old procedural renderer.

## Problem

The old procedural map can still interfere with development if it remains mixed with the new layered map.

Current web load order:

```html
<script src="assets/map.js"></script>
<script src="assets/map_layers.js"></script>
```

Current map creation:

```js
const map = new (WG.LayeredWorldMap || WG.WorldMap)(canvas, seed);
```

This means the old map cannot simply be removed yet unless the shared camera/input/base methods are extracted or replaced.

## Correct approach

Decommission the old map in stages.

```text
1. Extract shared map base behaviour out of map.js.
2. Make LayeredWorldMap depend on the new base file, not the old procedural renderer.
3. Keep the old procedural map as an archived fallback/debug file.
4. Stop loading the old procedural renderer on the main page.
5. Delete it only after tests and the web app confirm it is unused.
```

## Target files

```text
docs/assets/map_base.js        = camera, pan/zoom, attach, resize, world/screen conversion, shared helpers
docs/assets/map_layers.js      = real layered 3072x2048 map
docs/assets/map_procedural_old.js = archived old procedural map fallback/debug only
```

## Main page target load order

```html
<script src="assets/map_base.js"></script>
<script src="assets/map_layers.js"></script>
<script src="assets/sim.js"></script>
<script src="assets/ui.js"></script>
<script src="assets/main.js"></script>
```

Do not load `map_procedural_old.js` in normal gameplay.

## Main map creation target

```js
const map = new WG.LayeredWorldMap(canvas, seed);
```

No fallback to `WG.WorldMap` in normal mode.

Optional debug fallback later:

```js
const useOldMap = new URLSearchParams(location.search).has("oldMap");
const map = useOldMap && WG.ProceduralWorldMap
  ? new WG.ProceduralWorldMap(canvas, seed)
  : new WG.LayeredWorldMap(canvas, seed);
```

## Acceptance tests

```text
main page loads without map.js
LayeredWorldMap works with pan/zoom/click/hover
province clicking still uses RGB province map
army markers still use province centers
map debug overlay still works
no old cellOwner procedural ownership generation is used for final province selection
sim.adjacency still receives the layered adjacency
old screenshot/procedural map no longer appears in normal app
```

## Immediate Codex task

```text
Decommission the old procedural map without breaking the new layered map.

Tasks:
1. Audit docs/assets/map.js and identify the shared base methods LayeredWorldMap still needs.
2. Create docs/assets/map_base.js containing only shared map infrastructure:
   - constructor basics
   - resize
   - pan/zoom camera
   - worldToScreen
   - screenToWorld
   - attach hover/click handlers
   - selected/hover state helpers
   - markDirty
3. Update docs/assets/map_layers.js so LayeredWorldMap extends WG.MapBase instead of WG.WorldMap.
4. Rename or copy the old procedural map implementation to docs/assets/map_procedural_old.js as WG.ProceduralWorldMap.
5. Update docs/index.html so normal gameplay loads map_base.js and map_layers.js, not map.js.
6. Update docs/assets/main.js so normal gameplay requires WG.LayeredWorldMap.
7. Add optional ?oldMap debug fallback only if needed.
8. Confirm the normal app never uses procedural cellOwner ownership for final map picking.
9. Do not delete the archived old map file until the new load path is tested.
```

# Map polish next pass

This is the next pass after generating the terrain masks.

## Goal

Turn the terrain masks into an actual good-looking in-game map instead of only having mask files sitting in the repo.

## Pass 1: integrate masks into the renderer

Tasks:

1. Load the mask PNGs in the web map asset loader.
2. Blend terrain colors using masks, not flat province colors.
3. Use forest, marsh, dryland, farmland, steppe, mountain, bare rock and snow masks.
4. Keep province clicking on the unique-RGB province map.
5. Add a debug mode that can toggle each mask on/off.
6. Add a terrain preview mode that shows the terrain without political tint.

Acceptance test:

- The map should still be clickable.
- Provinces should still select correctly.
- The terrain should visibly show forests, drylands, marshes, mountains, coasts and highlands.
- Political mode should tint the terrain rather than replacing it with flat color.

## Pass 2: remove ugly prototype rivers

Tasks:

1. Disable seed.rivers drawing by default.
2. Create assets/maps/rivers/river_paths.json.
3. Add river_renderer.js.
4. Draw rivers in passes: riverbed shadow, water stroke, highlight and wet bank tint.
5. Add major rivers only first: no random generated spaghetti.
6. Add canals only where lore supports them, especially Rov Basin and Sevrin Canal.

Acceptance test:

- No random blue line should appear.
- Major waterways should look intentional and strategic.
- Rivers should not break province clicking.

## Pass 3: roads and trade routes

Tasks:

1. Create assets/maps/routes/road_paths.json.
2. Add old imperial Stone Roads first.
3. Add smaller trade roads only after major roads look good.
4. Roads should follow passes, river crossings, ports, cities and province centers.
5. Roads should render below borders but above terrain.

Acceptance test:

- Roads make strategic sense.
- Roads connect important provinces, ports, passes and capitals.
- Roads do not clutter the map at far zoom.

## Pass 4: icons and feature points

Tasks:

1. Add ports, bridges, forts, passes, cities and mana sites as feature files.
2. Render icons only when zoomed in enough.
3. Make icons readable but not cartoonish.
4. Add hover data later.

Acceptance test:

- Ports appear only on coasts or navigable rivers.
- Bridges appear only where roads cross major rivers.
- Forts appear only where fort level is high enough.
- Passes appear only in mountain/highland regions.

## Pass 5: map usability polish

Tasks:

1. Reduce province border harshness.
2. Improve label priority and collision rules.
3. Hide minor labels when zoomed out.
4. Keep realm names readable without covering terrain.
5. Add a screenshot/debug hotkey for comparing map modes.

## Immediate Codex task

Implement Pass 1 only:

```text
Load the generated terrain masks and blend them into the web map renderer.
Do not add new rivers, roads or icons yet.
Make political mode tint the terrain instead of replacing it.
Keep province picking based on the unique-RGB province map.
Add a debug mask toggle panel for forest, marsh, dryland, farmland, steppe, mountain, bare rock, snow and coast masks.
```

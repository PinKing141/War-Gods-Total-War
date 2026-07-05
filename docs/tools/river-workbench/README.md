# River Workbench

Standalone private river editor for War Gods Total War.

Open from the docs server:

```text
http://127.0.0.1:8766/tools/river-workbench/
```

## MVP Scope

This version is the standalone editor plus the first deterministic hydrology simulator. It loads the world map assets, lets you create and edit vector river paths, can generate a first-pass river network, validates basic data, and exports game-ready JSON, CSV, and mask PNG files.

It does not modify the normal observer map.

## Inputs

The workbench reads:

```text
docs/assets/heightmaps/world_heightmap_3072x2048_16bit.png
docs/assets/provinces/world_provinces_unique_rgb_3072x2048.png
docs/assets/provinces/world_province_definitions.csv
docs/assets/provinces/world_province_adjacency.csv
docs/assets/terrain_masks/previews/terrain_masks_combined_preview_3072x2048.png
docs/assets/terrain_masks/masks_3072x2048/water_mask.png
docs/assets/terrain_masks/masks_3072x2048/land_mask.png
docs/assets/terrain_masks/masks_3072x2048/coast_mask.png
docs/assets/terrain_masks/masks_3072x2048/mountain_mask.png
docs/assets/terrain_masks/masks_3072x2048/highland_mask.png
docs/assets/terrain_masks/masks_3072x2048/lowland_mask.png
docs/assets/terrain_masks/masks_3072x2048/fertile_lowland_mask.png
docs/assets/terrain_masks/masks_3072x2048/marsh_mask.png
docs/assets/terrain_masks/masks_3072x2048/farmland_mask.png
docs/assets/terrain_masks/masks_3072x2048/forest_mask.png
docs/assets/terrain_masks/masks_3072x2048/dryland_mask.png
docs/assets/terrain_masks/masks_3072x2048/steppe_mask.png
docs/assets/terrain_masks/masks_3072x2048/oasis_wetland_mask.png
docs/assets/terrain_masks/masks_3072x2048/bare_rock_mask.png
docs/assets/terrain_masks/masks_3072x2048/snow_peak_mask.png
docs/assets/terrain_masks/masks_3072x2048/pass_mask.png
docs/assets/rivers/river_paths.json
```

## Simulator

To activate the simulator:

1. Open `http://127.0.0.1:8766/tools/river-workbench/`.
2. In the left `Simulator` panel, keep `Replace current rivers` checked if you want a fresh generated draft.
3. Set `Min Flow`, `Max Rivers`, `Grid Step`, `Smoothing`, `Min Length`, `Source Spacing`, `Point Density`, and `Variant Seed`.
4. Click `Run River Simulator`.
5. Click `Randomize Draft` to choose a new seed and generate another version with the same hydrology logic.
6. Use `Reset Simulator Settings` if a draft does not appear after experimenting with strict settings.
7. Generated rivers become normal editable rivers. Use `Select`, `Add Point`, `Delete Point`, `Reverse Direction`, and the right inspector to fix them by hand.

The simulator is deterministic for each seed. It uses the heightmap and existing masks rather than visual AI. The seed only changes valid close-call source ranking and bend phases; flow direction and flow accumulation still come from the map.

It calculates:

- slope, flow direction, flow accumulation, watersheds, source score, and mouth score
- sinuosity, target sinuosity, gradient, elevation range, uphill error, meander potential, and terrain fit
- stream order, discharge estimate, width class, navigability, and tributary join quality
- floodplain fertility, crossing difficulty, bridge/ford score, port score, canal feasibility, marsh risk, and strategic chokepoint score

For more rivers:

- increase `Max Rivers`
- lower `Min Flow`
- lower `Source Spacing`
- lower `Min Length`

The default simulator settings are now tuned for a fuller draft network rather than only a few major rivers.

If a run finds zero rivers, the workbench automatically tries one safer relaxed pass and reports that in the simulator panel.

## Heightmap View

Use the `Layers` panel to switch between:

- `Terrain`: terrain preview
- `Height Relief`: readable hillshade-style heightmap for node editing
- `Raw Heightmap`: the source heightmap image
- `Province RGB`: unique-RGB province picking source

Enable `Contours` to show elevation bands over the active layer. The bottom-left cursor readout also shows the current map coordinate and sampled height value.

## Editing

- `New River` creates a selected river and switches to `Add Point`.
- `Add Point` appends clicked map points to the selected river.
- `Select` lets you select rivers and drag control points.
- `Delete Point` removes the clicked control point.
- `Reverse Direction` flips source-to-mouth order.
- `Add More Points` splits every segment of the selected river so you have more draggable nodes.
- The right panel edits id, name, type, width class, navigability, source province, mouth, connected provinces, crossings, and notes.

## Exports

The exporter downloads:

```text
river_workbench_project.json
river_paths.json
waterways.csv
river_core_mask.png
river_mask.png
river_bank_mask.png
floodplain_mask.png
delta_mask.png
canal_mask.png
marsh_channel_mask.png
oasis_wadi_mask.png
navigable_river_mask.png
river_crossing_mask.png
```

## Validation

The validation panel warns about empty projects, missing ids/names, duplicate ids, too few points, unknown province references, suspicious uphill flow, missing mouths for major rivers, and mouths that are not near the water mask.

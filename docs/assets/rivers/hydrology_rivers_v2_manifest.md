# Hydrology rivers v2 manifest

This pass is a corrected river-map attempt generated from the custom War Gods heightmap and terrain masks instead of image-style guessing.

## Why this pass exists

The earlier river attempts looked like random scribbles because they were not constrained by the heightmap. This pass uses the heightmap and land/water masks as the source data.

## Method

```text
1. Load the custom 3072 x 2048 heightmap.
2. Load land and water masks.
3. Downsample to a hydrology simulation grid.
4. Run priority-flood drainage toward water.
5. Calculate upstream flow accumulation.
6. Trace connected river channels.
7. Simplify and smooth those channels into editable vector paths.
8. Export river masks from the vector paths.
```

## Generated pack

```text
war_gods_hydrology_rivers_v2_pack.zip
```

## Included outputs

```text
data/river_paths.json
data/waterways.csv
masks_3072x2048/river_core_mask.png
masks_3072x2048/river_mask.png
masks_3072x2048/river_bank_mask.png
masks_3072x2048/floodplain_mask.png
masks_3072x2048/delta_mask.png
masks_3072x2048/canal_mask.png
masks_3072x2048/marsh_channel_mask.png
masks_3072x2048/oasis_wadi_mask.png
masks_3072x2048/navigable_river_mask.png
masks_3072x2048/river_crossing_mask.png
masks_3072x2048/rivers_hydrology_ck2_palette_map.png
masks_3072x2048/rivers_hydrology_ck2_palette_map.bmp
previews/hydrology_rivers_blended_terrain_3072x2048.png
previews/hydrology_rivers_blended_terrain_1536x1024.png
previews/hydrology_rivers_ck2_palette_preview_1536x1024.png
previews/hydrology_rivers_raw_blue_overlay_1536x1024.png
previews/hydrology_river_mask_contact_sheet.png
```

## Important limitation

This is not final hand-authored river design. It is a physics-guided first pass that should be opened in the River Workbench and corrected by hand.

The correct workflow is:

```text
hydrology simulator first pass
→ River Workbench manual correction
→ final river paths and masks
→ main renderer blend pass
```

## Renderer rule

Do not render the river mask as bright blue lines. Use the masks as blend layers:

```text
1. floodplain_mask modifies nearby terrain colour
2. river_bank_mask darkens/wets the river edge
3. river_mask draws muted water
4. river_core_mask adds depth only at the center
```

## Province rule

River masks must not affect province selection. Province clicking remains based on the unique-RGB province map.

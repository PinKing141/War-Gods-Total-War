# Realistic editor river blend manifest

This manifest records the river blend pack generated from the user's River Workbench paths.

## Source inputs

```text
river_paths.json
waterways.csv
source map screenshot
```

The source `river_paths.json` uses a 3072 x 2048 map coordinate space. Empty placeholder rivers were skipped.

## Generated pack

```text
war_gods_realistic_river_blend_from_editor_pack.zip
```

## Purpose

The previous masks still looked like visible blue worms because the water channel was being treated as the final art. This pass treats the uploaded river paths as structure and builds layered render masks from them.

## Generated masks

```text
masks_3072x2048/river_path_source_mask.png
masks_3072x2048/river_core_mask.png
masks_3072x2048/river_mask.png
masks_3072x2048/river_bank_mask.png
masks_3072x2048/floodplain_mask.png
masks_3072x2048/river_shadow_mask.png
masks_3072x2048/river_highlight_mask.png
masks_3072x2048/delta_mask.png
masks_3072x2048/canal_mask.png
masks_3072x2048/marsh_channel_mask.png
masks_3072x2048/oasis_wadi_mask.png
masks_3072x2048/navigable_river_mask.png
masks_3072x2048/river_crossing_mask.png
masks_3072x2048/rivers_ck2_palette_from_editor.png
```

## Preview files

```text
previews/realistic_rivers_blended_on_user_map_970x640.png
previews/realistic_rivers_blended_on_user_map_1536x1024.png
previews/raw_blue_lines_overlay_970x640.png
previews/raw_blue_lines_overlay_1536x1024.png
previews/rivers_ck2_palette_preview_1536x1024.png
previews/river_mask_contact_sheet.png
```

## Data files

```text
data/river_paths_cleaned_from_editor.json
data/river_paths_original_uploaded.json
data/waterways_uploaded.csv
data/waterways_generated_from_editor.csv
```

## Render rule

Do not render `river_mask.png` as a bright blue overlay. Use this layered blend instead:

```text
1. floodplain_mask: subtle green/fertile terrain influence
2. river_bank_mask: wet/darker edge blending
3. river_shadow_mask: carved groove under the water
4. river_mask: muted teal water body
5. river_core_mask: darker center depth
6. river_highlight_mask: tiny low-opacity highlight
```

## Important limitation

This pass improves the visual treatment, but the river geometry still comes from the user's current paths. If a path is too short, isolated, or placed oddly, the blend will make it look better but cannot make the geography fully realistic by itself.

## Province rule

River masks must not affect province picking. Province picking remains based on the unique-RGB province map.

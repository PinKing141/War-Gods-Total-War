# Editor river masks manifest

This manifest records the river mask pack generated from the user's River Workbench/export files.

## Source inputs

```text
river_paths.json
waterways.csv
```

The export contained 13 river entries. 10 had usable point paths and 3 were empty placeholder rivers, so the generated mask pack skips the empty placeholders.

## Generated pack

```text
war_gods_editor_river_masks_pack.zip
```

## Generated mask files

```text
masks_3072x2048/river_path_source_mask.png
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
masks_3072x2048/rivers_ck2_palette_from_editor.png
```

## Generated data files

```text
data/river_paths_cleaned_from_editor.json
data/river_paths_original_uploaded.json
data/waterways_uploaded.csv
data/waterways_generated_from_editor.csv
```

## Preview files

```text
previews/source_map_preview_1536x1024.png
previews/river_mask_raw_blue_overlay_1536x1024.png
previews/river_masks_blended_on_user_map_1536x1024.png
previews/river_mask_contact_sheet_1536x1024.png
```

## Render rule

The masks should not be rendered as bright blue lines. Use the masks as blend layers:

```text
1. floodplain_mask adds green/fertile influence.
2. river_bank_mask darkens and wets the river edge.
3. river_mask draws muted water.
4. river_core_mask adds depth along the center.
```

## Important rule

Do not use any river mask for province clicking. Province clicking must remain based on the unique-RGB province map.

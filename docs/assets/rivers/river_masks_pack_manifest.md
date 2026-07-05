# Pronounced river masks pack manifest

This manifest describes the generated pronounced river masks pack for the 3072 x 2048 world map.

## Purpose

The first terrain masks made the terrain less flat, but rivers need to read clearly on top of the map. These river masks are intentionally stronger and wider so waterways appear pronounced instead of fading into the background.

## Source of truth

```text
docs/assets/rivers/river_paths.json = editable river path and gameplay source
docs/assets/rivers/waterways.csv = river metadata table
river masks = visual blending layer only
```

## Included mask files in the ZIP

```text
river_core_mask.png
river_mask.png
river_bank_mask.png
floodplain_mask.png
delta_mask.png
canal_mask.png
marsh_channel_mask.png
oasis_wadi_mask.png
river_crossing_mask.png
navigable_river_mask.png
```

## Preview files in the ZIP

```text
previews/river_masks_pronounced_overlay_3072x2048.png
previews/river_masks_pronounced_overlay_1536x1024.png
previews/river_masks_combined_grayscale_3072x2048.png
previews/river_masks_combined_grayscale_1536x1024.png
previews/river_mask_contact_sheet.png
```

## Render recommendation

```text
1. base terrain and biome masks
2. floodplain_mask
3. river_bank_mask
4. river_mask and river_core_mask
5. canal/marsh/delta/wadi accents
6. roads and bridges
7. province borders
8. labels and UI
```

## Important rule

Do not use river masks for province clicking. Province clicking must continue to use the unique-RGB province map.

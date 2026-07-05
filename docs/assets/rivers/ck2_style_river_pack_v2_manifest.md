# CK2-style river pack v2

This pass replaces the earlier thick river-mask experiment with a CK2-inspired river standard.

## What changed

The previous river masks were too thick and read like painted blue bands. This pass uses a thinner dendritic river network inspired by CK2 rivers.bmp logic:

- white land
- pink sea and major water
- blue one-pixel river corridors in the CK2 preview
- green river sources
- red merge points
- yellow split/delta points

## Files in the generated ZIP

```text
masks_3072x2048/rivers_ck2_palette_map.png
masks_3072x2048/rivers_ck2_palette_map.bmp
masks_3072x2048/river_core_mask.png
masks_3072x2048/river_mask.png
masks_3072x2048/river_bank_mask.png
masks_3072x2048/floodplain_mask.png
masks_3072x2048/delta_mask.png
masks_3072x2048/canal_mask.png
masks_3072x2048/marsh_channel_mask.png
masks_3072x2048/oasis_wadi_mask.png
masks_3072x2048/river_crossing_mask.png
masks_3072x2048/navigable_river_mask.png
data/river_paths.json
data/waterways.csv
previews/ck2_style_rivers_palette_preview_1536x1024.png
previews/ck2_style_rivers_on_terrain_1536x1024.png
previews/ck2_style_river_mask_contact_sheet.png
```

## Engine rule

```text
river_paths.json = gameplay/vector source of truth
rivers_ck2_palette_map = CK2-style validation/reference preview
river masks = visual blending only
province RGB map = province clicking source of truth
```

## Renderer guidance

Do not render rivers as thick blue strokes. Use the path data for identity and interaction, but use the masks for subtle banks and floodplains.

Recommended draw order:

```text
1. terrain and biome masks
2. floodplain mask
3. river bank mask
4. river core/mask
5. roads and bridges
6. province borders
7. labels and UI
```

## Important note

This is still a first corrected pass, not a final hand-painted river map. The next improvement should be hand-adjusting river mouths and tributaries around the most important start-region provinces.

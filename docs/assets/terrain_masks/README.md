# War Gods Total War terrain masks

Generated first-pass terrain masks for the 3072 x 2048 world map.

## How to read the masks

Each PNG is 8-bit grayscale:

- black = no presence
- white = strong presence
- grey = partial blend / soft transition

These masks are intended for terrain rendering, not clicking. Province clicking should still use the unique-RGB province map.

## Included

- masks_3072x2048/*.png — individual terrain masks
- previews/terrain_masks_combined_preview_3072x2048.png — combined terrain preview
- previews/terrain_masks_combined_preview_1536x1024.png — smaller terrain preview
- previews/terrain_mask_contact_sheet.png — all masks at a glance
- manifest.json — file list and generation notes

## Recommended render use

Draw order:

1. water/deep water/shallow water
2. land base
3. elevation shading from heightmap
4. biome masks: forest, marsh, dryland, steppe, farmland
5. mountain / bare rock / snow masks
6. rivers and roads later
7. political overlay
8. province borders and labels

## Warning

These are not final hand-painted art masks. They are a clean generated baseline so the terrain stops looking flat and ugly. The next pass should manually refine rivers, road corridors, forests around rivers, and special lore regions.

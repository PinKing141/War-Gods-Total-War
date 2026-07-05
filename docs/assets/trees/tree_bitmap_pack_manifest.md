# Tree bitmap pack manifest

This manifest records the first War Gods CK-style tree placement pack.

## Purpose

This pack follows the CK-style idea where a smaller tree bitmap controls tree placement, type and density. Each coloured pixel represents one in-game tree clump or tree tile.

## Source inputs

```text
terrain masks pack
land_mask.png
water_mask.png
forest_mask.png
marsh_mask.png
farmland_mask.png
fertile_lowland_mask.png
lowland_mask.png
highland_mask.png
mountain_mask.png
dryland_mask.png
steppe_mask.png
oasis_wetland_mask.png
coast_mask.png
snow_peak_mask.png
bare_rock_mask.png
```

## Generated pack

```text
war_gods_tree_bitmap_pack.zip
```

## Main outputs

```text
trees_bmp_style_384x256.png
trees_bmp_style_384x256.bmp
data/tree_pixels.csv
manifest.json
```

The tree bitmap is 384 x 256, which is 1/8 of the 3072 x 2048 world map.

## Generated masks

```text
masks_3072x2048/palm_tree_pixels_mask.png
masks_3072x2048/coniferous_tree_pixels_mask.png
masks_3072x2048/mediterranean_tree_pixels_mask.png
masks_3072x2048/deciduous_tree_pixels_mask.png
masks_3072x2048/tree_density_1_mask.png
masks_3072x2048/tree_density_2_mask.png
masks_3072x2048/tree_density_3_mask.png
masks_3072x2048/tree_cover_mask.png
```

## Tree palette

```text
Palm trees:
  density 1 = #FFFF00
  density 2 = #D6A000
  density 3 = #917000

Coniferous trees:
  density 1 = #1E8B6D
  density 2 = #105E43
  density 3 = #063C2B

Mediterranean trees:
  density 1 = #9A9C33
  density 2 = #737719
  density 3 = #4C5406

Deciduous trees:
  density 1 = #4C9C33
  density 2 = #2E721E
  density 3 = #0E4D0D
```

Darker colours represent denser or larger tree clumps.

## Placement logic

```text
coniferous = cold forests, northern highlands, mountain foothills
deciduous = wet lowlands, forests, marsh edges, fertile lands
mediterranean = dryland woodland, steppe edge, coastal scrub, warm hills
palm = oasis wetlands, hot coasts, dry southern lowlands
```

Water, snow peaks and bare rock are heavily reduced or excluded.

## Current counts

```text
total tree pixels = 19739
palm density 1 = 8
palm density 2 = 87
palm density 3 = 21
coniferous density 1 = 411
coniferous density 2 = 529
coniferous density 3 = 1407
mediterranean density 1 = 405
mediterranean density 2 = 6566
mediterranean density 3 = 154
deciduous density 1 = 105
deciduous density 2 = 488
deciduous density 3 = 9558
```

## Renderer rule

Do not use this bitmap for province picking. It is only tree placement/visual density data.

The main renderer can use the tree bitmap in three ways:

```text
1. spawn tree clumps at coloured pixels
2. add subtle forest density tint from tree_cover_mask
3. show tree symbols/details only at higher zoom
```

## Warning

This is a generated first pass. It should be edited later with a dedicated vegetation/tree editor if the placement looks too dense, too sparse or regionally wrong.

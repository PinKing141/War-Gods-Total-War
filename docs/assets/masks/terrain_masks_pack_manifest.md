# Terrain masks pack manifest

This manifest describes the generated first-pass terrain mask pack for the 3072 x 2048 world map.

## Purpose

The masks are used to make the map renderer blend terrain visually instead of showing flat province colours.

The masks should not be used for province clicking. Province clicking must still use the unique-RGB province map.

## Source inputs

```text
war_gods_total_war_custom_world_heightmap_ck2scale_3072x2048_16bit.png
war_gods_world_provinces_unique_rgb_3072x2048.png
war_gods_world_province_definitions.csv
```

## Mask format

```text
8-bit grayscale PNG
black = absent
white = strong presence
grey = partial blend
resolution = 3072 x 2048
```

## Included masks

```text
water_mask.png
land_mask.png
coast_mask.png
shallow_water_mask.png
deep_water_mask.png
lowland_mask.png
fertile_lowland_mask.png
farmland_mask.png
forest_mask.png
marsh_mask.png
dryland_mask.png
steppe_mask.png
oasis_wetland_mask.png
highland_mask.png
mountain_mask.png
bare_rock_mask.png
snow_peak_mask.png
pass_mask.png
road_influence_mask.png
port_mask.png
fort_mask.png
mana_site_mask.png
strategic_site_mask.png
```

## Recommended render use

```text
1. water / shallow water / deep water
2. base land colour
3. heightmap elevation shading
4. biome masks: forest, marsh, dryland, steppe, farmland
5. mountain, bare rock and snow masks
6. rivers and roads later
7. political overlay
8. province borders and labels
```

## Notes

These are generated baseline masks. They are useful for getting away from ugly flat colours, but they are not final hand-painted art. The next pass should refine rivers, road corridors, forest edges, marshlands and important lore regions manually.

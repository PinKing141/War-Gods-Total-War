# Heightmap and province-map implementation plan

This plan explains how to turn the custom heightmap and CK2-style province map into a clickable, good-looking strategic map.

## Goal

Use separate map layers instead of baking everything into one image.

```text
heightmap = elevation only
province RGB map = clickable province IDs
biome/terrain color layer = forests, grasslands, drylands, mountains, marshes
political overlay = realm ownership
borders/labels/rivers/roads = drawn on top
```

## Required files

```text
docs/assets/heightmaps/world_heightmap_3072x2048_16bit.png
docs/assets/provinces/world_provinces_unique_rgb_3072x2048.png
docs/assets/provinces/world_province_definitions.csv
docs/assets/provinces/world_province_adjacency.csv
```

The province RGB map is the clickable data source. The painted preview is only for human checking.

## Renderer steps

1. Load the heightmap image into an offscreen canvas.
2. Load the unique-RGB province map into another offscreen canvas.
3. Load province_definitions.csv and build two lookups:
   - province_id -> province data
   - rgb_key -> province_id
4. For each screen pixel or low-resolution render pixel:
   - read the corresponding height value
   - read the province RGB value
   - find the province ID from RGB
   - find province terrain/region from the CSV
   - choose a biome base color
   - shade it using elevation and slope
5. Draw political/culture/religion/devastation overlays as transparent tints above the terrain layer.
6. Draw borders, rivers, roads, labels and selected province outlines last.

## Click handling

On click:

1. Convert screen position to world/map coordinates.
2. Convert world/map coordinates to image pixel coordinates.
3. Read the RGB value from the province-map canvas.
4. Convert RGB to a key like `r,g,b`.
5. Look up the province ID.
6. Open/select that province.

Pseudo-code:

```js
function provinceIdAtMapPixel(px, py) {
  const data = provinceCtx.getImageData(px, py, 1, 1).data;
  const key = `${data[0]},${data[1]},${data[2]}`;
  return rgbToProvinceId.get(key) || null;
}
```

## Visual style rules

Do not show the raw heightmap directly. It will look ugly.

Use it as data:

```text
low elevation + wet region = dark green forest / marsh
low elevation + dry region = tan dryland / steppe
mid elevation + fertile region = green plains
mid elevation + dry region = ochre plateau
high elevation = grey/brown mountains
highest peaks = pale rock / snow highlights
water = deep blue, shallow coast blue-green
```

## Suggested biome colors

```text
river_city / canal_farmland = fertile green and yellow-green
frontier_farms = muted green-brown
bog_forest = dark green / marsh olive
mountain_pass = slate grey / brown rock
steppe_market = dry grass yellow-brown
river_port = coastal green-blue mix
sacred_battlefield = muted grass with worn-earth tint
Qeresh drylands = sand / ochre
Fenward = wet forest green
Bannerfields = rich farmland green/gold
```

## First coding target

Create a new renderer module:

```text
docs/assets/map_layers.js
```

Suggested class:

```js
WG.LayeredWorldMap
```

Responsibilities:

- load images and CSV
- render terrain from height + biome rules
- read province RGB for hover/click
- draw map overlays
- preserve existing pan/zoom/hover/click behaviour

## Important warning

The current `map.js` generates land ownership procedurally from province centers. The new pipeline should stop using that generated cellOwner grid for final world maps. Instead, the province RGB map becomes the source of truth for province ownership and click detection.

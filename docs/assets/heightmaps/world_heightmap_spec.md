# Custom world heightmap

Target asset path:

```text
docs/assets/heightmaps/world_heightmap_3072x2048_16bit.png
```

Preview asset path:

```text
docs/assets/heightmaps/world_heightmap_3072x2048_8bit_preview.png
```

## Target size

```text
3072 x 2048
```

This is a large grand-strategy map raster intended as the macro terrain layer.

## Height rules

```text
black = water / lowest elevation
dark gray = coasts and lowlands
mid gray = plains, uplands, and plateaus
light gray = highlands and foothills
white = highest mountain ridges
```

## Design direction

The world should feel familiar at a glance but not be a literal Earth copy. Keep the broad continent arrangement recognizable, then alter the coasts, inland seas, island chains, mountain arcs, rift systems, and plateau regions.

## Usage notes

Use the 16-bit PNG as the terrain source. Use the 8-bit PNG only for previewing. Keep political borders, labels, province lines, roads, and overlays separate from the heightmap.

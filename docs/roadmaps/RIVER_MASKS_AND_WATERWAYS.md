# River masks and waterways

Yes, the map should have river masks, but river masks should not replace river path data.

## Core rule

```text
river_paths.json = gameplay and vector source of truth
river_mask.png = visual blending and terrain wetness
waterways.csv = gameplay metadata and province connections
```

## Why river paths are still needed

`river_paths.json` is the best source for:

- river names
- river type
- navigability
- width
- connected provinces
- crossings
- bridges
- road intersections
- supply and trade routes
- movement crossing penalties

Paths are easier to edit, validate and attach to gameplay.

## Why river masks are useful

`river_mask.png` is useful for making the map look good.

The renderer can use river masks for:

- wet bank tint
- floodplain greenery
- marsh blending
- fertile riverland blending
- soft river edges
- delta texture
- preventing rivers from looking like blue marker lines

## Recommended river mask files

```text
assets/maps/rivers/river_mask.png
assets/maps/rivers/river_bank_mask.png
assets/maps/rivers/floodplain_mask.png
assets/maps/rivers/delta_mask.png
assets/maps/rivers/canal_mask.png
assets/maps/rivers/marsh_channel_mask.png
```

## Mask meanings

```text
river_mask.png = exact visible water corridor
river_bank_mask.png = soft wetness beside rivers
floodplain_mask.png = fertile land influenced by rivers
canal_mask.png = artificial straight waterways
marsh_channel_mask.png = broken channels inside wetlands
river_crossing_mask.png = optional bridge/ford influence points
```

## Render use

```text
1. terrain base
2. biome masks
3. floodplain and river bank masks
4. river water from river_paths.json or river_mask.png
5. roads and bridges
6. province borders
7. labels and UI
```

## Do not do this

Do not use river masks for clicking provinces.
Do not use river masks as the only source of river gameplay.
Do not draw random rivers just because a mask exists.
Do not bake river colour directly into the heightmap.

## First implementation recommendation

For Pass 2, create both:

```text
assets/maps/rivers/river_paths.json
assets/maps/rivers/river_mask.png
```

Use `river_paths.json` for logic and renderer strokes.
Use `river_mask.png` only for blending banks, floodplains and soft water edges.

## Validation rules

```text
Every river path must have at least 2 points.
Every connected province must exist.
Every navigable river should touch at least one port or trade province.
Every canal should connect settlement, farmland or river-city terrain.
River mask and river paths should visually overlap.
River masks must never modify the province RGB map.
```

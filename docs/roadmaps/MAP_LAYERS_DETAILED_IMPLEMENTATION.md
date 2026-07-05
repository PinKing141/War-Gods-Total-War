# Map layers detailed implementation

This document expands the next map upgrade: rivers, roads, forests, drylands, mountains, passes, ports, bridges and forts.

## Core rule

The map must be layered. Do not bake everything into one image.

```text
heightmap = elevation data
province RGB map = clickable province IDs
province definitions = province meaning
terrain layer = what the player sees
feature layers = rivers, roads, forests, passes, ports, forts
political overlay = realm ownership tint
labels and UI = final readable layer
```

## Render order

```text
1. base water and terrain
2. elevation shading
3. biome masks: forest, marsh, dryland, steppe, farmland
4. rivers and lakes
5. roads and routes
6. political/culture/religion overlay tint
7. province borders
8. icons: ports, bridges, passes, forts, temples, cities
9. labels
10. hover/selection outlines and debug overlay
```

## 1. Rivers

Rivers should not be simple blue lines. They should be data objects that affect visuals and gameplay.

### Required file

```text
assets/maps/rivers/river_paths.json
```

### River object

```json
{
  "id": "RIV_ROV_MAIN",
  "name": "Rov River",
  "type": "major_river",
  "points": [[1240, 430], [1310, 520], [1400, 610], [1510, 700]],
  "width": 5,
  "navigable": true,
  "source_province": "PROV_GREYHOOK_045",
  "mouth": "Lanter Sea",
  "connected_provinces": ["PROV_ROV_HALEM", "PROV_SEVRIN_CANAL"],
  "crossings": ["BRG_HALEM", "FORD_SEVRIN"]
}
```

### River types

```text
major_river = wide, important, affects trade and movement
tributary = feeds major rivers, smaller and often hidden at far zoom
canal = straighter, artificial, linked to canal cities and farmland
marsh_channel = broken, branchy, dark, linked to marsh and disease regions
oasis_wadi = seasonal dryland water route, important in Qeresh regions
delta = split river mouth near a sea or lake
```

### River rendering

Draw each river in several passes:

```text
riverbed shadow -> main water -> inner highlight -> wet bank tint
```

Minor streams should disappear when zoomed out. Major rivers should remain readable at world zoom.

### River gameplay

Rivers should affect:

```text
crossing movement cost
bridge and ford importance
trade and supply movement
river ports
canal farmland value
defensive battle modifiers
plague and travel routes
siege supply access
```

## 2. Roads

Roads should be a separate layer, not drawn into the province texture.

### Required file

```text
assets/maps/routes/road_paths.json
```

### Road object

```json
{
  "id": "ROAD_STONE_HALem_TO_WEST_GEAR",
  "name": "Halem-West Gear Stone Road",
  "type": "stone_road",
  "points": [[1713, 742], [1850, 730], [2097, 739]],
  "quality": 5,
  "imperial": true,
  "connected_provinces": ["PROV_ROV_HALEM", "PROV_WEST_GEAR"]
}
```

### Road types

```text
stone_road = old imperial road, fast movement and high strategic value
trade_road = caravan or merchant route
local_road = normal local travel
mountain_pass_road = pass route, slow but strategically vital
forest_track = hidden or weak route through woodland
salt_road = dryland caravan route tied to Qeresh water law
```

### Road gameplay

Roads should affect:

```text
army movement speed
supply range
tax reach
trade income
rebellion suppression speed
plague movement speed
strategic control of bridges and passes
```

## 3. Forests, marshes, drylands and greenery

Do not draw greenery randomly. Greenery should come from province terrain, region climate, height and moisture.

### Required masks

```text
assets/maps/masks/forest_mask.png
assets/maps/masks/marsh_mask.png
assets/maps/masks/dryland_mask.png
assets/maps/masks/farmland_mask.png
```

### Terrain rules

```text
Rov Basin = fertile riverland, canals, farms, cities
Cairn March = cold bog forest, iron hills, winter forests
Taluun Steppe = grassland, camps, sparse rivers
Qeresh Wells = hot dry oasis, salt roads, stone towns
Maren Coast = wet ports, islands, maritime greenery
Fenward = dense marsh, wet forest, poor roads
Bannerfields = grain fields, abbeys, cavalry estates
Greyhook = mountain passes, mines, sparse highland vegetation
```

### Visual approach

Use texture and color variation, not giant flat green blobs.

```text
forest = dark green mottling, clustered near wetland/lowland areas
marsh = green-brown broken patches near rivers and coast
farmland = lighter green/yellow patches near roads and rivers
dryland = tan/ochre with sparse scrub
steppe = yellow-green grassland, smoother and more open
mountains = grey/brown rock with lighter ridges
```

## 4. Mountains and passes

Mountains should come from the heightmap. Passes should be explicit gameplay objects.

### Required file

```text
assets/maps/features/passes.csv
```

### Pass fields

```text
pass_id,name,province_id,connects_a,connects_b,difficulty,fortified,controller_importance
```

### Mountain gameplay

Mountains should affect:

```text
movement time
winter attrition
fort defense
mine resources
pass tolls
ambush risk
supply limits
strategic chokepoints
```

## 5. Ports, bridges and fort icons

Icons are not just decoration. They show important interaction points.

### Required files

```text
assets/maps/features/ports.csv
assets/maps/features/bridges.csv
assets/maps/features/forts.csv
```

### Icon rules

```text
port icon = only if port_level > 0 or river navigable
bridge icon = where major road crosses major river
fort icon = fort_level 3+
pass icon = mountain_pass terrain or pass feature
city icon = high strategic value, road level, port level or population
mana site icon = mana_site_level > 0
```

## What to build first

### Phase A: Rivers only

1. Create river_paths.json.
2. Add river renderer.
3. Disable prototype seed.rivers.
4. Add river tooltip/debug data.
5. Add river movement and crossing modifiers later.

### Phase B: Roads

1. Create road_paths.json.
2. Render roads by type and quality.
3. Link roads to provinces.
4. Use road_level for movement and supply.

### Phase C: Biome masks

1. Generate or paint forest/marsh/dryland/farmland masks.
2. Blend masks into terrain renderer.
3. Do not affect click detection.

### Phase D: Icons

1. Add ports, bridges, forts, passes and cities.
2. Render icons only when zoom level allows.
3. Make icons clickable later if needed.

## Validation checks

```text
Every river point must be inside map bounds.
Every connected province ID must exist.
Every bridge must connect a road and river.
Every port must be on water or a navigable river.
Every pass must sit on mountain or highland terrain.
Every road endpoint must connect to a valid province.
No feature layer may change province RGB click detection.
```

## Next Codex task

```text
Implement Phase A of MAP_LAYERS_DETAILED_IMPLEMENTATION.md.
Create river_paths.json and river_renderer.js.
Disable prototype seed.rivers unless debug mode is enabled.
Draw rivers with riverbed shadow, water stroke, highlight and wet bank tint.
Do not change province picking.
Add validation that all river connected_provinces exist.
```

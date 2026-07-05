# River tile data fallback

This plan pauses the polished visible river-art problem and keeps rivers as gameplay/map data baked into terrain tiles/provinces.

## Decision

Until final river art is hand-painted or the CK-style renderer is good enough, rivers do not need to appear as separate polished image layers.

Instead, river information should be baked into tile/province data so the game can still understand rivers mechanically.

```text
visual river art = optional / later
river tile data = required now
```

## Why

The current river masks and blends are not yet good enough visually. Bad visible rivers make the map look worse. It is better to hide or understate them visually while keeping river data available to the simulation.

## Core idea

Each map tile/province can know whether it has river influence.

Examples:

```text
has_river = true / false
river_id = RIV_ROV_MAIN
river_type = major_river / tributary / canal / marsh_channel / wadi / delta
river_width_class = 1-5
river_edge = north / east / south / west / center
river_crossing = none / ford / bridge / ferry
river_navigable = true / false
river_floodplain = true / false
```

The renderer can choose to show nothing, show a tiny subtle glyph/tint, or later draw proper river art from the same data.

## What gets baked into tiles

For each tile/province touched by a river path, store:

```text
tile_id
province_id
river_ids
primary_river_id
river_type
river_width_class
river_direction_in
river_direction_out
has_river_crossing
crossing_type
has_floodplain
has_delta
has_marsh_channel
navigable
movement_modifier
defense_modifier
trade_modifier
supply_modifier
farmland_modifier
```

## Minimal CSV output

```text
river_tiles.csv
```

Suggested columns:

```text
tile_id,province_id,river_id,river_type,width_class,direction_in,direction_out,navigable,crossing_type,floodplain,delta,marsh_channel,movement_cost,defense_bonus,trade_bonus,supply_bonus,farmland_bonus
```

## Province-level fallback

If the game does not yet have a proper tile grid, use province-level river fields first.

Add or generate:

```text
province_river_features.csv
```

Suggested columns:

```text
province_id,river_ids,primary_river_id,has_major_river,has_tributary,has_canal,has_delta,has_floodplain,has_crossing,navigable_river,river_trade_value,river_defense_bonus,river_movement_penalty,farmland_bonus
```

## Visual fallback options

Use one of these until proper river art exists:

### Option A: no visible river layer

Rivers only exist in tooltips, province panels and simulation rules.

### Option B: subtle tile tint

River provinces receive a small green/blue fertility tint, not a visible blue line.

### Option C: small map glyphs

Show a tiny river/floodplain/crossing icon only at high zoom.

### Option D: province panel only

When a player clicks a province, the panel says:

```text
River: Rov River
Crossing: Halem Bridge
Terrain effect: +farmland, +trade, defensive river crossing
```

## Gameplay uses now

Even without visible rivers, river tile data can support:

```text
river crossing defense
bridge/ford chokepoints
trade routes
supply movement
floodplain farmland bonuses
marsh disease/attrition
canal wealth
river ports
settlement placement
AI strategic value
```

## Renderer rule

Do not render ugly blue river lines in the main map.

Until proper CK-style river rendering is ready, the main map should use:

```text
terrain base
province colour/tint
optional subtle floodplain tint
province borders
labels/icons
```

Raw river masks and blue overlays are debug only.

## Workbench rule

The River Workbench can still show river paths and masks loudly, because it is an editor/debug tool. The main map should not.

## Future upgrade path

When the player-facing river art is ready, the same river tile data can drive the visual renderer.

```text
river_paths.json
+ river_tiles.csv
+ province_river_features.csv
→ CK-style river renderer
```

No simulation work should be thrown away.

## Codex task

```text
Implement river tile data fallback.

Tasks:
1. Keep river_paths.json and waterways.csv as source data.
2. Generate province_river_features.csv from river_paths.json and province definitions.
3. If a tile grid exists, generate river_tiles.csv. If not, skip tile output for now and use province-level river data.
4. Add river information to province tooltips/panels.
5. Add gameplay fields for river crossing, floodplain, navigability, trade, supply and farmland bonuses.
6. Disable visible bright river rendering in the main map.
7. Allow only subtle floodplain/river influence tint in normal map mode.
8. Keep raw river masks and blue overlays available only in debug/editor mode.
9. Do not remove the River Workbench.
10. Do not remove river_paths.json; it remains the future source for the CK-style renderer.
```

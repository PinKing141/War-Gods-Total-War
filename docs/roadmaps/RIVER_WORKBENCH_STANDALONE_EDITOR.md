# River Workbench: standalone editor and hydrology simulator

This document defines the River Workbench: a separate debug map editor for designing, simulating, correcting, validating and exporting rivers.

## Goal

Build the river tool as its own private workbench first, separate from the normal observer map.

The workbench should support two workflows:

```text
1. Hydrology simulator generates a believable first-pass river network.
2. Designer edits the generated rivers by hand and exports clean river assets.
```

The final output should feed back into the main War Gods map renderer.

## Why this should be separate

The normal observer map should stay clean and playable. The river editor needs extra tools, panels, debug overlays, validation warnings, raw export buttons and editing controls that would make the normal map messy.

So the editor should live separately.

## Proposed access path

Private first:

```text
docs/tools/river-workbench/index.html
```

Later public/editor build:

```text
web/tools/river-workbench/index.html
```

The first version can be accessed with a local file or localhost server. Later it can be protected behind a debug flag or published as a public map-editing tool.

## Folder structure

```text
docs/tools/river-workbench/
├── index.html
├── river_workbench.css
├── river_workbench.js
├── hydrology_simulator.js
├── river_editor.js
├── river_exporter.js
├── river_validator.js
└── README.md
```

Long-term structure after the wider project folder migration:

```text
tools/map_pipeline/
├── hydrology/
│   ├── flow_direction.py
│   ├── flow_accumulation.py
│   ├── trace_rivers.py
│   └── smooth_paths.py
web/tools/river-workbench/
├── index.html
├── src/
│   ├── river_workbench.js
│   ├── hydrology_simulator.js
│   ├── river_editor.js
│   ├── river_exporter.js
│   └── river_validator.js
└── styles/
    └── river_workbench.css
```

## Inputs

```text
docs/assets/heightmaps/world_heightmap_3072x2048_16bit.png
docs/assets/provinces/world_provinces_unique_rgb_3072x2048.png
docs/assets/provinces/world_province_definitions.csv
docs/assets/provinces/world_province_adjacency.csv
docs/assets/terrain_masks/masks_3072x2048/water_mask.png
docs/assets/terrain_masks/masks_3072x2048/land_mask.png
docs/assets/terrain_masks/masks_3072x2048/mountain_mask.png
docs/assets/terrain_masks/masks_3072x2048/lowland_mask.png
docs/assets/terrain_masks/masks_3072x2048/marsh_mask.png
docs/assets/terrain_masks/masks_3072x2048/farmland_mask.png
```

Optional existing river input:

```text
docs/assets/rivers/river_paths.json
```

## Outputs

```text
river_paths.json
waterways.csv
river_core_mask.png
river_mask.png
river_bank_mask.png
floodplain_mask.png
delta_mask.png
canal_mask.png
marsh_channel_mask.png
oasis_wadi_mask.png
navigable_river_mask.png
river_crossing_mask.png
river_workbench_project.json
```

## Workbench screens

### 1. Map viewport

The viewport should show the same world map scale as the main map, but with editor overlays.

Toggles:

```text
heightmap
province RGB overlay
terrain preview
water mask
slope map
flow direction
flow accumulation
simulated rivers
edited rivers
river masks
province labels
```

### 2. Hydrology simulator panel

Controls:

```text
Run simulation
Clear simulation
Minimum flow threshold
Smoothing amount
Minimum river length
Source elevation minimum
Allow endorheic basins
Delta creation threshold
Marsh channel creation threshold
Generate tributaries
Generate only major rivers
```

The simulator should produce a first-pass river network. It should not be considered final art.

### 3. River editor panel

Controls:

```text
New river
Select river
Delete river
Add point
Move point
Delete point
Split river
Join tributary
Reverse river direction
Set source
Set mouth
Set merge point
Set delta point
```

River fields:

```text
id
name
type
width_class
navigable
source_province
mouth
connected_provinces
crossings
notes
```

Allowed river types:

```text
major_river
tributary
canal
marsh_channel
oasis_wadi
delta
lake_outlet
endorheic_stream
```

### 4. Snapping tools

Snapping helps hand-drawn rivers stay believable.

```text
Snap to lower elevation
Snap to valley/flow line
Snap to coastline/water
Snap to existing river endpoint
Snap to province center
Snap to lowland/floodplain
Snap canal to straight segment
Snap river mouth to sea or lake
```

### 5. Validation panel

Warnings should appear before export.

```text
river has fewer than 2 points
river does not reach water/lake/basin
river flows uphill too much
river width decreases downstream
major river has no tributaries
tributary does not join a larger river
river splits inland outside delta or marsh type
canal is too curved
connected province does not exist
river crosses sea incorrectly
river crosses high mountains without a pass source
mask has gaps
mask and vector path do not overlap
```

## Hydrology simulator logic

The simulator should not be a visual AI. It should be a deterministic terrain algorithm.

### Step 1: prepare elevation

```text
load heightmap
apply land/water mask
slightly blur/smooth tiny noise
preserve major mountains and coasts
fill small pits or mark them as lakes/basins
```

### Step 2: flow direction

For each land pixel or sampled cell, water flows to the lowest neighbouring cell.

Use an 8-neighbour grid:

```text
NW N NE
W  X E
SW S SE
```

### Step 3: flow accumulation

Count how many upstream cells drain into each cell.

High accumulation means the cell belongs to a river path.

### Step 4: trace rivers

Start from high-elevation source zones where flow accumulation exceeds threshold. Trace downhill until water reaches:

```text
sea
lake
marsh basin
endorheic basin
existing larger river
```

### Step 5: simplify and smooth

The raw pixel path will look jagged. Convert it to control points and smooth it.

Important rule: smoothing must not move rivers into the sea, outside land, or across mountain ridges incorrectly.

### Step 6: classify rivers

```text
flow amount high + long path = major_river
flow amount medium = tributary
flat wetland + slow flow = marsh_channel
dryland basin + seasonal flow = oasis_wadi
near sea mouth + splitting = delta
```

### Step 7: generate masks

From the edited vector paths, generate masks with consistent widths:

```text
river_core_mask = thin central water line
river_mask = full visible water channel
river_bank_mask = soft edge around river
floodplain_mask = wider fertile influence
navigable_river_mask = navigable major rivers only
delta_mask = delta mouths only
canal_mask = canal paths only
marsh_channel_mask = marsh channel paths only
```

## Manual editing workflow

```text
1. Open River Workbench.
2. Load heightmap, province map and masks.
3. Run hydrology simulator.
4. Hide tiny streams.
5. Keep only believable major rivers and tributaries.
6. Hand-adjust ugly routes.
7. Draw lore-important canals by hand.
8. Validate all rivers.
9. Export river_paths.json and masks.
10. Import outputs into the main map renderer.
```

## Minimum viable version

The first useful version does not need perfect hydrology. It should support:

```text
standalone editor page
load map and heightmap
draw/edit river paths by hand
save/load river_workbench_project.json
export river_paths.json
export river_mask.png
export river_bank_mask.png
export floodplain_mask.png
basic validation
```

Then add the hydrology simulator after the manual editor is stable.

## Codex implementation prompt

```text
Create a standalone River Workbench for War Gods Total War.

Add docs/tools/river-workbench/index.html and supporting JS/CSS files.

The workbench should load the existing heightmap, province RGB map, province definitions CSV and terrain masks. It should not replace the normal observer map.

Implement:
1. map viewport with pan/zoom
2. river edit mode with add/move/delete points
3. river metadata form: id, name, type, width_class, navigable, connected_provinces, crossings
4. save/load river_workbench_project.json
5. export river_paths.json
6. export waterways.csv
7. export masks as PNGs: river_core_mask, river_mask, river_bank_mask, floodplain_mask, delta_mask, canal_mask, marsh_channel_mask, oasis_wadi_mask, navigable_river_mask, river_crossing_mask
8. validation panel
9. keep this tool separate from the main observer app

After the manual editor works, add a hydrology simulator panel that uses the heightmap to generate a first-pass river network for the designer to edit.
```

# Project structure overhaul

Purpose: split the project into clean layers so the simulation, web observer, map assets, generated data and lore content do not all fight each other.

## Current problem

The repository is doing several jobs at once:

- Python simulation engine
- CSV lore database
- browser observer app
- generated web seed files
- map assets and province assets
- planning docs and roadmaps

That is fine, but the folder structure needs clearer ownership.

## Target top-level structure

```text
War-Gods-Total-War/
├── README.md
├── pyproject.toml
├── requirements.txt
├── docs/
├── web/
├── assets/
├── data/
├── scripts/
├── tools/
├── src/
└── tests/
```

## Folder responsibilities

### docs/

Human planning and explanation only.

```text
docs/
├── design/
│   ├── WORLD_LORE_FOUNDATION.md
│   ├── GAME_PILLARS.md
│   ├── MAP_DESIGN.md
│   └── SIMULATION_RULES.md
├── roadmaps/
│   ├── MASTER_ROADMAP.md
│   ├── PROJECT_STRUCTURE_OVERHAUL.md
│   ├── HEIGHTMAP_AND_PROVINCE_MAP_IMPLEMENTATION.md
│   └── MAP_VISUAL_POLISH_ROADMAP.md
└── technical/
    ├── ARCHITECTURE.md
    ├── DATA_PIPELINE.md
    ├── WEB_OBSERVER.md
    └── TESTING.md
```

Rule: no runtime code should depend on docs.

### web/

The playable browser observer app.

```text
web/
├── index.html
├── styles/
│   ├── base.css
│   ├── layout.css
│   ├── map.css
│   └── panels.css
├── src/
│   ├── boot.js
│   ├── app.js
│   ├── ui/
│   │   ├── ui.js
│   │   ├── panels.js
│   │   ├── tooltip.js
│   │   └── overlay.js
│   ├── map/
│   │   ├── layered_world_map.js
│   │   ├── map_camera.js
│   │   ├── province_picker.js
│   │   ├── terrain_renderer.js
│   │   ├── border_renderer.js
│   │   ├── label_renderer.js
│   │   ├── river_renderer.js
│   │   └── map_assets.js
│   ├── sim/
│   │   ├── sim.js
│   │   ├── armies.js
│   │   ├── wars.js
│   │   ├── economy.js
│   │   └── succession.js
│   └── util/
│       ├── csv.js
│       ├── rng.js
│       ├── color.js
│       └── math.js
└── data/
    ├── web_seed.js
    ├── map_manifest.json
    └── generated/
```

Rule: web reads exported data. It should not own the master lore database.

### assets/

Large game assets that are not source code.

```text
assets/
├── maps/
│   ├── world/
│   │   ├── heightmap_3072x2048_16bit.png
│   │   ├── provinces_rgb_3072x2048.png
│   │   ├── terrain_preview_3072x2048.png
│   │   ├── province_preview_3072x2048.png
│   │   └── manifest.json
│   ├── masks/
│   │   ├── water_mask.png
│   │   ├── forest_mask.png
│   │   ├── mountain_mask.png
│   │   └── biome_mask.png
│   └── rivers/
│       ├── river_paths.json
│       ├── river_mask.png
│       └── waterways.csv
├── icons/
├── shields/
└── fonts/
```

Rule: assets are inputs or outputs, not logic.

### data/

Master game data in stable formats.

```text
data/
├── lore/
│   ├── species.csv
│   ├── cultures.csv
│   ├── religions.csv
│   ├── regions.csv
│   ├── resources.csv
│   └── naming_rules.csv
├── seed_frontier/
│   ├── factions.csv
│   ├── provinces.csv
│   ├── claims.csv
│   ├── characters.csv
│   ├── relations.csv
│   └── mages.csv
├── map/
│   ├── province_definitions.csv
│   ├── province_adjacency.csv
│   ├── province_centers.csv
│   └── terrain_rules.csv
└── generated/
    ├── web_seed.json
    ├── web_seed.js
    └── validation_report.json
```

Rule: CSV and JSON in data are the source of truth. Generated files go in generated folders.

### scripts/

Small command entrypoints.

```text
scripts/
├── run_sim.py
├── run_export.py
├── export_web_seed.py
├── validate_data.py
├── build_map_assets.py
└── generate_rivers.py
```

Rule: scripts call package code; scripts should not contain the main business logic.

### tools/

Offline asset and data generation tools.

```text
tools/
├── map_pipeline/
│   ├── build_heightmap.py
│   ├── build_province_map.py
│   ├── build_adjacency.py
│   ├── build_biome_masks.py
│   └── build_rivers.py
├── data_pipeline/
│   ├── csv_loader.py
│   ├── validators.py
│   └── web_seed_exporter.py
└── dev/
    ├── repo_audit.py
    └── asset_audit.py
```

Rule: tools can be messy internally, but their outputs must be predictable.

### src/

Python package for the real simulation engine.

```text
src/warfare_simulation/
├── __init__.py
├── app/
│   ├── campaign_service.py
│   └── use_cases/
├── domain/
│   ├── characters/
│   ├── diplomacy/
│   ├── economy/
│   ├── geography/
│   ├── magic/
│   ├── military/
│   ├── politics/
│   ├── religion/
│   └── time/
├── simulation/
│   ├── engine.py
│   ├── ticks.py
│   ├── events.py
│   └── rules.py
├── persistence/
│   ├── database.py
│   ├── repositories.py
│   └── migrations/
├── config/
│   ├── schema.py
│   └── loaders.py
└── export/
    ├── workbook/
    └── web/
```

Rule: domain code should not know about the web observer.

### tests/

```text
tests/
├── unit/
├── integration/
├── data_validation/
├── map_pipeline/
└── web_smoke/
```

## Migration phases

### Phase 1: create folders without moving code

Create the target folders and add README files explaining their purpose.

### Phase 2: move static web app from docs to web

Keep GitHub Pages compatibility by either copying built output to docs or configuring Pages to serve the right folder.

### Phase 3: move map assets into assets/maps

Move heightmaps, province maps, masks, river files and manifests into assets/maps/world.

### Phase 4: move master CSV data into data

Keep compatibility shims for old paths until the exporter and tests are updated.

### Phase 5: split web JavaScript

Break the current large files into map, ui, sim and util modules.

### Phase 6: update exporters and tests

Make scripts/export_web_seed.py read from data and write to web/data/generated.

### Phase 7: delete old duplicate paths

Only after tests and the web observer pass.

## Next practical task

Before the full folder migration, finish the map integration:

1. confirm the web map uses RGB province picking
2. confirm army markers use province center data from the province definitions CSV
3. disable prototype rivers until real river_paths.json exists
4. add a map debug overlay for province ID, RGB, center, terrain and controller
5. add a smoke test that confirms every army loc exists in province definitions

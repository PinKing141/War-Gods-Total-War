# Phase 4 data architecture and scenario foundation

This phase gives the current prototype a small scenario layer before any world expansion.

## Current data inventory

```text
docs/assets/data.js
  Static web observer seed exported from lore CSVs.

src/warfare_simulation/config/lore_csv/
  Source lore tables for species, cultures, religions, geography, economy and seed frontier content.

docs/assets/provinces/world_province_definitions.csv
  Layered map province definitions, RGB keys, terrain, biome, resources and controller fields.

docs/assets/provinces/world_province_adjacency.csv
  Layered map adjacency used by the observer simulation.

docs/assets/rivers/province_river_features.csv
  Province-level river gameplay metadata.

docs/assets/scenarios/default_frontier.json
  Default scenario manifest for the existing prototype baseline.
```

## Phase 4-A closing slice — DONE

```text
- Default scenario manifest exists.
- Scenario ID validates.
- Scenario data-source paths validate.
- Scenario faction and province references validate.
- No new factions, provinces, rivers or map art are added.
- Full test suite passes.
```

## Next Phase 4 work

```text
1. Decide whether scenario manifests should load directly in the web observer.
2. Add scenario selection only after the manifest format is stable.
3. Move more seed metadata out of core code only after validation stays green.
```

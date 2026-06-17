# Architecture

The warfare simulation engine is organized as a domain-driven Python package. JSON files define the immutable starting campaign, SQLite stores runtime state, repositories hydrate domain models, and the export layer builds the campaign workbook.

## Runtime flow

1. `ConfigManager` loads and validates JSON campaign data from `src/warfare_simulation/config/data`.
2. `CampaignBootstrap` initializes SQLite, seeds it from the validated configs, and hydrates repositories.
3. `WarfareSimulationApp` wires repositories into `CampaignOrchestrator`.
4. `CampaignOrchestrator.export_campaign()` delegates to the workbook factory.
5. The export package generates the eight workbook sheets used by the legacy campaign engine.

## Package boundaries

- `core`: shared constants, base protocols, exceptions, logging, and validation helpers.
- `config`: JSON loading and Pydantic validation schemas.
- `persistence`: SQLite connection management, schema setup, seeding, migrations, and repository hydration.
- `domain`: independent domain models, repositories, and services for kingdom, geography, military, diplomacy, logistics, and events.
- `export`: workbook styling, sheet generators, and workbook assembly.
- `orchestration`: high-level campaign coordination and game-state placeholders.
- `app.py`: the thin application entry point for config → database → export.

## Phase 6 monolith policy

`campaign_engine_initialiser.py` is deprecated and retained only as the golden reference for parity tests. New behavior should be added through the modular package. Remove the monolith in a follow-up change after Phase 6 acceptance confirms parity coverage is sufficient.

# Public API Reference

## `warfare_simulation.app.WarfareSimulationApp`

Thin entry point for bootstrapping a campaign and exporting the workbook.

```python
from warfare_simulation.app import WarfareSimulationApp

app = WarfareSimulationApp()
app.run("Auster_Campaign_Engine.xlsx")
```

- `__init__(config_path=None, db_path="war_sim.db")`: loads configuration, initializes SQLite, seeds campaign state, hydrates repositories, and prepares the orchestrator.
- `export_campaign(filename="Auster_Campaign_Engine.xlsx")`: writes the workbook through the orchestrator and returns the output path.
- `run(filename="Auster_Campaign_Engine.xlsx")`: convenience method that prints status, exports the workbook, and returns the output path.

## `warfare_simulation.orchestration.campaign.CampaignOrchestrator`

Coordinates campaign-level actions.

- `export_campaign(filename)`: writes the current campaign workbook and returns the output path.
- `advance_turn()`: advances the campaign one monthly turn, updates kingdom economy, advances logistics resources, synchronizes `GameState`, and returns the updated state.

## `warfare_simulation.orchestration.game_state.GameState`

Tracks the global campaign clock.

- `advance_turn()`: increments turn/month and rolls month 12 into the next year.
- `sync_from_kingdom(kingdom)`: mirrors clock fields from the active kingdom aggregate.
- `save_checkpoint(filename)`: writes the clock state to JSON.
- `load_checkpoint(filename)`: restores a clock state from JSON.

## `warfare_simulation.config.config.ConfigManager`

Loads validated JSON configuration.

- `load_kingdom_config()`
- `load_provinces_config()`
- `load_units_config()`
- `load_commanders_config()`
- `load_diplomacy_config()`
- `load_resources_config()`
- `load_all_configs()`

## `warfare_simulation.persistence.campaign_bootstrap.CampaignBootstrap`

Bridges config, SQLite, and repositories.

- `seed_from_config(config_mgr, db, force=False)`: inserts validated JSON data into SQLite and returns the kingdom id.
- `load_repositories(db)`: hydrates domain repositories from SQLite.
- `initialize(config_mgr, db, force=False)`: seeds if needed and returns hydrated repositories.

## `warfare_simulation.export.workbook_factory.WorkbookFactory`

Creates the modular Excel workbook.

- `from_campaign_repositories(repos)`: builds a factory from hydrated repositories.
- `create_workbook()`: returns an `openpyxl.Workbook` containing the campaign sheets.
- `save(filename)`: writes the workbook and returns the output path.

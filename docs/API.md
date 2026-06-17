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

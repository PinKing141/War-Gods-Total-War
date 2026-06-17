# Extending the Campaign Engine

Use the existing domain packages as templates when adding new systems.

## Add a new domain

1. Create `src/warfare_simulation/domain/<domain>/models.py` for dataclasses or entities.
2. Create `repository.py` for storage-facing collection methods.
3. Create `service.py` for domain rules and calculations.
4. Export the public types from the domain package `__init__.py`.
5. Add tests that exercise the domain without depending on unrelated domains.

## Add persisted state

1. Add tables or columns in `DatabaseManager.initialize_schema()` or a migration.
2. Seed initial values in `CampaignBootstrap.seed_from_config()` if they come from JSON.
3. Hydrate repository instances in `CampaignBootstrap.load_repositories()`.
4. Add persistence tests for schema creation, seeding, and hydration.

## Add workbook output

1. Add a generator under `src/warfare_simulation/export`.
2. Keep formatting centralized in `styles.py` and shared generator helpers.
3. Register the generator in `WorkbookFactory`.
4. Extend parity tests when changing existing legacy sheets.

## Turn simulation note

Full turn advancement is intentionally post-Phase 6. Until then, keep `WarfareSimulationApp` focused on initialization, SQLite seeding, repository hydration, and workbook export.

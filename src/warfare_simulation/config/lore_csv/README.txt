CSV = authored reference and seed data.
SQLite = mutable runtime truth after campaign creation.
Chronicle = interpreted views generated from state, events, and logs.

Load CSVs once through CsvLoreLoader/LoreBootstrap. Runtime systems should query
SQLite or hydrated repositories, not re-read raw CSV files during simulation turns.

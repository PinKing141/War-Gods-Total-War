"""CSV loader for authored lore and seed data."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from warfare_simulation.config.schema import (
    AiWeightCsvSchema,
    CultureCsvSchema,
    CultureModifierCsvSchema,
    LoreResourceCsvSchema,
    MechanicHookCsvSchema,
    NamingStyleCsvSchema,
    RegionCsvSchema,
    ReligionCsvSchema,
    ReligionModifierCsvSchema,
    SeedCharacterCsvSchema,
    SeedClaimCsvSchema,
    SeedFactionCsvSchema,
    SeedMageCsvSchema,
    SeedProvinceCsvSchema,
    SeedRegionCsvSchema,
    SeedRelationCsvSchema,
    SpeciesCsvSchema,
)
from warfare_simulation.core.exceptions import ConfigurationError


CsvModel = TypeVar("CsvModel", bound=BaseModel)


class CsvLoreLoader:
    """Load and validate CSV lore files from the package lore_csv directory."""

    def __init__(self, lore_dir: str | Path | None = None):
        self.lore_dir = Path(lore_dir) if lore_dir is not None else Path(__file__).parent / "lore_csv"

        if not self.lore_dir.exists():
            raise ConfigurationError(f"Lore CSV directory not found: {self.lore_dir}")

    def load_csv(self, relative_path: str) -> list[dict[str, str]]:
        """Load a CSV file as raw dictionaries."""
        path = self.lore_dir / relative_path

        if not path.exists():
            raise ConfigurationError(f"Missing lore CSV: {path}")

        try:
            with path.open("r", encoding="utf-8-sig", newline="") as csv_file:
                reader = csv.DictReader(csv_file)
                if reader.fieldnames is None:
                    raise ConfigurationError(f"Lore CSV has no header: {path}")

                rows: list[dict[str, str]] = []
                for index, raw_row in enumerate(reader, start=2):
                    if None in raw_row:
                        raise ConfigurationError(
                            f"Malformed lore CSV row {index} in {path}: too many fields"
                        )
                    row = {key: value or "" for key, value in raw_row.items()}
                    if any(value for value in row.values()):
                        rows.append(row)
                return rows
        except OSError as exc:
            raise ConfigurationError(f"Error loading lore CSV {path}: {exc}") from exc

    def _load_validated(self, relative_path: str, schema: type[CsvModel]) -> list[CsvModel]:
        rows = self.load_csv(relative_path)
        validated_rows: list[CsvModel] = []

        for index, row in enumerate(rows, start=2):
            try:
                validated_rows.append(schema(**row))
            except ValidationError as exc:
                raise ConfigurationError(
                    f"Invalid lore CSV row {index} in {relative_path}: {exc}"
                ) from exc

        return validated_rows

    def load_species(self) -> list[SpeciesCsvSchema]:
        return self._load_validated("03_species/species.csv", SpeciesCsvSchema)

    def load_cultures(self) -> list[CultureCsvSchema]:
        return self._load_validated("05_cultures/cultures.csv", CultureCsvSchema)

    def load_culture_modifiers(self) -> list[CultureModifierCsvSchema]:
        return self._load_validated("05_cultures/culture_modifiers.csv", CultureModifierCsvSchema)

    def load_religions(self) -> list[ReligionCsvSchema]:
        return self._load_validated("06_religion/religions.csv", ReligionCsvSchema)

    def load_religion_modifiers(self) -> list[ReligionModifierCsvSchema]:
        return self._load_validated(
            "06_religion/religion_modifiers.csv",
            ReligionModifierCsvSchema,
        )

    def load_regions(self) -> list[RegionCsvSchema]:
        return self._load_validated("04_geography/regions.csv", RegionCsvSchema)

    def load_lore_resources(self) -> list[LoreResourceCsvSchema]:
        return self._load_validated("08_economy/resources.csv", LoreResourceCsvSchema)

    def load_naming_styles(self) -> list[NamingStyleCsvSchema]:
        return self._load_validated("10_naming_data/naming_styles.csv", NamingStyleCsvSchema)

    def load_ai_weights(self) -> list[AiWeightCsvSchema]:
        return self._load_validated("11_simulation_schemas/ai_weights.csv", AiWeightCsvSchema)

    def load_mechanic_hooks(self) -> list[MechanicHookCsvSchema]:
        return self._load_validated(
            "11_simulation_schemas/mechanic_hooks.csv",
            MechanicHookCsvSchema,
        )

    def load_seed_region(self) -> list[SeedRegionCsvSchema]:
        return self._load_validated("12_seed_frontier/seed_region.csv", SeedRegionCsvSchema)

    def load_seed_factions(self) -> list[SeedFactionCsvSchema]:
        return self._load_validated("12_seed_frontier/seed_factions.csv", SeedFactionCsvSchema)

    def load_seed_provinces(self) -> list[SeedProvinceCsvSchema]:
        return self._load_validated("12_seed_frontier/seed_provinces.csv", SeedProvinceCsvSchema)

    def load_seed_relations(self) -> list[SeedRelationCsvSchema]:
        return self._load_validated("12_seed_frontier/seed_relations.csv", SeedRelationCsvSchema)

    def load_seed_characters(self) -> list[SeedCharacterCsvSchema]:
        return self._load_validated("12_seed_frontier/seed_characters.csv", SeedCharacterCsvSchema)

    def load_seed_claims(self) -> list[SeedClaimCsvSchema]:
        return self._load_validated("12_seed_frontier/seed_claims.csv", SeedClaimCsvSchema)

    def load_seed_mages(self) -> list[SeedMageCsvSchema]:
        return self._load_validated("12_seed_frontier/seed_mages.csv", SeedMageCsvSchema)

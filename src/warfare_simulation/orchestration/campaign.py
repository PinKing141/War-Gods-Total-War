"""Campaign-level orchestration for export-only Phase 5 slice."""

from pathlib import Path
from typing import Any, Mapping

from warfare_simulation.export.workbook_factory import WorkbookFactory


class CampaignOrchestrator:
    """Coordinates high-level campaign actions across domain repositories."""

    def __init__(self, repos: Mapping[str, Any]):
        self.repos = dict(repos)

    def export_campaign(self, filename: str | Path) -> Path:
        """Generate the current campaign state as an Excel workbook."""
        output_path = Path(filename)
        factory = WorkbookFactory(self.repos)
        workbook = factory.create_workbook()
        workbook.save(output_path)
        return output_path

    def advance_turn(self) -> None:
        """Turn simulation is intentionally deferred until after export parity."""
        raise NotImplementedError("Turn simulation comes after export parity is verified")

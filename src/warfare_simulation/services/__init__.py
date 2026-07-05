"""UI-facing service layer — thin facade over the simulation engine."""

from .campaign_service import (
    CampaignService,
    EventRow,
    FactionRow,
    ProvinceRow,
    RelationRow,
    ResourceRow,
    SimulationStatus,
)

__all__ = [
    "CampaignService",
    "ProvinceRow",
    "ResourceRow",
    "EventRow",
    "FactionRow",
    "RelationRow",
    "SimulationStatus",
]

"""UI-facing service layer — thin facade over the simulation engine."""

from .campaign_service import (
    CampaignService,
    EventRow,
    FactionRow,
    KingdomSummary,
    ProvinceRow,
    RelationRow,
    ResourceRow,
    SimulationStatus,
)

__all__ = [
    "CampaignService",
    "KingdomSummary",
    "ProvinceRow",
    "ResourceRow",
    "EventRow",
    "FactionRow",
    "RelationRow",
    "SimulationStatus",
]

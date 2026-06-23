"""Qt model for observer chronicle summary rows."""
from __future__ import annotations

from typing import List, Optional

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from warfare_simulation.services.campaign_service import ObserverSummaryRow

_HEADERS = [
    "Period",
    "Title",
    "Date Range",
    "Turn",
    "Narrative",
    "Events",
    "Audits",
    "Observer Logs",
    "Highlights",
]
_FIELDS = [
    "period",
    "title",
    "date_range",
    "turn",
    "narrative",
    "event_count",
    "audit_count",
    "observer_log_count",
    "highlights",
]
_NUMERIC_FIELDS = {"turn", "event_count", "audit_count", "observer_log_count"}


class ObserverSummaryTableModel(QAbstractTableModel):
    """Read-only table model for daily, weekly, monthly, and yearly chronicles."""

    def __init__(self, rows: Optional[List[ObserverSummaryRow]] = None, parent=None) -> None:
        super().__init__(parent)
        self._rows: List[ObserverSummaryRow] = rows or []

    def refresh(self, rows: List[ObserverSummaryRow]) -> None:
        self.beginResetModel()
        self._rows = rows
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:  # noqa: N802
        return len(self._rows)

    def columnCount(self, parent=QModelIndex()) -> int:  # noqa: N802
        return len(_HEADERS)

    def headerData(  # noqa: N802
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return _HEADERS[section]
        return None

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        row = self._rows[index.row()]
        field = _FIELDS[index.column()]
        value = getattr(row, field)

        if role == Qt.ItemDataRole.DisplayRole:
            return str(value)

        if role == Qt.ItemDataRole.TextAlignmentRole:
            if field in _NUMERIC_FIELDS or field in {"period", "date_range"}:
                return int(Qt.AlignmentFlag.AlignCenter)
            return int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        return None

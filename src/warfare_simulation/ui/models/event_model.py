"""Qt model for the Event Log table."""
from __future__ import annotations

from typing import List, Optional

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QColor

from warfare_simulation.services.campaign_service import EventRow

_HEADERS = ["Turn", "Category", "Event", "Impact"]
_FIELDS = ["turn", "category", "description", "impact"]

_CATEGORY_COLORS: dict[str, str] = {
    "Military":   "#c45f5f",
    "Diplomacy":  "#5d9bd4",
    "Economy":    "#5dbd7a",
    "Logistics":  "#c9a84c",
    "System":     "#6a7489",
    "Natural":    "#8a5dbd",
    "Intrigue":   "#bd5d9b",
}


class EventTableModel(QAbstractTableModel):
    def __init__(self, rows: Optional[List[EventRow]] = None, parent=None) -> None:
        super().__init__(parent)
        self._rows: List[EventRow] = rows or []

    def refresh(self, rows: List[EventRow]) -> None:
        self.beginResetModel()
        self._rows = rows
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:  # noqa: N802
        return len(self._rows)

    def columnCount(self, parent=QModelIndex()) -> int:  # noqa: N802
        return len(_HEADERS)

    def headerData(self, section: int, orientation: Qt.Orientation,  # noqa: N802
                   role: int = Qt.ItemDataRole.DisplayRole):
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

        if role == Qt.ItemDataRole.ForegroundRole and field == "category":
            hex_color = _CATEGORY_COLORS.get(str(value), "#c8bfa8")
            return QColor(hex_color)

        if role == Qt.ItemDataRole.TextAlignmentRole:
            if field == "turn":
                return int(Qt.AlignmentFlag.AlignCenter)
            return int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        return None

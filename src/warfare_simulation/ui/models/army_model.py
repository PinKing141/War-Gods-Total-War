"""Qt model for the Army Inspector table."""
from __future__ import annotations

from typing import List, Optional

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QColor

from warfare_simulation.services.campaign_service import ArmyRow

_HEADERS = [
    "Unit", "Type", "Soldiers", "Veterans", "Strength", "Morale", "Fatigue",
    "Armour", "Status", "Location", "Commander",
]
_FIELDS = [
    "name", "unit_type", "soldiers", "veterans", "strength", "morale", "fatigue",
    "armor", "status", "location", "commander",
]

_COLOR_GOOD = QColor("#5dbd7a")
_COLOR_WARN = QColor("#c9a84c")
_COLOR_BAD = QColor("#c45f5f")


class ArmyTableModel(QAbstractTableModel):
    """Read-only table model exposing unit readiness for observer inspection."""

    def __init__(self, rows: Optional[List[ArmyRow]] = None, parent=None) -> None:
        super().__init__(parent)
        self._rows: List[ArmyRow] = rows or []

    def refresh(self, rows: List[ArmyRow]) -> None:
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
            return f"{value:,}" if isinstance(value, int) else str(value)

        if role == Qt.ItemDataRole.ForegroundRole:
            if field == "morale":
                if value < 40:
                    return _COLOR_BAD
                if value < 70:
                    return _COLOR_WARN
                return _COLOR_GOOD
            if field == "fatigue":
                if value >= 70:
                    return _COLOR_BAD
                if value >= 35:
                    return _COLOR_WARN
                return _COLOR_GOOD
            if field == "strength":
                if value < 300:
                    return _COLOR_BAD
                if value < 600:
                    return _COLOR_WARN
                return _COLOR_GOOD

        if role == Qt.ItemDataRole.TextAlignmentRole:
            if isinstance(value, int):
                return int(Qt.AlignmentFlag.AlignCenter)
            return int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        return None

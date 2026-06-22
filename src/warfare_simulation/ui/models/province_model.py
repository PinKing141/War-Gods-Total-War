"""Qt model for the Provinces table."""
from __future__ import annotations

from typing import List, Optional

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QColor

from warfare_simulation.services.campaign_service import ProvinceRow

_HEADERS = [
    "Province", "Population", "Fort", "Food Stored",
    "Monthly Tax", "Loyalty %", "Garrison", "Governor",
]
_FIELDS = [
    "name", "population", "fort_level", "food_stored",
    "monthly_tax", "loyalty", "garrison", "governor",
]
_LOYALTY_WARN = 65   # below this → amber
_LOYALTY_BAD  = 40   # below this → red


class ProvinceTableModel(QAbstractTableModel):
    def __init__(self, rows: Optional[List[ProvinceRow]] = None, parent=None) -> None:
        super().__init__(parent)
        self._rows: List[ProvinceRow] = rows or []

    def refresh(self, rows: List[ProvinceRow]) -> None:
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

        if role == Qt.ItemDataRole.ForegroundRole and field == "loyalty":
            if value < _LOYALTY_BAD:
                return QColor("#c45f5f")
            if value < _LOYALTY_WARN:
                return QColor("#c9a84c")

        if role == Qt.ItemDataRole.TextAlignmentRole:
            if isinstance(value, int):
                return int(Qt.AlignmentFlag.AlignCenter)
            return int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        return None

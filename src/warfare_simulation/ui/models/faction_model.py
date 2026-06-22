"""Qt model for the Factions table."""
from __future__ import annotations

from typing import List, Optional

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QColor

from warfare_simulation.services.campaign_service import FactionRow

_HEADERS = ["Faction", "Type", "Power", "Wealth", "Stability"]
_FIELDS = ["name", "faction_type", "power_level", "wealth", "stability"]

_LOW = 35
_HIGH = 65


def _bar_color(value: int) -> QColor:
    if value < _LOW:
        return QColor("#c45f5f")
    if value < _HIGH:
        return QColor("#c9a84c")
    return QColor("#5dbd7a")


class FactionTableModel(QAbstractTableModel):
    def __init__(self, rows: Optional[List[FactionRow]] = None, parent=None) -> None:
        super().__init__(parent)
        self._rows: List[FactionRow] = rows or []

    def refresh(self, rows: List[FactionRow]) -> None:
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

        if role == Qt.ItemDataRole.ForegroundRole and field in ("power_level", "wealth", "stability"):
            return _bar_color(int(value))

        if role == Qt.ItemDataRole.TextAlignmentRole:
            if isinstance(value, int):
                return int(Qt.AlignmentFlag.AlignCenter)
            return int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        return None

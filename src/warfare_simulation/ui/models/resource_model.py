"""Qt model for the Resources table."""
from __future__ import annotations

from typing import List, Optional

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QColor

from warfare_simulation.services.campaign_service import ResourceRow

_HEADERS = [
    "Resource", "Stored", "Monthly +", "Monthly −", "Net / Month", "Capacity", "Fill %",
]
_FIELDS = [
    "resource_type", "stored", "monthly_production", "monthly_consumption",
    "net_change", "max_storage",
]

_COLOR_POS = QColor("#5dbd7a")
_COLOR_NEG = QColor("#c45f5f")
_COLOR_WARN = QColor("#c9a84c")


class ResourceTableModel(QAbstractTableModel):
    def __init__(self, rows: Optional[List[ResourceRow]] = None, parent=None) -> None:
        super().__init__(parent)
        self._rows: List[ResourceRow] = rows or []

    def refresh(self, rows: List[ResourceRow]) -> None:
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
        col = index.column()

        # Fill % is a derived column (index 6) not directly in _FIELDS
        if col == 6:
            if role == Qt.ItemDataRole.DisplayRole:
                pct = int(row.stored / row.max_storage * 100) if row.max_storage else 0
                return f"{pct}%"
            if role == Qt.ItemDataRole.ForegroundRole:
                pct = int(row.stored / row.max_storage * 100) if row.max_storage else 0
                if pct < 25:
                    return _COLOR_NEG
                if pct < 60:
                    return _COLOR_WARN
                return _COLOR_POS
            if role == Qt.ItemDataRole.TextAlignmentRole:
                return int(Qt.AlignmentFlag.AlignCenter)
            return None

        field = _FIELDS[col]
        value = getattr(row, field)

        if role == Qt.ItemDataRole.DisplayRole:
            if field == "net_change":
                return f"+{value:,}" if value >= 0 else f"{value:,}"
            return f"{value:,}" if isinstance(value, int) else str(value)

        if role == Qt.ItemDataRole.ForegroundRole and field == "net_change":
            return _COLOR_POS if value >= 0 else _COLOR_NEG

        if role == Qt.ItemDataRole.TextAlignmentRole:
            if isinstance(value, int):
                return int(Qt.AlignmentFlag.AlignCenter)
            return int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        return None

"""Qt model for the observer timeline viewer."""

from __future__ import annotations

from typing import List, Optional

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QColor

from warfare_simulation.services.campaign_service import TimelineRow

_HEADERS = ["Date", "Turn", "Kind", "System", "Title", "Details"]
_FIELDS = ["date", "turn", "kind", "system", "title", "details"]

_KIND_COLORS = {
    "summary": "#c9a84c",
    "event": "#5d9bd4",
    "observer": "#5dbd7a",
}


class TimelineTableModel(QAbstractTableModel):
    """Read-only table model exposing a dated campaign timeline."""

    def __init__(self, rows: Optional[List[TimelineRow]] = None, parent=None) -> None:
        super().__init__(parent)
        self._rows: List[TimelineRow] = rows or []

    def refresh(self, rows: List[TimelineRow]) -> None:
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

        if role == Qt.ItemDataRole.ForegroundRole and field == "kind":
            return QColor(_KIND_COLORS.get(str(value), "#c8bfa8"))

        if role == Qt.ItemDataRole.TextAlignmentRole:
            if field in {"date", "turn", "kind", "system"}:
                return int(Qt.AlignmentFlag.AlignCenter)
            return int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        return None

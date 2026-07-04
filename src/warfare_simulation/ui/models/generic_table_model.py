"""Generic Qt table model for service-provided dictionary rows."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QColor


class GenericTableModel(QAbstractTableModel):
    """Small reusable table model for read-only dashboard/lore tables.

    The service layer owns all data access.  UI widgets receive already-shaped
    dictionaries and this model simply renders them.
    """

    def __init__(
        self,
        headers: list[str],
        fields: list[str],
        rows: Iterable[Mapping[str, Any]] | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._headers = headers
        self._fields = fields
        self._rows: list[Mapping[str, Any]] = list(rows or [])

    def refresh(self, rows: Iterable[Mapping[str, Any]]) -> None:
        self.beginResetModel()
        self._rows = list(rows)
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:  # noqa: N802
        return len(self._rows)

    def columnCount(self, parent=QModelIndex()) -> int:  # noqa: N802
        return len(self._headers)

    def headerData(  # noqa: N802
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self._headers[section]
        return None

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        row = self._rows[index.row()]
        field = self._fields[index.column()]
        value = row.get(field, "")

        if role == Qt.ItemDataRole.DisplayRole:
            if isinstance(value, bool):
                return "yes" if value else "no"
            return str(value)

        if role == Qt.ItemDataRole.ForegroundRole and isinstance(value, int):
            if value < 0:
                return QColor("#c45f5f")
            if value >= 70:
                return QColor("#5dbd7a")
            if value >= 40:
                return QColor("#c9a84c")

        if role == Qt.ItemDataRole.TextAlignmentRole:
            if isinstance(value, int):
                return int(Qt.AlignmentFlag.AlignCenter)
            return int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        return None

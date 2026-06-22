"""Generic sortable table view widget — reused by all tab views."""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QAbstractTableModel, QSortFilterProxyModel, Qt
from PySide6.QtWidgets import QHeaderView, QTableView, QVBoxLayout, QWidget


class SortableTableView(QWidget):
    """A sortable, read-only table view backed by any QAbstractTableModel."""

    def __init__(
        self,
        model: QAbstractTableModel,
        stretch_last: bool = True,
        resize_columns: Optional[list[int]] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)

        self._proxy = QSortFilterProxyModel(self)
        self._proxy.setSourceModel(model)
        self._proxy.setSortRole(Qt.ItemDataRole.DisplayRole)

        self._table = QTableView()
        self._table.setModel(self._proxy)
        self._table.setAlternatingRowColors(True)
        self._table.setSortingEnabled(True)
        self._table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(False)
        self._table.setWordWrap(False)

        hdr = self._table.horizontalHeader()
        if resize_columns:
            for col in resize_columns:
                hdr.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        else:
            hdr.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

        if stretch_last:
            hdr.setStretchLastSection(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._table)

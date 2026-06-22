"""Kingdom sidebar panel — pure presentation widget."""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from warfare_simulation.services.campaign_service import KingdomSummary


def _section_label(text: str) -> QLabel:
    lbl = QLabel(text.upper())
    lbl.setObjectName("sectionHeader")
    return lbl


def _stat_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("statLabel")
    lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    return lbl


def _value_label() -> QLabel:
    lbl = QLabel("—")
    lbl.setObjectName("statValue")
    lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    return lbl


def _divider() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFrameShadow(QFrame.Shadow.Plain)
    return line


class KingdomPanel(QWidget):
    """Left-sidebar showing the active kingdom's vital statistics."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("kingdomPanel")
        self.setFixedWidth(230)

        # Identity
        self._name_lbl = QLabel("—")
        self._name_lbl.setObjectName("kingdomName")
        self._name_lbl.setWordWrap(True)
        self._name_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self._ruler_lbl = QLabel("—")
        self._ruler_lbl.setObjectName("rulerLabel")
        self._ruler_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self._date_lbl = QLabel("—")
        self._date_lbl.setObjectName("dateLabel")
        self._date_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        # Economy stat values
        self._treasury = _value_label()
        self._income   = _value_label()
        self._expenses = _value_label()
        self._net      = _value_label()

        # Realm stat values
        self._morale  = _value_label()
        self._loyalty = _value_label()
        self._grain   = _value_label()

        self._assemble()

    # ------------------------------------------------------------------

    def _assemble(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 16, 12, 12)
        layout.setSpacing(0)

        layout.addWidget(self._name_lbl)
        layout.addSpacing(4)
        layout.addWidget(self._ruler_lbl)
        layout.addSpacing(2)
        layout.addWidget(self._date_lbl)
        layout.addSpacing(18)

        layout.addWidget(_divider())
        layout.addSpacing(14)
        layout.addWidget(_section_label("Economy"))
        layout.addSpacing(8)
        layout.addLayout(self._grid([
            ("Treasury",    self._treasury),
            ("Income",      self._income),
            ("Expenses",    self._expenses),
            ("Net / Month", self._net),
        ]))
        layout.addSpacing(18)

        layout.addWidget(_divider())
        layout.addSpacing(14)
        layout.addWidget(_section_label("Realm"))
        layout.addSpacing(8)
        layout.addLayout(self._grid([
            ("Morale",         self._morale),
            ("Loyalty",        self._loyalty),
            ("Grain (Months)", self._grain),
        ]))

        layout.addStretch()

    @staticmethod
    def _grid(pairs: list) -> QGridLayout:
        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(9)
        grid.setContentsMargins(0, 0, 0, 0)
        for row, (label_text, value_widget) in enumerate(pairs):
            grid.addWidget(_stat_label(label_text), row, 0)
            grid.addWidget(value_widget, row, 1)
        grid.setColumnStretch(1, 1)
        return grid

    # ------------------------------------------------------------------

    def refresh(self, summary: Optional[KingdomSummary]) -> None:
        if summary is None:
            return

        self._name_lbl.setText(summary.name)
        self._ruler_lbl.setText(summary.ruler)
        self._date_lbl.setText(
            f"{summary.current_day:02d}/{summary.current_month:02d}/{summary.current_year:04d}"
        )

        self._treasury.setText(f"{summary.treasury:,} ◆")

        self._income.setText(f"+{summary.monthly_income:,}")
        self._income.setObjectName("statValuePositive")

        self._expenses.setText(f"−{summary.monthly_expenses:,}")
        self._expenses.setObjectName("statValueNegative")

        net = summary.net_income
        self._net.setText(f"+{net:,}" if net >= 0 else f"{net:,}")
        self._net.setObjectName("statValuePositive" if net >= 0 else "statValueNegative")

        self._morale.setText(f"{summary.morale}%")
        self._loyalty.setText(f"{summary.loyalty}%")
        self._grain.setText(str(summary.grain_stores))

        # Re-polish dynamic objectName changes so QSS picks them up
        for lbl in (self._income, self._expenses, self._net):
            lbl.style().unpolish(lbl)
            lbl.style().polish(lbl)

"""Main application window.

Owns the window frame, tab layout, toolbar, and data refresh cycle.
No simulation state or domain objects live here — everything goes through
the CampaignService facade.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, QThread, QTimer, Signal, Slot
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QStatusBar,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from warfare_simulation.services.campaign_service import CampaignService
from warfare_simulation.ui.models.event_model import EventTableModel
from warfare_simulation.ui.models.faction_model import FactionTableModel
from warfare_simulation.ui.models.province_model import ProvinceTableModel
from warfare_simulation.ui.models.resource_model import ResourceTableModel
from warfare_simulation.ui.widgets.kingdom_panel import KingdomPanel
from warfare_simulation.ui.widgets.table_view import SortableTableView


class _TickWorker(QObject):
    """Background worker for daily advancement while autoplay is running."""

    finished = Signal()
    errored = Signal(str)

    def __init__(self, service: CampaignService) -> None:
        super().__init__()
        self._service = service

    @Slot()
    def run(self) -> None:
        try:
            self._service.advance_day()
        except Exception as exc:  # noqa: BLE001
            self.errored.emit(str(exc))
        finally:
            self.finished.emit()


class MainWindow(QMainWindow):
    """Campaign observatory window backed only by the service layer."""

    _SPEED_STEPS = ["0.5x", "1x", "2x", "3x"]

    def __init__(self, service: CampaignService, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._service = service
        self._thread: Optional[QThread] = None
        self._worker: Optional[_TickWorker] = None
        self._selected_speed = "1x"
        self._tick_timer = QTimer(self)
        self._tick_timer.timeout.connect(self._on_timer_tick)

        self._province_model = ProvinceTableModel()
        self._resource_model = ResourceTableModel()
        self._event_model = EventTableModel()
        self._faction_model = FactionTableModel()

        self._build_ui()
        self._load_stylesheet()
        self.refresh()

    def _build_ui(self) -> None:
        self.setWindowTitle("War Gods — Campaign Observatory")
        self.resize(1300, 820)
        self.setMinimumSize(960, 600)

        root = QWidget()
        self.setCentralWidget(root)
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self._kingdom_panel = KingdomPanel()
        root_layout.addWidget(self._kingdom_panel)

        separator = QWidget()
        separator.setFixedWidth(1)
        separator.setStyleSheet("background-color: #2e3347;")
        root_layout.addWidget(separator)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        content_layout.addWidget(self._make_toolbar())
        content_layout.addWidget(self._make_tabs())
        root_layout.addWidget(content)

        self._status = QStatusBar()
        self.setStatusBar(self._status)

    def _make_toolbar(self) -> QToolBar:
        bar = QToolBar()
        bar.setMovable(False)
        bar.setFloatable(False)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self._date_label = QLabel("")
        self._date_label.setObjectName("statLabel")
        self._date_label.setContentsMargins(0, 0, 16, 0)

        self._speed_label = QLabel("")
        self._speed_label.setObjectName("statLabel")
        self._speed_label.setContentsMargins(0, 0, 8, 0)

        self._pause_btn = QPushButton("▶ Play")
        self._pause_btn.clicked.connect(self._on_toggle_pause)

        self._slower_btn = QPushButton("− Speed")
        self._slower_btn.clicked.connect(self._on_slower)

        self._faster_btn = QPushButton("+ Speed")
        self._faster_btn.clicked.connect(self._on_faster)

        bar.addWidget(spacer)
        bar.addWidget(self._date_label)
        bar.addWidget(self._speed_label)
        bar.addWidget(self._pause_btn)
        bar.addWidget(self._slower_btn)
        bar.addWidget(self._faster_btn)
        return bar

    def _make_tabs(self) -> QTabWidget:
        tabs = QTabWidget()
        tabs.setDocumentMode(True)

        tabs.addTab(SortableTableView(self._province_model), "  Provinces  ")
        tabs.addTab(
            SortableTableView(self._resource_model, resize_columns=[0, 1, 2, 3, 4, 5, 6]),
            "  Resources  ",
        )
        tabs.addTab(
            SortableTableView(
                self._faction_model,
                resize_columns=[0, 1, 2, 3, 4],
                stretch_last=False,
            ),
            "  Factions  ",
        )
        tabs.addTab(
            SortableTableView(
                self._event_model,
                resize_columns=[0, 1],
                stretch_last=True,
            ),
            "  Event Log  ",
        )
        return tabs

    def _load_stylesheet(self) -> None:
        qss = Path(__file__).parent / "assets" / "style.qss"
        if qss.exists():
            self.setStyleSheet(qss.read_text(encoding="utf-8"))

    def closeEvent(self, event: QCloseEvent) -> None:
        self._tick_timer.stop()
        if self._thread is not None:
            try:
                if self._thread.isRunning():
                    self._thread.quit()
                    self._thread.wait()
            except RuntimeError:
                pass
        self._thread = None
        self._worker = None
        super().closeEvent(event)

    def refresh(self) -> None:
        summary = self._service.get_kingdom_summary()
        sim = self._service.get_simulation_status()

        if sim.simulation_speed in self._SPEED_STEPS:
            self._selected_speed = sim.simulation_speed

        self._kingdom_panel.refresh(summary)
        self._province_model.refresh(self._service.get_provinces())
        self._resource_model.refresh(self._service.get_resources())
        self._event_model.refresh(self._service.get_events())
        self._faction_model.refresh(self._service.get_factions())

        self._date_label.setText(sim.formatted_date)
        self._pause_btn.setText("▶ Play" if sim.is_paused else "⏸ Pause")
        self._speed_label.setText(f"Speed: {self._selected_speed}")

        if summary is not None:
            self._status.showMessage(
                f"{summary.name}  —  Treasury: {summary.treasury:,} ◆  "
                f"  Net: {summary.net_income:+,} / month  ·  Date: {sim.formatted_date}"
            )

        self._apply_timer_state(sim.is_paused)

    def _apply_timer_state(self, is_paused: bool) -> None:
        if is_paused:
            self._service.set_simulation_speed("paused")
            self._tick_timer.stop()
            return
        self._service.set_simulation_speed(self._selected_speed)
        interval = self._service.get_speed_interval_ms() or 1000
        self._tick_timer.start(interval)

    def _thread_is_running(self) -> bool:
        if self._thread is None:
            return False
        try:
            return self._thread.isRunning()
        except RuntimeError:
            self._thread = None
            self._worker = None
            return False

    @Slot()
    def _on_timer_tick(self) -> None:
        if self._thread_is_running():
            return
        self._start_tick_worker()

    @Slot()
    def _on_toggle_pause(self) -> None:
        sim = self._service.get_simulation_status()
        self._apply_timer_state(not sim.is_paused)
        self.refresh()

    @Slot()
    def _on_slower(self) -> None:
        current_index = self._SPEED_STEPS.index(self._selected_speed)
        self._selected_speed = self._SPEED_STEPS[max(0, current_index - 1)]
        if not self._service.get_simulation_status().is_paused:
            self._service.set_simulation_speed(self._selected_speed)
        self.refresh()

    @Slot()
    def _on_faster(self) -> None:
        current_index = self._SPEED_STEPS.index(self._selected_speed)
        self._selected_speed = self._SPEED_STEPS[min(len(self._SPEED_STEPS) - 1, current_index + 1)]
        if not self._service.get_simulation_status().is_paused:
            self._service.set_simulation_speed(self._selected_speed)
        self.refresh()

    def _start_tick_worker(self) -> None:
        if self._thread_is_running():
            return

        self._pause_btn.setEnabled(False)
        self._slower_btn.setEnabled(False)
        self._faster_btn.setEnabled(False)
        self._status.showMessage("Advancing day…")

        self._thread = QThread(self)
        self._worker = _TickWorker(self._service)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._on_thread_finished)
        self._thread.finished.connect(self._thread.deleteLater)
        self._worker.finished.connect(self._on_tick_done)
        self._worker.errored.connect(self._on_tick_error)

        self._thread.start()

    @Slot()
    def _on_thread_finished(self) -> None:
        self._thread = None
        self._worker = None

    @Slot()
    def _on_tick_done(self) -> None:
        self.refresh()
        self._pause_btn.setEnabled(True)
        self._slower_btn.setEnabled(True)
        self._faster_btn.setEnabled(True)

    @Slot(str)
    def _on_tick_error(self, msg: str) -> None:
        self._status.showMessage(f"Simulation error: {msg}")
        self._pause_btn.setEnabled(True)
        self._slower_btn.setEnabled(True)
        self._faster_btn.setEnabled(True)

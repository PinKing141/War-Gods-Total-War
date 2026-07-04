"""Main application window.

Owns the window frame, command-center layout, toolbar, and data refresh cycle.
No simulation state or domain objects live here — everything goes through
CampaignService.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, QThread, QTimer, Signal, Slot
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGridLayout,
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

from warfare_simulation.services.campaign_service import CampaignService, WorldOverview
from warfare_simulation.ui.models.army_model import ArmyTableModel
from warfare_simulation.ui.models.event_model import EventTableModel
from warfare_simulation.ui.models.faction_model import FactionTableModel
from warfare_simulation.ui.models.generic_table_model import GenericTableModel
from warfare_simulation.ui.models.observer_summary_model import ObserverSummaryTableModel
from warfare_simulation.ui.models.province_model import ProvinceTableModel
from warfare_simulation.ui.models.resource_model import ResourceTableModel
from warfare_simulation.ui.models.timeline_model import TimelineTableModel
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
    """Campaign command-center window backed only by the service layer."""

    _SPEED_STEPS = ["1x", "2x", "5x", "fast"]

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
        self._army_model = ArmyTableModel()
        self._observer_summary_model = ObserverSummaryTableModel()
        self._timeline_model = TimelineTableModel()

        self._seed_faction_model = GenericTableModel(
            ["ID", "Faction", "Identity", "Culture", "Species", "Religion", "Government", "Goal"],
            ["faction_id", "name", "identity", "dominant_culture", "dominant_species", "religion_id", "government", "primary_goal"],
        )
        self._seed_province_model = GenericTableModel(
            ["ID", "Province", "Imperial Name", "Controller", "Terrain", "Resource", "Road", "Fort", "Strategic"],
            ["province_id", "common_name", "old_imperial_name", "controller", "terrain", "primary_resource", "road_level", "fort_level", "strategic_value"],
        )
        self._seed_relation_model = GenericTableModel(
            ["ID", "Faction A", "Faction B", "Score", "War Risk", "Main Tension"],
            ["relation_id", "faction_a", "faction_b", "score", "war_risk", "main_tension"],
        )
        self._seed_character_model = GenericTableModel(
            ["ID", "Name", "Species", "Culture", "Faction", "Role", "Age", "Pressure"],
            ["character_id", "name", "species_id", "culture_id", "faction_id", "role", "age", "core_pressure"],
        )
        self._claim_model = GenericTableModel(
            ["ID", "Claimant", "Target", "Type", "Strength", "Decay", "Myth", "Recognized By", "Source"],
            ["claim_id", "claimant", "target", "claim_type", "strength", "decay_rate", "myth_status", "recognized_by", "source"],
        )
        self._mage_model = GenericTableModel(
            ["ID", "Character", "Species", "Capacity", "Control", "Recovery", "Strain", "Specialization", "Legal", "Patron", "Risk"],
            ["mage_id", "character_id", "species_id", "capacity", "control", "recovery", "strain_tolerance", "specialization", "legal_status", "patron_faction", "risk_score"],
        )
        self._culture_model = GenericTableModel(
            ["ID", "Self Name", "Common", "Imperial", "Species", "Location", "Military", "Contradiction"],
            ["culture_id", "self_name", "common_name", "old_imperial_name", "dominant_species", "location", "military_style", "contradiction"],
        )
        self._religion_model = GenericTableModel(
            ["ID", "Name", "Type", "War Stance", "Mage Stance", "Holy Trigger", "Core Claim"],
            ["religion_id", "name", "type", "war_stance", "mage_stance", "holy_war_triggers", "core_claim"],
        )
        self._species_model = GenericTableModel(
            ["ID", "Common", "Self", "Lifespan", "Fertility", "Food", "Magic", "Politics"],
            ["species_id", "common_name", "self_name", "avg_lifespan", "fertility_rate", "food_need", "magic_tendency", "political_pattern"],
        )
        self._ai_weight_model = GenericTableModel(
            ["ID", "Applies To", "Weight", "Drives"],
            ["ai_weight_id", "applies_to", "weight", "drives"],
        )
        self._mechanic_hook_model = GenericTableModel(
            ["ID", "Input", "Output"],
            ["hook_id", "input_text", "output_text"],
        )

        self._overview_labels: dict[str, QLabel] = {}

        self._build_ui()
        self._load_stylesheet()
        self.refresh()

    def _build_ui(self) -> None:
        self.setWindowTitle("War Gods — Living Chronicle Command Center")
        self.resize(1500, 900)
        self.setMinimumSize(1100, 680)

        root = QWidget()
        self.setCentralWidget(root)
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

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
        bar.setObjectName("commandToolbar")
        bar.setMovable(False)
        bar.setFloatable(False)

        title = QLabel("WAR GODS // LIVING CHRONICLE")
        title.setObjectName("toolbarTitle")
        subtitle = QLabel("Lore-driven observer command center")
        subtitle.setObjectName("toolbarSubtitle")

        title_box = QWidget()
        title_layout = QVBoxLayout(title_box)
        title_layout.setContentsMargins(0, 0, 12, 0)
        title_layout.setSpacing(0)
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self._date_label = QLabel("")
        self._date_label.setObjectName("statLabel")
        self._date_label.setContentsMargins(0, 0, 16, 0)

        self._speed_label = QLabel("")
        self._speed_label.setObjectName("statLabel")
        self._speed_label.setContentsMargins(0, 0, 8, 0)

        self._pause_btn = QPushButton("▶ Play")
        self._pause_btn.setObjectName("primaryButton")
        self._pause_btn.clicked.connect(self._on_toggle_pause)

        self._slower_btn = QPushButton("− Speed")
        self._slower_btn.clicked.connect(self._on_slower)

        self._faster_btn = QPushButton("+ Speed")
        self._faster_btn.clicked.connect(self._on_faster)

        self._export_btn = QPushButton("Export Workbook")
        self._export_btn.clicked.connect(self._on_export_workbook)

        bar.addWidget(title_box)
        bar.addWidget(spacer)
        bar.addWidget(self._date_label)
        bar.addWidget(self._speed_label)
        bar.addWidget(self._pause_btn)
        bar.addWidget(self._slower_btn)
        bar.addWidget(self._faster_btn)
        bar.addWidget(self._export_btn)
        return bar

    def _make_tabs(self) -> QTabWidget:
        tabs = QTabWidget()
        tabs.setDocumentMode(True)

        tabs.addTab(self._make_command_center(), "  Command Center  ")
        tabs.addTab(
            SortableTableView(
                self._timeline_model,
                resize_columns=[0, 1, 2, 3, 4],
                stretch_last=True,
            ),
            "  Timeline  ",
        )
        tabs.addTab(self._make_seed_frontier_tabs(), "  Frontier Seed  ")
        tabs.addTab(self._make_lore_tabs(), "  Lore Systems  ")
        tabs.addTab(SortableTableView(self._province_model), "  Active Provinces  ")
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
            "  Active Factions  ",
        )
        tabs.addTab(
            SortableTableView(
                self._army_model,
                resize_columns=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
                stretch_last=True,
            ),
            "  Armies  ",
        )
        tabs.addTab(
            SortableTableView(
                self._event_model,
                resize_columns=[0, 1, 2, 3, 4, 5],
                stretch_last=True,
            ),
            "  Event Log  ",
        )
        tabs.addTab(
            SortableTableView(
                self._observer_summary_model,
                resize_columns=[0, 1, 2, 3, 5, 6, 7],
                stretch_last=True,
            ),
            "  Chronicle  ",
        )
        return tabs

    def _make_command_center(self) -> QWidget:
        page = QWidget()
        page.setObjectName("commandCenter")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        hero = QFrame()
        hero.setObjectName("heroPanel")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(18, 16, 18, 16)
        hero_layout.setSpacing(6)

        title = QLabel("Frontier campaign intelligence")
        title.setObjectName("heroTitle")
        body = QLabel(
            "The dashboard now reads the CSV-backed lore layer: active campaign state, seed frontier, claims, mages, cultures, religions, AI weights and mechanics hooks."
        )
        body.setObjectName("heroBody")
        body.setWordWrap(True)
        hero_layout.addWidget(title)
        hero_layout.addWidget(body)
        layout.addWidget(hero)

        cards = QGridLayout()
        cards.setHorizontalSpacing(12)
        cards.setVerticalSpacing(12)

        specs = [
            ("active_factions", "Active Factions"),
            ("active_provinces", "Active Provinces"),
            ("active_armies", "Army Units"),
            ("seed_factions", "Seed Factions"),
            ("seed_provinces", "Seed Provinces"),
            ("claims", "Claims"),
            ("mages", "Mages"),
            ("cultures", "Cultures"),
            ("religions", "Religions"),
            ("ai_weights", "AI Weights"),
            ("mechanic_hooks", "Mechanic Hooks"),
            ("timeline_entries", "Timeline Rows"),
        ]
        for index, (key, label) in enumerate(specs):
            cards.addWidget(self._make_overview_card(key, label), index // 4, index % 4)
        layout.addLayout(cards)

        quick_tabs = QTabWidget()
        quick_tabs.setDocumentMode(True)
        quick_tabs.addTab(SortableTableView(self._claim_model, stretch_last=True), "Claims")
        quick_tabs.addTab(SortableTableView(self._mage_model, stretch_last=True), "Mages")
        quick_tabs.addTab(SortableTableView(self._seed_relation_model, stretch_last=True), "Tensions")
        quick_tabs.addTab(SortableTableView(self._ai_weight_model, stretch_last=True), "AI Priorities")
        layout.addWidget(quick_tabs, 1)

        return page

    def _make_overview_card(self, key: str, label_text: str) -> QFrame:
        card = QFrame()
        card.setObjectName("overviewCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)

        label = QLabel(label_text.upper())
        label.setObjectName("overviewLabel")
        value = QLabel("—")
        value.setObjectName("overviewValue")
        value.setMinimumHeight(28)

        self._overview_labels[key] = value
        layout.addWidget(label)
        layout.addWidget(value)
        return card

    def _make_seed_frontier_tabs(self) -> QTabWidget:
        tabs = QTabWidget()
        tabs.setDocumentMode(True)
        tabs.addTab(SortableTableView(self._seed_faction_model, stretch_last=True), "Factions")
        tabs.addTab(SortableTableView(self._seed_province_model, stretch_last=True), "Provinces")
        tabs.addTab(SortableTableView(self._seed_relation_model, stretch_last=True), "Relations")
        tabs.addTab(SortableTableView(self._seed_character_model, stretch_last=True), "Characters")
        tabs.addTab(SortableTableView(self._claim_model, stretch_last=True), "Claims")
        tabs.addTab(SortableTableView(self._mage_model, stretch_last=True), "Mages")
        return tabs

    def _make_lore_tabs(self) -> QTabWidget:
        tabs = QTabWidget()
        tabs.setDocumentMode(True)
        tabs.addTab(SortableTableView(self._culture_model, stretch_last=True), "Cultures")
        tabs.addTab(SortableTableView(self._religion_model, stretch_last=True), "Religions")
        tabs.addTab(SortableTableView(self._species_model, stretch_last=True), "Species")
        tabs.addTab(SortableTableView(self._ai_weight_model, stretch_last=True), "AI Weights")
        tabs.addTab(SortableTableView(self._mechanic_hook_model, stretch_last=True), "Mechanic Hooks")
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
        sim = self._service.get_simulation_status()
        overview = self._service.get_world_overview()

        if sim.simulation_speed in self._SPEED_STEPS:
            self._selected_speed = sim.simulation_speed

        self._province_model.refresh(self._service.get_provinces())
        self._resource_model.refresh(self._service.get_resources())
        self._event_model.refresh(self._service.get_events())
        self._faction_model.refresh(self._service.get_factions())
        self._army_model.refresh(self._service.get_armies())
        self._observer_summary_model.refresh(self._service.get_observer_summaries())
        self._timeline_model.refresh(self._service.get_timeline())

        self._seed_faction_model.refresh(self._service.get_seed_factions())
        self._seed_province_model.refresh(self._service.get_seed_provinces())
        self._seed_relation_model.refresh(self._service.get_seed_relations())
        self._seed_character_model.refresh(self._service.get_seed_characters())
        self._claim_model.refresh(self._service.get_claims())
        self._mage_model.refresh(self._service.get_mages())
        self._culture_model.refresh(self._service.get_cultures())
        self._religion_model.refresh(self._service.get_religions())
        self._species_model.refresh(self._service.get_species())
        self._ai_weight_model.refresh(self._service.get_ai_weights())
        self._mechanic_hook_model.refresh(self._service.get_mechanic_hooks())
        self._refresh_overview_cards(overview)

        self._date_label.setText(sim.formatted_date)
        self._pause_btn.setText("▶ Play" if sim.is_paused else "⏸ Pause")
        self._speed_label.setText(f"Speed: {self._selected_speed}")

        self._status.showMessage(f"Observing the living world  ·  Date: {sim.formatted_date}")

        self._apply_timer_state(sim.is_paused)

    def _refresh_overview_cards(self, overview: WorldOverview) -> None:
        for key, label in self._overview_labels.items():
            label.setText(f"{getattr(overview, key):,}")

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
        self._export_btn.setEnabled(False)
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
        self._export_btn.setEnabled(True)

    @Slot(str)
    def _on_tick_error(self, msg: str) -> None:
        self._status.showMessage(f"Simulation error: {msg}")
        self._pause_btn.setEnabled(True)
        self._slower_btn.setEnabled(True)
        self._faster_btn.setEnabled(True)
        self._export_btn.setEnabled(True)

    @Slot()
    def _on_export_workbook(self) -> None:
        """Export the current observer-visible campaign state to an Excel workbook."""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Campaign Workbook",
            "Auster_Campaign_Engine.xlsx",
            "Excel Workbooks (*.xlsx)",
        )
        if not filename:
            return
        output_path = self._service.export_workbook(Path(filename))
        self._status.showMessage(f"Exported campaign workbook to {output_path}")

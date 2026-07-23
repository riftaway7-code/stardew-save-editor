from __future__ import annotations

from PySide6.QtWidgets import QLabel, QMainWindow, QMessageBox, QPushButton, QTabWidget, QVBoxLayout, QWidget

from svse.gui.panels.device_picker import DevicePickerBar
from svse.gui.panels.inventory_tab import InventoryTab
from svse.gui.panels.map_tab import LOCATION_TYPE, MapTab
from svse.gui.panels.money_tab import MoneyTab
from svse.gui.panels.relationships_tab import RelationshipsTab
from svse.gui.session import Session
from svse.gui.workers.background_tasks import run_in_background
from svse.itemdb import default_db
from svse.savemodel.errors import InventoryFullError, TileOccupiedError
from svse.savemodel.validation import ValidationError


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Stardew Valley Save Editor")
        self.resize(720, 560)

        self.session = Session()
        self._worker = None

        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        self.device_bar = DevicePickerBar()
        self.device_bar.save_loaded.connect(self._on_save_loaded)
        layout.addWidget(self.device_bar)

        self.tabs = QTabWidget()
        self.money_tab = MoneyTab()
        self.money_tab.money_changed.connect(self._on_money_changed)
        self.tabs.addTab(self.money_tab, "Money")

        self.inventory_tab = InventoryTab()
        self.inventory_tab.item_add_requested.connect(self._on_item_add_requested)
        self.tabs.addTab(self.inventory_tab, "Inventory")

        self.relationships_tab = RelationshipsTab()
        self.relationships_tab.points_changed.connect(self._on_friendship_points_changed)
        self.tabs.addTab(self.relationships_tab, "Relationships")

        self.map_tab = MapTab(default_db())
        self.map_tab.chest_place_requested.connect(self._on_chest_place_requested)
        self.tabs.addTab(self.map_tab, "Map")

        layout.addWidget(self.tabs)

        bottom = QWidget()
        bottom_layout = QVBoxLayout(bottom)
        self.dirty_label = QLabel("No unsaved changes")
        bottom_layout.addWidget(self.dirty_label)
        self.push_button = QPushButton("Push to Device")
        self.push_button.setEnabled(False)
        self.push_button.clicked.connect(self._on_push_clicked)
        bottom_layout.addWidget(self.push_button)
        layout.addWidget(bottom)

    # -- Loading ------------------------------------------------------------
    def _on_save_loaded(self, udid: str, folder_name: str) -> None:
        self._worker = run_in_background(
            self,
            self.session.pull,
            udid,
            folder_name,
            on_success=self._on_pull_worker_success,
            on_error=self._on_pull_worker_error,
        )

    def _on_pull_worker_success(self, _result) -> None:
        self._populate_tabs()

    def _on_pull_worker_error(self, exc: Exception) -> None:
        QMessageBox.critical(self, "Load Failed", str(exc))

    def _populate_tabs(self) -> None:
        self.money_tab.set_money(self.session.get_money())
        self.money_tab.setEnabled(True)
        self.inventory_tab.set_slots(self.session.get_slots())
        self.inventory_tab.setEnabled(True)
        self.relationships_tab.set_friendships(self.session.get_friendships())
        self.relationships_tab.setEnabled(True)
        self.map_tab.set_placed_objects(self.session.get_placed_objects(LOCATION_TYPE))
        self.map_tab.setEnabled(True)
        self.push_button.setEnabled(True)
        self._update_dirty_label()

    def _update_dirty_label(self) -> None:
        if self.session.dirty:
            self.dirty_label.setText("Unsaved changes - click Push to Device to write them")
        else:
            self.dirty_label.setText("No unsaved changes")

    # -- Money ----------------------------------------------------------
    def _on_money_changed(self, value: int) -> None:
        self.session.set_money(value)
        self._update_dirty_label()

    # -- Inventory --------------------------------------------------------
    def _on_item_add_requested(self, item_id: str, name: str, quantity: int, quality: int) -> None:
        try:
            self.session.add_item(item_id=item_id, name=name, stack=quantity, quality=quality)
        except InventoryFullError as exc:
            self.inventory_tab.show_inventory_full_error(exc)
            return
        self.inventory_tab.set_slots(self.session.get_slots())
        self._update_dirty_label()

    # -- Relationships ------------------------------------------------------
    def _on_friendship_points_changed(self, npc_name: str, points: int) -> None:
        self.session.set_friendship_points(npc_name, points)
        self._update_dirty_label()

    # -- Map / Placement ----------------------------------------------------
    def _on_chest_place_requested(self, x: int, y: int) -> None:
        try:
            self.session.place_chest(LOCATION_TYPE, x, y)
        except TileOccupiedError as exc:
            QMessageBox.warning(self, "Tile Occupied", str(exc))
            return
        self.map_tab.set_placed_objects(self.session.get_placed_objects(LOCATION_TYPE))
        self._update_dirty_label()

    # -- Push -------------------------------------------------------------
    def _on_push_clicked(self) -> None:
        self.push_button.setEnabled(False)
        self.dirty_label.setText("Pushing to device...")
        self._worker = run_in_background(
            self,
            self.session.push,
            on_success=lambda _: self._on_push_succeeded(),
            on_error=self._on_push_failed,
        )

    def _on_push_succeeded(self) -> None:
        self.push_button.setEnabled(True)
        self._update_dirty_label()
        QMessageBox.information(
            self,
            "Pushed",
            "Changes written to the device. Fully close and reopen Stardew "
            "Valley on the device to see them (if it's still running, it "
            "may overwrite what was just written).",
        )

    def _on_push_failed(self, exc: Exception) -> None:
        self.push_button.setEnabled(True)
        self._update_dirty_label()
        if isinstance(exc, ValidationError):
            QMessageBox.critical(self, "Validation Failed", f"Refused to push - {exc}")
        else:
            QMessageBox.critical(self, "Push Failed", str(exc))

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QGridLayout, QLabel, QMessageBox, QVBoxLayout, QWidget

from svse.itemdb import default_db
from svse.savemodel import InventorySlot
from svse.savemodel.constants import BACKPACK_SLOT_COUNT
from svse.savemodel.errors import InventoryFullError
from svse.gui.widgets.inventory_slot_widget import InventorySlotWidget
from svse.gui.widgets.item_picker_dialog import ItemPickerDialog


class InventoryTab(QWidget):
    item_add_requested = Signal(str, str, int, int)  # item_id, name, quantity, quality

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._item_db = default_db()
        self._slot_widgets: list[InventorySlotWidget] = []

        layout = QVBoxLayout(self)

        hint = QLabel(
            "The backpack is hard-capped at 36 slots - the mobile game "
            "ignores anything beyond that even if the save file has more. "
            "Full slots can't be added to; clear one first."
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)

        grid = QGridLayout()
        grid.setSpacing(4)
        for index in range(BACKPACK_SLOT_COUNT):
            row, col = divmod(index, 12)
            slot_widget = InventorySlotWidget(index, self._item_db)
            slot_widget.clicked_with_index.connect(self._on_slot_clicked)
            grid.addWidget(slot_widget, row, col)
            self._slot_widgets.append(slot_widget)
        layout.addLayout(grid)
        layout.addStretch()

        self.setEnabled(False)

    def set_slots(self, slots: list[InventorySlot | None]) -> None:
        for widget, slot in zip(self._slot_widgets, slots):
            widget.set_slot(slot)

    def _on_slot_clicked(self, index: int) -> None:
        dialog = ItemPickerDialog(self._item_db, parent=self)
        if dialog.exec() != ItemPickerDialog.Accepted:
            return
        item = dialog.selected_item()
        if item is None:
            return
        self.item_add_requested.emit(item.id, item.name, dialog.selected_quantity(), dialog.selected_quality())

    def show_inventory_full_error(self, exc: InventoryFullError) -> None:
        QMessageBox.warning(
            self,
            "Backpack Full",
            f"{exc}\n\nUse the Map tab to place a chest and store items "
            "there instead, or clear a backpack slot first.",
        )

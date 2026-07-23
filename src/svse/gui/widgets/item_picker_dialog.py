from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QSpinBox,
    QVBoxLayout,
    QFormLayout,
)

from svse.itemdb import Item, ItemDB, search


class ItemPickerDialog(QDialog):
    """Searchable item picker backed exclusively by the verified item
    database - there is deliberately no free-text ID entry field here. This
    is what closes off the "wrong ID typed from memory" failure mode from
    tonight (3 of 26 hand-typed IDs were wrong)."""

    def __init__(self, item_db: ItemDB, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Item")
        self.setMinimumSize(420, 480)
        self._item_db = item_db
        self._selected_item: Item | None = None

        layout = QVBoxLayout(self)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search items...")
        self.search_box.textChanged.connect(self._on_search_changed)
        layout.addWidget(self.search_box)

        self.results_list = QListWidget()
        self.results_list.itemSelectionChanged.connect(self._on_selection_changed)
        self.results_list.itemDoubleClicked.connect(self._on_double_click)
        layout.addWidget(self.results_list)

        form = QFormLayout()
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(1, 999)
        self.quantity_spin.setValue(1)
        form.addRow("Quantity:", self.quantity_spin)

        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(0, 4)
        self.quality_spin.setSpecialValueText("Normal")
        form.addRow("Quality (4 = gold star):", self.quality_spin)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.ok_button = buttons.button(QDialogButtonBox.Ok)
        self.ok_button.setEnabled(False)
        layout.addWidget(buttons)

        self._populate_results("")

    def _populate_results(self, query: str) -> None:
        self.results_list.clear()
        for item in search(self._item_db, query, limit=100):
            list_item = QListWidgetItem(f"{item.name}  (#{item.id})")
            list_item.setData(1000, item)
            self.results_list.addItem(list_item)

    def _on_search_changed(self, text: str) -> None:
        self._populate_results(text)

    def _on_selection_changed(self) -> None:
        selected = self.results_list.selectedItems()
        if not selected:
            self._selected_item = None
            self.ok_button.setEnabled(False)
            return
        self._selected_item = selected[0].data(1000)
        self.ok_button.setEnabled(True)

    def _on_double_click(self, _item: QListWidgetItem) -> None:
        self.accept()

    def selected_item(self) -> Item | None:
        return self._selected_item

    def selected_quantity(self) -> int:
        return self.quantity_spin.value()

    def selected_quality(self) -> int:
        # UI only exposes the meaningful in-game qualities: 0/1/2/4 (there is
        # no quality "3" in Stardew), so the spinbox uses a 0-4 range but we
        # snap 3 to 4 to avoid an invalid intermediate value.
        value = self.quality_spin.value()
        return 4 if value == 3 else value

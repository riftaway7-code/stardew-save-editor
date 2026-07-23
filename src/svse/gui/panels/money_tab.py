from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFormLayout, QLabel, QPushButton, QSpinBox, QVBoxLayout, QWidget


class MoneyTab(QWidget):
    money_changed = Signal(int)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._loading = False

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.money_spin = QSpinBox()
        self.money_spin.setRange(0, 999_999_999)
        self.money_spin.setGroupSeparatorShown(True)
        self.money_spin.valueChanged.connect(self._on_value_changed)
        form.addRow("Money:", self.money_spin)

        layout.addLayout(form)

        self.hint_label = QLabel(
            "Changes are staged locally - nothing is written to the device "
            "until you click \"Push to Device\"."
        )
        self.hint_label.setWordWrap(True)
        layout.addWidget(self.hint_label)
        layout.addStretch()

        self.setEnabled(False)

    def set_money(self, value: int) -> None:
        self._loading = True
        self.money_spin.setValue(value)
        self._loading = False

    def _on_value_changed(self, value: int) -> None:
        if self._loading:
            return
        self.money_changed.emit(value)

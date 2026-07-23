from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHeaderView,
    QLabel,
    QSlider,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from svse.savemodel import FriendshipInfo
from svse.savemodel.relationships import POINTS_PER_HEART


class RelationshipsTab(QWidget):
    points_changed = Signal(str, int)  # npc_name, points

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._loading = False
        self._npc_order: list[str] = []

        layout = QVBoxLayout(self)

        hint = QLabel(
            "Regular villagers cap at 10 hearts (2500 points). A married "
            "spouse can go up to 14 hearts (3500 points) - the slider's "
            "range adjusts automatically per NPC."
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["NPC", "Hearts", "Points"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

        self.setEnabled(False)

    def set_friendships(self, friendships: dict[str, FriendshipInfo]) -> None:
        self._loading = True
        self._npc_order = sorted(friendships.keys())
        self.table.setRowCount(len(self._npc_order))
        for row, npc_name in enumerate(self._npc_order):
            info = friendships[npc_name]

            name_item = QTableWidgetItem(npc_name)
            if info.status in ("Married", "Roommate"):
                name_item.setText(f"{npc_name}  ({info.status})")
            self.table.setItem(row, 0, name_item)

            hearts_item = QTableWidgetItem(f"{info.hearts} / {info.max_points // POINTS_PER_HEART}")
            self.table.setItem(row, 1, hearts_item)

            slider = QSlider(Qt.Horizontal)
            slider.setRange(0, info.max_points)
            slider.setValue(info.points)
            slider.setSingleStep(POINTS_PER_HEART)
            slider.valueChanged.connect(lambda value, name=npc_name, r=row: self._on_slider_changed(name, r, value))
            self.table.setCellWidget(row, 2, slider)

        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._loading = False

    def _on_slider_changed(self, npc_name: str, row: int, value: int) -> None:
        max_points = self.table.cellWidget(row, 2).maximum()
        self.table.item(row, 1).setText(f"{value // POINTS_PER_HEART} / {max_points // POINTS_PER_HEART}")
        if self._loading:
            return
        self.points_changed.emit(npc_name, value)

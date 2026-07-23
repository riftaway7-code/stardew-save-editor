from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QMessageBox, QVBoxLayout, QWidget

from svse.itemdb import ItemDB
from svse.gui.widgets.tile_canvas import TileCanvas
from svse.savemodel import PlacedObjectInfo

LOCATION_TYPE = "Farm"  # v1 scope: Farm only, see project plan phasing


class MapTab(QWidget):
    chest_place_requested = Signal(int, int)

    def __init__(self, item_db: ItemDB, parent: QWidget | None = None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        hint = QLabel(
            "Farm view - click any highlighted free tile to place a new "
            "chest there. Occupied tiles (red highlight) can't be clicked; "
            "this is enforced on write too, so it's never possible to "
            "corrupt a save by placing on top of something."
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.canvas = TileCanvas(item_db)
        self.canvas.tile_clicked.connect(self._on_tile_clicked)
        layout.addWidget(self.canvas)

        self.setEnabled(False)

    def set_placed_objects(self, objects: list[PlacedObjectInfo]) -> None:
        self.canvas.set_placed_objects(objects)

    def _on_tile_clicked(self, x: int, y: int) -> None:
        answer = QMessageBox.question(
            self,
            "Place Chest",
            f"Place a new chest at tile ({x}, {y})?",
        )
        if answer == QMessageBox.Yes:
            self.chest_place_requested.emit(x, y)

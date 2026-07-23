from __future__ import annotations

from PySide6.QtCore import QSize, Signal, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QToolButton

from svse.itemdb import ItemDB
from svse.mapdata.tilesheet import sprite_for_item_id
from svse.savemodel import InventorySlot

_ICON_SIZE = 40
_QUALITY_MARKER = {0: "", 1: "*", 2: "**", 4: "★"}  # gold star for quality 4


class InventorySlotWidget(QToolButton):
    """One cell in the 36-slot backpack grid. Shows the item's real sprite
    icon (see mapdata.tilesheet) with a short quantity/quality caption below
    it, rather than the full name crammed into the button - a 64px button
    couldn't legibly fit "Large Goat Milk\\nx5" in a pixel font, so the icon
    carries the identification and the full name lives in the tooltip.
    QToolButton (not QPushButton) specifically for ToolButtonTextUnderIcon -
    QPushButton only lays icon+text out side by side, too cramped here."""

    clicked_with_index = Signal(int)

    def __init__(self, index: int, item_db: ItemDB, parent=None):
        super().__init__(parent)
        self.index = index
        self._item_db = item_db
        self.setFixedSize(76, 76)
        self.setIconSize(QSize(_ICON_SIZE, _ICON_SIZE))
        self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.setCheckable(False)
        self.setStyleSheet("font-size: 11px;")
        self.clicked.connect(lambda: self.clicked_with_index.emit(self.index))
        self.set_slot(None)

    def set_slot(self, slot: InventorySlot | None) -> None:
        if slot is None:
            self.setIcon(QIcon())
            self.setText("+")
            self.setToolTip("Empty slot - click to add an item")
            return

        bigcraftable = slot.xsi_type not in ("", "Object")
        pixmap = sprite_for_item_id(self._item_db, slot.item_id, bigcraftable=bigcraftable, size=_ICON_SIZE)
        self.setIcon(QIcon(pixmap))

        caption_parts = []
        if slot.stack > 1:
            caption_parts.append(f"x{slot.stack}")
        quality_marker = _QUALITY_MARKER.get(slot.quality, "")
        if quality_marker:
            caption_parts.append(quality_marker)
        self.setText(" ".join(caption_parts))
        self.setToolTip(f"{slot.name} (id {slot.item_id}), qty {slot.stack}, quality {slot.quality}")

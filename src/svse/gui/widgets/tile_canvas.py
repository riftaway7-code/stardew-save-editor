"""Zoomable/scrollable tile grid for the Map/Placement tab.

Scope note (see project plan): this renders a schematic grid with real
per-object sprite art, NOT a pixel-accurate reproduction of the player's
actual farm terrain layout - the save file doesn't store a renderable
terrain image, only tile indices referencing the game's own map assets,
which (per tonight's investigation) aren't reachable from the device. Real
object/item art *is* used (see mapdata/tilesheet.py) - just on a plain grid
background rather than real grass/dirt/water tiles."""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QPainter, QPen
from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsScene, QGraphicsView

from svse.itemdb import ItemDB
from svse.mapdata.tilesheet import sprite_for_item_id
from svse.savemodel import PlacedObjectInfo

TILE_SIZE = 32
_GRASS_COLOR = QColor(86, 138, 75)
_GRID_LINE_COLOR = QColor(70, 110, 60)
_HOVER_FREE_COLOR = QColor(80, 220, 80, 140)
_HOVER_OCCUPIED_COLOR = QColor(220, 60, 60, 140)


class TileCanvas(QGraphicsView):
    tile_clicked = Signal(int, int)  # only ever emitted for a currently-free tile

    def __init__(self, item_db: ItemDB, grid_width: int = 120, grid_height: int = 100, parent=None):
        super().__init__(parent)
        self._item_db = item_db
        self._grid_width = grid_width
        self._grid_height = grid_height
        self._occupied: set[tuple[int, int]] = set()

        self._scene = QGraphicsScene(0, 0, grid_width * TILE_SIZE, grid_height * TILE_SIZE)
        self.setScene(self._scene)
        self.setRenderHint(QPainter.Antialiasing, False)  # crisp pixel-art edges, no smoothing
        self.setMouseTracking(True)
        self.setDragMode(QGraphicsView.ScrollHandDrag)

        self._draw_background()
        self._hover_item: QGraphicsRectItem | None = None

    def _draw_background(self) -> None:
        self._scene.setBackgroundBrush(QBrush(_GRASS_COLOR))
        pen = QPen(_GRID_LINE_COLOR)
        pen.setWidth(0)
        for x in range(self._grid_width + 1):
            self._scene.addLine(x * TILE_SIZE, 0, x * TILE_SIZE, self._grid_height * TILE_SIZE, pen)
        for y in range(self._grid_height + 1):
            self._scene.addLine(0, y * TILE_SIZE, self._grid_width * TILE_SIZE, y * TILE_SIZE, pen)

    def set_placed_objects(self, objects: list[PlacedObjectInfo]) -> None:
        # clear previously-drawn sprite items (keep background lines, which
        # were added first and have no custom data tag)
        for item in list(self._scene.items()):
            if item.data(0) == "sprite":
                self._scene.removeItem(item)

        self._occupied = {(o.x, o.y) for o in objects if 0 <= o.x < self._grid_width and 0 <= o.y < self._grid_height}
        for obj in objects:
            if not (0 <= obj.x < self._grid_width and 0 <= obj.y < self._grid_height):
                continue
            bigcraftable = obj.xsi_type not in ("", "Object")
            pixmap = sprite_for_item_id(self._item_db, obj.item_id, bigcraftable=bigcraftable, size=TILE_SIZE)
            pixmap_item = self._scene.addPixmap(pixmap)
            pixmap_item.setPos(obj.x * TILE_SIZE, obj.y * TILE_SIZE)
            pixmap_item.setData(0, "sprite")
            pixmap_item.setToolTip(f"{obj.name} ({obj.x}, {obj.y})")

    def is_occupied(self, x: int, y: int) -> bool:
        return (x, y) in self._occupied

    def _tile_at(self, view_pos) -> tuple[int, int] | None:
        scene_pos = self.mapToScene(view_pos)
        x, y = int(scene_pos.x() // TILE_SIZE), int(scene_pos.y() // TILE_SIZE)
        if 0 <= x < self._grid_width and 0 <= y < self._grid_height:
            return x, y
        return None

    def mouseMoveEvent(self, event) -> None:
        super().mouseMoveEvent(event)
        tile = self._tile_at(event.pos())
        if self._hover_item is not None:
            self._scene.removeItem(self._hover_item)
            self._hover_item = None
        if tile is None:
            return
        x, y = tile
        color = _HOVER_OCCUPIED_COLOR if self.is_occupied(x, y) else _HOVER_FREE_COLOR
        rect = QRectF(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        self._hover_item = self._scene.addRect(rect, QPen(Qt.NoPen), QBrush(color))
        self._hover_item.setZValue(10)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton and not (event.modifiers() & Qt.AltModifier):
            tile = self._tile_at(event.pos())
            if tile is not None and not self.is_occupied(*tile):
                self.tile_clicked.emit(*tile)
                return
        super().mousePressEvent(event)

    def wheelEvent(self, event) -> None:
        zoom_factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(zoom_factor, zoom_factor)

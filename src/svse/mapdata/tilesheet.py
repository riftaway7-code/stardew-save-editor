"""Loads real per-item sprite art (extracted by tools/build_item_db.py from
community modding-reference data, see data/items_raw/SOURCES.md) as QPixmaps
for the map/placement view and inventory grid. Falls back to a plain colored
square for anything without a sprite - most decorative/terrain objects
(weeds, litter) aren't in the object database and were never expected to
render as real art; only place-able objects/bigcraftables need to."""

from __future__ import annotations

from functools import lru_cache

from PySide6.QtGui import QColor, QPainter, QPixmap

from svse.itemdb import ItemDB

_FALLBACK_COLOR = QColor(120, 120, 120)


@lru_cache(maxsize=1024)
def _load_pixmap(path_str: str) -> QPixmap:
    return QPixmap(path_str)


def _fallback_pixmap(size: int) -> QPixmap:
    pixmap = QPixmap(size, size)
    pixmap.fill(_FALLBACK_COLOR)
    painter = QPainter(pixmap)
    painter.setPen(QColor(60, 60, 60))
    painter.drawRect(0, 0, size - 1, size - 1)
    painter.end()
    return pixmap


def sprite_for_item_id(db: ItemDB, item_id: str, *, bigcraftable: bool = False, size: int = 32) -> QPixmap:
    item = db.get_bigcraftable(item_id) if bigcraftable else db.get(item_id)
    if item is not None:
        path = db.sprite_path(item, bigcraftable=bigcraftable)
        if path is not None:
            pixmap = _load_pixmap(str(path))
            if not pixmap.isNull():
                return pixmap.scaled(size, size)
    return _fallback_pixmap(size)

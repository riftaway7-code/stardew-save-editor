from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from svse.itemdb.models import Item
from svse.paths import data_dir

_DEFAULT_PATH = data_dir() / "items.json"
_SPRITE_ROOT = data_dir() / "tilesheets"


def _parse_table(raw: dict) -> dict[str, Item]:
    return {
        item_id: Item(
            id=entry["id"],
            name=entry["name"],
            object_type=entry["object_type"],
            category=entry["category"],
            price=entry["price"],
            edibility=entry["edibility"],
            has_sprite=entry.get("has_sprite", False),
        )
        for item_id, entry in raw.items()
    }


class ItemDB:
    def __init__(self, items: dict[str, Item], bigcraftables: dict[str, Item] | None = None):
        self._items = items
        self._bigcraftables = bigcraftables or {}

    def __len__(self) -> int:
        return len(self._items)

    def __contains__(self, item_id: str) -> bool:
        return item_id in self._items

    def get(self, item_id: str) -> Item | None:
        return self._items.get(item_id)

    def all(self) -> list[Item]:
        return list(self._items.values())

    def get_bigcraftable(self, item_id: str) -> Item | None:
        return self._bigcraftables.get(item_id)

    @staticmethod
    def sprite_path(item: Item, *, bigcraftable: bool = False) -> Path | None:
        if not item.has_sprite:
            return None
        subdir = "bigcraftables" if bigcraftable else "objects"
        path = _SPRITE_ROOT / subdir / f"{item.id}.png"
        return path if path.exists() else None


def load_items(path: Path | None = None) -> ItemDB:
    path = path or _DEFAULT_PATH
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    items = _parse_table(data["items"])
    bigcraftables = _parse_table(data.get("bigcraftables", {}))
    return ItemDB(items, bigcraftables)


@lru_cache(maxsize=1)
def default_db() -> ItemDB:
    """Cached singleton for GUI use - the item DB is loaded once per process."""
    return load_items()

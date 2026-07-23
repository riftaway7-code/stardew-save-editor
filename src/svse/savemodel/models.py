from __future__ import annotations

from dataclasses import dataclass


@dataclass
class InventorySlot:
    index: int
    item_id: str
    name: str
    category: int
    price: int
    edibility: int
    stack: int
    quality: int
    xsi_type: str
    """The item's xsi:type attribute (e.g. "Object", "MeleeWeapon", "Hoe").
    Only "Object" items are Data/Objects entries resolvable in the item db -
    tools/weapons/rings live in entirely different id namespaces and can
    share numeric ids with unrelated objects, so never assume a numeric
    item_id alone means it's an Object."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Item:
    id: str
    name: str
    object_type: str
    category: int
    price: int
    edibility: int
    has_sprite: bool = False

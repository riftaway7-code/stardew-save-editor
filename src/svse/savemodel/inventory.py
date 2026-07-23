"""Player backpack (36 fixed slots) read/write.

The <Item xsi:type="Object"> field layout below was captured verbatim from
real save data (hand-verified field-by-field against several live in-game
items) - see project plan. Do not add/remove/reorder fields without
re-checking against a real save; the game's deserializer is tolerant of
some things but this exact shape is known-good.
"""

from __future__ import annotations

from lxml import etree

from svse.savemodel.constants import BACKPACK_SLOT_COUNT, XSI_NIL, XSI_TYPE
from svse.savemodel.errors import InventoryFullError, SlotIndexError
from svse.savemodel.models import InventorySlot
from svse.savemodel.object_xml import make_nil_item, make_object_item
from svse.savemodel.save_file import SaveFile

_ITEMS_PATH = "./player/items"


def _items_element(main: SaveFile) -> etree._Element:
    items_el = main.find(_ITEMS_PATH)
    if items_el is None:
        raise SlotIndexError("Save file has no <player><items> element")
    return items_el


def _is_nil(item_el: etree._Element) -> bool:
    return item_el.get(XSI_NIL) == "true"


def get_slots(main: SaveFile) -> list[InventorySlot | None]:
    """Return all 36 backpack slots in order; None for empty slots.

    Not every slot is our own xsi:type="Object" schema - tools, weapons,
    rings etc (xsi:type="MeleeWeapon"/"Hoe"/"FishingRod"/...) use entirely
    different field sets (e.g. a weapon has minDamage/maxDamage, no
    price/edibility at all). We only fully model plain Objects (what
    add_item/set_slot create); everything else is reported with best-effort
    fields defaulted to 0/blank so occupancy checks and display never crash
    on a real, heterogeneous inventory."""
    items_el = _items_element(main)
    children = list(items_el)
    slots: list[InventorySlot | None] = []
    for index, child in enumerate(children):
        if _is_nil(child):
            slots.append(None)
            continue
        slots.append(
            InventorySlot(
                index=index,
                item_id=_text(child, "itemId"),
                name=_text(child, "name"),
                category=_int(child, "category"),
                price=_int(child, "price"),
                edibility=_int(child, "edibility"),
                stack=_int(child, "stack", default=1),
                quality=_int(child, "quality"),
                xsi_type=child.get(XSI_TYPE, ""),
            )
        )
    return slots


def _text(item_el: etree._Element, tag: str) -> str:
    child = item_el.find(tag)
    return child.text if child is not None and child.text is not None else ""


def _int(item_el: etree._Element, tag: str, default: int = 0) -> int:
    raw = _text(item_el, tag)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def find_free_slots(main: SaveFile) -> list[int]:
    return [i for i, slot in enumerate(get_slots(main)) if slot is None]


def set_slot(
    main: SaveFile,
    index: int,
    *,
    item_id: str,
    name: str,
    category: int,
    price: int,
    edibility: int,
    stack: int = 1,
    quality: int = 0,
) -> None:
    """Write (or overwrite) one specific slot by index. Never changes the
    total slot count - existing entries at other indices are untouched."""
    items_el = _items_element(main)
    children = list(items_el)
    if not (0 <= index < len(children)):
        raise SlotIndexError(f"Slot index {index} out of range (0-{len(children) - 1})")
    new_el = make_object_item(item_id, name, category, price, edibility, stack, quality)
    items_el.replace(children[index], new_el)


def clear_slot(main: SaveFile, index: int) -> None:
    items_el = _items_element(main)
    children = list(items_el)
    if not (0 <= index < len(children)):
        raise SlotIndexError(f"Slot index {index} out of range (0-{len(children) - 1})")
    items_el.replace(children[index], make_nil_item())


def add_item(
    main: SaveFile,
    *,
    item_id: str,
    name: str,
    category: int,
    price: int,
    edibility: int,
    stack: int = 1,
    quality: int = 0,
) -> int:
    """Place an item into the first free backpack slot. Raises
    InventoryFullError if all BACKPACK_SLOT_COUNT slots are occupied - the
    caller (GUI) should catch this and offer chest placement instead.
    Returns the slot index used."""
    free = find_free_slots(main)
    if not free:
        raise InventoryFullError(
            f"All {BACKPACK_SLOT_COUNT} backpack slots are full. "
            "Place this item in a chest instead."
        )
    index = free[0]
    set_slot(
        main,
        index,
        item_id=item_id,
        name=name,
        category=category,
        price=price,
        edibility=edibility,
        stack=stack,
        quality=quality,
    )
    return index

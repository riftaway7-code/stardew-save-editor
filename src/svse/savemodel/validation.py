"""Last line of defense before any bytes leave this machine for the device.
Every push in the GUI must run all of these first (see safety.snapshots for
the other half of the safety net: a local backup taken before the write)."""

from __future__ import annotations

from lxml import etree

from svse.savemodel.constants import BACKPACK_SLOT_COUNT
from svse.savemodel.money import get_money
from svse.savemodel.save_file import SaveFile


class ValidationError(Exception):
    """Raised when a save fails a safety check - the push must not proceed."""


def validate_xml_wellformed(raw: bytes) -> None:
    try:
        SaveFile.loads(raw)
    except Exception as exc:
        raise ValidationError(f"Produced XML is not well-formed: {exc}") from exc


def validate_inventory_slot_count(main: SaveFile) -> None:
    items_el = main.find("./player/items")
    if items_el is None:
        raise ValidationError("Save file has no <player><items> element")
    count = len(list(items_el))
    if count != BACKPACK_SLOT_COUNT:
        raise ValidationError(
            f"Backpack has {count} slots, expected exactly {BACKPACK_SLOT_COUNT} "
            "(the mobile UI silently ignores anything past slot 36 - see "
            "project plan for how this was discovered)"
        )


_XSI_TYPE_ATTR = "{http://www.w3.org/2001/XMLSchema-instance}type"


def validate_no_duplicate_tiles(main: SaveFile, location_type: str) -> None:
    location = main.find(f"./locations/GameLocation[@{_XSI_TYPE_ATTR}='{location_type}']")
    if location is None:
        return
    objects_el = location.find("./objects")
    if objects_el is None:
        return
    seen: set[tuple[str, str]] = set()
    for item_el in objects_el.findall("./item"):
        vector = item_el.find("./key/Vector2")
        if vector is None:
            continue
        x = vector.find("X").text
        y = vector.find("Y").text
        key = (x, y)
        if key in seen:
            raise ValidationError(
                f"Duplicate object at tile ({x}, {y}) in {location_type} - "
                "this would corrupt the save (see project plan for the "
                "incident this check exists because of)"
            )
        seen.add(key)


def validate_money_sync(main: SaveFile, info: SaveFile) -> None:
    main_money = get_money(main)
    info_el = info.find("./money")
    if info_el is None or info_el.text is None:
        raise ValidationError("SaveGameInfo has no <money> element")
    info_money = int(info_el.text)
    if main_money != info_money:
        raise ValidationError(
            f"Money out of sync: main save has {main_money}, SaveGameInfo has {info_money}"
        )


def validate_before_push(main: SaveFile, info: SaveFile) -> None:
    """Run the full validation suite. Raises ValidationError on the first
    failure; callers should show this to the user and refuse to push."""
    validate_xml_wellformed(main.dumps())
    validate_xml_wellformed(info.dumps())
    validate_inventory_slot_count(main)
    validate_money_sync(main, info)
    for location_type in ("Farm", "FarmHouse"):
        validate_no_duplicate_tiles(main, location_type)

"""Placing objects (chests, machines, etc.) into a world location's
<objects> tile dictionary.

CRITICAL - see project plan: placing an object at a tile that's already
occupied creates a duplicate dictionary key, which corrupts the save and
makes the game silently fall back to an older auto-backup on load (a real
incident from live testing). place_object() below is the single,
centralized enforcement point for this - it always re-checks occupancy at
write time, never trusting a caller's earlier (possibly stale) read."""

from __future__ import annotations

from dataclasses import dataclass

from lxml import etree

from svse.savemodel.errors import TileOccupiedError
from svse.savemodel.save_file import SaveFile

_XSI_TYPE_ATTR = "{http://www.w3.org/2001/XMLSchema-instance}type"


@dataclass
class PlacedObjectInfo:
    x: int
    y: int
    item_id: str
    name: str
    xsi_type: str


def _location_element(main: SaveFile, location_type: str) -> etree._Element | None:
    return main.find(f"./locations/GameLocation[@{_XSI_TYPE_ATTR}='{location_type}']")


def _objects_element(main: SaveFile, location_type: str) -> etree._Element:
    location = _location_element(main, location_type)
    if location is None:
        raise ValueError(f"No GameLocation of type {location_type!r} in this save")
    objects_el = location.find("./objects")
    if objects_el is None:
        raise ValueError(f"{location_type} has no <objects> element")
    return objects_el


def list_occupied_tiles(main: SaveFile, location_type: str) -> set[tuple[int, int]]:
    """All currently-used (X, Y) tile coordinates in a location's objects
    dict. Used both for GUI rendering (which tiles to grey out) and, more
    importantly, re-checked independently inside place_object() at write
    time - a stale UI read can never corrupt a save through this function."""
    objects_el = _objects_element(main, location_type)
    occupied: set[tuple[int, int]] = set()
    for item in objects_el.findall("./item"):
        vector = item.find("./key/Vector2")
        if vector is None:
            continue
        x_el, y_el = vector.find("X"), vector.find("Y")
        if x_el is None or y_el is None:
            continue
        occupied.add((int(x_el.text), int(y_el.text)))
    return occupied


def get_placed_objects(main: SaveFile, location_type: str) -> list[PlacedObjectInfo]:
    """Like list_occupied_tiles, but also returns each object's id/name/type
    for rendering (e.g. picking the right sprite icon in the map view)."""
    objects_el = _objects_element(main, location_type)
    result: list[PlacedObjectInfo] = []
    for item in objects_el.findall("./item"):
        vector = item.find("./key/Vector2")
        if vector is None:
            continue
        x_el, y_el = vector.find("X"), vector.find("Y")
        if x_el is None or y_el is None:
            continue
        value = item.find("./value")
        if value is None or len(value) == 0:
            continue
        obj_el = value[0]
        item_id_el = obj_el.find("./itemId")
        name_el = obj_el.find("./name")
        result.append(
            PlacedObjectInfo(
                x=int(x_el.text),
                y=int(y_el.text),
                item_id=item_id_el.text if item_id_el is not None and item_id_el.text else "",
                name=name_el.text if name_el is not None and name_el.text else "",
                xsi_type=obj_el.get(_XSI_TYPE_ATTR, ""),
            )
        )
    return result


def place_object(main: SaveFile, location_type: str, x: int, y: int, object_element: etree._Element) -> None:
    """Insert `object_element` (a fully-built <Object ...> element, e.g.
    from chest.build_chest_element) at tile (x, y) in the given location.
    Raises TileOccupiedError - and writes nothing - if that tile is already
    occupied, regardless of what the caller believes from an earlier read."""
    objects_el = _objects_element(main, location_type)
    if (x, y) in list_occupied_tiles(main, location_type):
        raise TileOccupiedError(
            f"Tile ({x}, {y}) in {location_type} is already occupied - "
            "placing here would create a duplicate dictionary key and "
            "corrupt the save."
        )

    item = etree.SubElement(objects_el, "item")
    key = etree.SubElement(item, "key")
    vector = etree.SubElement(key, "Vector2")
    etree.SubElement(vector, "X").text = str(x)
    etree.SubElement(vector, "Y").text = str(y)
    value = etree.SubElement(item, "value")
    value.append(object_element)


def remove_object(main: SaveFile, location_type: str, x: int, y: int) -> bool:
    """Remove whatever's at (x, y), if anything. Returns True if something
    was removed, False if the tile was already empty."""
    objects_el = _objects_element(main, location_type)
    for item in objects_el.findall("./item"):
        vector = item.find("./key/Vector2")
        if vector is None:
            continue
        x_el, y_el = vector.find("X"), vector.find("Y")
        if x_el is not None and y_el is not None and int(x_el.text) == x and int(y_el.text) == y:
            objects_el.remove(item)
            return True
    return False

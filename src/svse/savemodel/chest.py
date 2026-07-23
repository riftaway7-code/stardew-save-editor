"""Chest objects: build a new Chest <Object> element for placement.py, and
read/write its own (uncapped, unlike the player backpack) items list.

Schema captured from a real save's existing chest:
    <Object xsi:type="Chest">...<items><Item xsi:type="Object">...</Item>
    ...<Item xsi:nil="true" />...</items>...<playerChest>true</playerChest>
    <fridge>false</fridge>...</Object>
Unlike the player backpack, a chest's <items> list has no fixed slot count
or padding requirement - it's just as many <Item> entries as it holds."""

from __future__ import annotations

from lxml import etree

from svse.savemodel.constants import XSI_NIL, XSI_TYPE
from svse.savemodel.models import InventorySlot
from svse.savemodel.object_xml import make_object_item
from svse.savemodel.save_file import SaveFile

# Sprite-sheet frame for a plain (non-colored) chest, and its tile pixel
# offset math - taken verbatim from a real placed chest, so a freshly built
# one renders identically to a player-placed one.
_CHEST_ITEM_ID = "130"


def build_chest_element(tile_x: int, tile_y: int) -> etree._Element:
    el = etree.Element("Object")
    el.set(XSI_TYPE, "Chest")

    def sub(parent: etree._Element, tag: str, text: str) -> etree._Element:
        child = etree.SubElement(parent, tag)
        child.text = text
        return child

    sub(el, "isLostItem", "false")
    sub(el, "category", "-9")
    sub(el, "hasBeenInInventory", "false")
    sub(el, "name", "Chest")
    sub(el, "parentSheetIndex", _CHEST_ITEM_ID)
    sub(el, "itemId", _CHEST_ITEM_ID)
    sub(el, "specialItem", "false")
    sub(el, "isRecipe", "false")
    sub(el, "quality", "0")
    sub(el, "stack", "1")
    sub(el, "SpecialVariable", "0")

    tile = etree.SubElement(el, "tileLocation")
    etree.SubElement(tile, "X").text = str(tile_x)
    etree.SubElement(tile, "Y").text = str(tile_y)

    sub(el, "owner", "0")
    sub(el, "type", "Crafting")
    sub(el, "canBeSetDown", "true")
    sub(el, "canBeGrabbed", "true")
    sub(el, "isSpawnedObject", "false")
    sub(el, "questItem", "false")
    sub(el, "isOn", "true")
    sub(el, "fragility", "0")
    sub(el, "price", "0")
    sub(el, "edibility", "-300")
    sub(el, "bigCraftable", "true")
    sub(el, "setOutdoors", "true")
    sub(el, "setIndoors", "true")
    sub(el, "readyForHarvest", "false")
    sub(el, "showNextIndex", "false")
    sub(el, "flipped", "false")
    sub(el, "isLamp", "false")
    sub(el, "minutesUntilReady", "0")

    box = etree.SubElement(el, "boundingBox")
    etree.SubElement(box, "X").text = str(tile_x * 64)
    etree.SubElement(box, "Y").text = str(tile_y * 64)
    etree.SubElement(box, "Width").text = "64"
    etree.SubElement(box, "Height").text = "64"
    loc = etree.SubElement(box, "Location")
    etree.SubElement(loc, "X").text = str(tile_x * 64)
    etree.SubElement(loc, "Y").text = str(tile_y * 64)
    size = etree.SubElement(box, "Size")
    etree.SubElement(size, "X").text = "64"
    etree.SubElement(size, "Y").text = "64"

    scale = etree.SubElement(el, "scale")
    etree.SubElement(scale, "X").text = "0"
    etree.SubElement(scale, "Y").text = "0"

    sub(el, "uses", "0")
    sub(el, "destroyOvernight", "false")
    sub(el, "currentLidFrame", "131")
    lid_frame_count = etree.SubElement(el, "lidFrameCount")
    etree.SubElement(lid_frame_count, "int").text = "5"
    sub(el, "frameCounter", "-1")

    etree.SubElement(el, "items")  # starts empty

    wallet = etree.SubElement(el, "separateWalletItems")
    etree.SubElement(wallet, "SerializableDictionaryOfInt64Inventory")

    for tag, color in (("tint", (255, 255, 255, 255)), ("playerChoiceColor", (0, 0, 0, 255))):
        c = etree.SubElement(el, tag)
        etree.SubElement(c, "B").text = str(color[2])
        etree.SubElement(c, "G").text = str(color[1])
        etree.SubElement(c, "R").text = str(color[0])
        etree.SubElement(c, "A").text = str(color[3])
        packed = color[0] | (color[1] << 8) | (color[2] << 16) | (color[3] << 24)
        etree.SubElement(c, "PackedValue").text = str(packed)

    sub(el, "playerChest", "true")
    sub(el, "fridge", "false")
    sub(el, "giftbox", "false")
    sub(el, "giftboxIndex", "0")
    giftbox_starter = etree.SubElement(el, "giftboxIsStarterGift")
    etree.SubElement(giftbox_starter, "boolean").text = "false"
    sub(el, "spriteIndexOverride", "-1")
    sub(el, "dropContents", "false")
    sub(el, "synchronized", "false")
    sub(el, "specialChestType", "None")
    global_inv = etree.SubElement(el, "globalInventoryId")
    string_el = etree.SubElement(global_inv, "string")
    string_el.set(XSI_NIL, "true")

    return el


def get_chest_element(main: SaveFile, location_type: str, x: int, y: int) -> etree._Element | None:
    from svse.savemodel.placement import _objects_element  # local import avoids a cycle at module load time

    objects_el = _objects_element(main, location_type)
    for item in objects_el.findall("./item"):
        vector = item.find("./key/Vector2")
        if vector is None:
            continue
        x_el, y_el = vector.find("X"), vector.find("Y")
        if x_el is not None and y_el is not None and int(x_el.text) == x and int(y_el.text) == y:
            value = item.find("./value")
            return value[0] if len(value) else None
    return None


def get_chest_items(chest_element: etree._Element) -> list[InventorySlot]:
    items_el = chest_element.find("./items")
    if items_el is None:
        return []
    slots: list[InventorySlot] = []
    for index, child in enumerate(items_el):
        if child.get(XSI_NIL) == "true":
            continue

        def text(tag: str) -> str:
            el = child.find(tag)
            return el.text if el is not None and el.text is not None else ""

        def as_int(tag: str, default: int = 0) -> int:
            raw = text(tag)
            try:
                return int(raw) if raw else default
            except ValueError:
                return default

        slots.append(
            InventorySlot(
                index=index,
                item_id=text("itemId"),
                name=text("name"),
                category=as_int("category"),
                price=as_int("price"),
                edibility=as_int("edibility"),
                stack=as_int("stack", default=1),
                quality=as_int("quality"),
                xsi_type=child.get(XSI_TYPE, ""),
            )
        )
    return slots


def add_item_to_chest(
    chest_element: etree._Element,
    *,
    item_id: str,
    name: str,
    category: int = 0,
    price: int = 0,
    edibility: int = -300,
    stack: int = 1,
    quality: int = 0,
) -> None:
    """Chests aren't capped at 36 like the player backpack - always appends,
    never raises InventoryFullError."""
    items_el = chest_element.find("./items")
    if items_el is None:
        items_el = etree.SubElement(chest_element, "items")
    items_el.append(make_object_item(item_id, name, category, price, edibility, stack, quality))

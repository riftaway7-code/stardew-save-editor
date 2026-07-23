"""Shared <Item xsi:type="Object"> XML builder, used by both the player
backpack (inventory.py) and chest contents (chest.py) so the two never drift
apart. Field layout captured verbatim from real save data - see project plan.
Do not add/remove/reorder fields without re-checking against a real save."""

from __future__ import annotations

from lxml import etree

from svse.savemodel.constants import XSI_NIL, XSI_TYPE


def make_nil_item() -> etree._Element:
    el = etree.Element("Item")
    el.set(XSI_NIL, "true")
    return el


def make_object_item(
    item_id: str, name: str, category: int, price: int, edibility: int, stack: int, quality: int
) -> etree._Element:
    el = etree.Element("Item")
    el.set(XSI_TYPE, "Object")

    def sub(tag: str, text: str) -> None:
        child = etree.SubElement(el, tag)
        child.text = text

    sub("isLostItem", "false")
    sub("category", str(category))
    sub("hasBeenInInventory", "true")
    sub("name", name)
    sub("parentSheetIndex", item_id)
    sub("itemId", item_id)
    sub("specialItem", "false")
    sub("isRecipe", "false")
    sub("quality", str(quality))
    sub("stack", str(stack))
    sub("SpecialVariable", "0")

    tile = etree.SubElement(el, "tileLocation")
    etree.SubElement(tile, "X").text = "0"
    etree.SubElement(tile, "Y").text = "0"

    sub("owner", "0")
    sub("type", "Basic")
    sub("canBeSetDown", "true")
    sub("canBeGrabbed", "true")
    sub("isSpawnedObject", "false")
    sub("questItem", "false")
    sub("isOn", "true")
    sub("fragility", "0")
    sub("price", str(price))
    sub("edibility", str(edibility))
    sub("bigCraftable", "false")
    sub("setOutdoors", "false")
    sub("setIndoors", "false")
    sub("readyForHarvest", "false")
    sub("showNextIndex", "false")
    sub("flipped", "false")
    sub("isLamp", "false")
    sub("minutesUntilReady", "0")

    box = etree.SubElement(el, "boundingBox")
    etree.SubElement(box, "X").text = "0"
    etree.SubElement(box, "Y").text = "0"
    etree.SubElement(box, "Width").text = "0"
    etree.SubElement(box, "Height").text = "0"
    loc = etree.SubElement(box, "Location")
    etree.SubElement(loc, "X").text = "0"
    etree.SubElement(loc, "Y").text = "0"
    size = etree.SubElement(box, "Size")
    etree.SubElement(size, "X").text = "0"
    etree.SubElement(size, "Y").text = "0"

    scale = etree.SubElement(el, "scale")
    etree.SubElement(scale, "X").text = "0"
    etree.SubElement(scale, "Y").text = "0"

    sub("uses", "0")
    sub("destroyOvernight", "false")
    return el

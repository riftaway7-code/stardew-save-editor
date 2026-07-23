"""View-model tying together device I/O, save parsing, and the safety net.
The GUI only ever talks to a Session - it never touches svse.device or
svse.savemodel directly, per the plan's layering principle."""

from __future__ import annotations

from dataclasses import dataclass, field

from svse import device as device_layer
from svse import safety
from svse.savemodel import (
    FriendshipInfo,
    InventorySlot,
    PlacedObjectInfo,
    SaveFile,
    add_item,
    build_chest_element,
    get_friendships,
    get_money,
    get_placed_objects,
    get_slots,
    place_object,
    set_money,
    set_points,
)
from svse.savemodel.errors import InventoryFullError
from svse.savemodel.validation import ValidationError, validate_before_push


@dataclass(repr=False)
class Session:
    """repr=False: the default dataclass repr would include _pulled_raw,
    which holds multi-megabyte raw save file bytes - its repr() blew up a
    debug log to 6MB+ during testing. Custom __repr__ below stays small."""

    udid: str | None = None
    folder_name: str | None = None
    main: SaveFile | None = None
    info: SaveFile | None = None
    dirty: bool = False
    _pulled_raw: dict[str, bytes] = field(default_factory=dict)

    def __repr__(self) -> str:
        return (
            f"Session(udid={self.udid!r}, folder_name={self.folder_name!r}, "
            f"loaded={self.loaded}, dirty={self.dirty})"
        )

    @property
    def loaded(self) -> bool:
        return self.main is not None and self.info is not None

    def pull(self, udid: str, folder_name: str) -> None:
        pulled = device_layer.pull_save(udid, folder_name)
        self.udid = udid
        self.folder_name = folder_name
        self._pulled_raw = pulled
        self.main = SaveFile.loads(pulled[folder_name])
        self.info = SaveFile.loads(pulled["SaveGameInfo"])
        self.dirty = False

    # -- Money --------------------------------------------------------
    def get_money(self) -> int:
        return get_money(self.main)

    def set_money(self, value: int) -> None:
        set_money(self.main, self.info, value)
        self.dirty = True

    # -- Inventory ------------------------------------------------------
    def get_slots(self) -> list[InventorySlot | None]:
        return get_slots(self.main)

    def add_item(self, *, item_id: str, name: str, stack: int = 1, quality: int = 0) -> int:
        """Raises InventoryFullError if the backpack is full - the caller
        (inventory tab) should catch this and offer chest placement (once
        the placement module exists) instead."""
        index = add_item(
            self.main,
            item_id=item_id,
            name=name,
            category=0,
            price=0,
            edibility=-300,
            stack=stack,
            quality=quality,
        )
        self.dirty = True
        return index

    # -- Relationships ----------------------------------------------------
    def get_friendships(self) -> dict[str, FriendshipInfo]:
        return get_friendships(self.main)

    def set_friendship_points(self, npc_name: str, points: int) -> None:
        set_points(self.main, npc_name, points)
        self.dirty = True

    # -- Map / Placement --------------------------------------------------
    def get_placed_objects(self, location_type: str) -> list[PlacedObjectInfo]:
        return get_placed_objects(self.main, location_type)

    def place_chest(self, location_type: str, x: int, y: int) -> None:
        """Raises TileOccupiedError (without writing anything) if the tile
        is already occupied - place_object() re-checks independently of
        whatever the caller's UI state believed."""
        chest = build_chest_element(x, y)
        place_object(self.main, location_type, x, y, chest)
        self.dirty = True

    # -- Push -----------------------------------------------------------
    def push(self) -> None:
        """Snapshot the pre-edit state, validate the edited state, then
        write to the device. Raises ValidationError without touching the
        device if validation fails."""
        if not self.loaded or self.udid is None or self.folder_name is None:
            raise RuntimeError("No save loaded")

        safety.take_snapshot(self.folder_name, self._pulled_raw)
        validate_before_push(self.main, self.info)

        files = {
            self.folder_name: self.main.dumps(),
            "SaveGameInfo": self.info.dumps(),
        }
        device_layer.push_save(self.udid, self.folder_name, files)
        self._pulled_raw = files
        self.dirty = False

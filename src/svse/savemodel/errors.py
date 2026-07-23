class SaveModelError(Exception):
    """Base class for all savemodel-layer errors."""


class InventoryFullError(SaveModelError):
    """All 36 backpack slots are occupied - see constants.BACKPACK_SLOT_COUNT.

    Callers (the GUI) should catch this and offer placing the item in a
    chest instead, via svse.savemodel.chest / svse.savemodel.placement.
    """


class TileOccupiedError(SaveModelError):
    """The target (x, y) tile in a GameLocation's <objects> dict is already
    occupied - placing here would create a duplicate dictionary key and
    corrupt the save (verified failure mode from live testing)."""


class SlotIndexError(SaveModelError):
    """Slot index out of range for the 36-slot backpack."""

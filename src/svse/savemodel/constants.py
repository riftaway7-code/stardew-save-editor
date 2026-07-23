XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
XSI_TYPE = f"{{{XSI_NS}}}type"
XSI_NIL = f"{{{XSI_NS}}}nil"

# Verified tonight against a live device: the mobile backpack UI is
# hard-capped at 36 slots regardless of the <maxItems> field's value - items
# appended past slot 36 are written to disk but invisible/inaccessible
# in-game. Never rely on <maxItems> to expand real usable capacity.
BACKPACK_SLOT_COUNT = 36

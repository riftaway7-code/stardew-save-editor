from pathlib import Path

import pytest

from svse.savemodel import InventoryFullError, SaveFile, add_item, clear_slot, find_free_slots, get_slots
from svse.savemodel.constants import BACKPACK_SLOT_COUNT

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "sample_save"

_requires_fixture = pytest.mark.skipif(
    not (FIXTURE_DIR / "PayaBean_441519152").exists(),
    reason="Real save fixture not present locally (gitignored)",
)


def _load_main() -> SaveFile:
    return SaveFile.load(FIXTURE_DIR / "PayaBean_441519152")


@_requires_fixture
def test_get_slots_returns_exactly_36():
    main = _load_main()
    slots = get_slots(main)
    assert len(slots) == BACKPACK_SLOT_COUNT


@_requires_fixture
def test_add_item_uses_a_free_slot_and_is_readable_back():
    main = _load_main()
    free_before = find_free_slots(main)
    assert free_before, "fixture save has no free slots to test with"

    index = add_item(
        main,
        item_id="272",
        name="Eggplant",
        category=-75,
        price=20,
        edibility=50,
        stack=1,
        quality=0,
    )

    assert index == free_before[0]
    slots = get_slots(main)
    assert slots[index] is not None
    assert slots[index].name == "Eggplant"
    assert slots[index].item_id == "272"


@_requires_fixture
def test_add_item_raises_when_backpack_is_full():
    main = _load_main()
    free = find_free_slots(main)
    # fill every free slot so the backpack is completely full
    for _ in range(len(free)):
        add_item(main, item_id="390", name="Stone", category=-16, price=2, edibility=-300)

    assert find_free_slots(main) == []
    with pytest.raises(InventoryFullError):
        add_item(main, item_id="390", name="Stone", category=-16, price=2, edibility=-300)


@_requires_fixture
def test_clear_slot_makes_it_free_again():
    main = _load_main()
    free_before = find_free_slots(main)
    index = add_item(main, item_id="272", name="Eggplant", category=-75, price=20, edibility=50)
    assert index not in find_free_slots(main)

    clear_slot(main, index)

    assert index in find_free_slots(main)

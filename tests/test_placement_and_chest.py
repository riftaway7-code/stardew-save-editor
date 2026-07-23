from pathlib import Path

import pytest

from svse.savemodel import (
    SaveFile,
    TileOccupiedError,
    add_item_to_chest,
    build_chest_element,
    get_chest_element,
    get_chest_items,
    list_occupied_tiles,
    place_object,
    remove_object,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "sample_save"

_requires_fixture = pytest.mark.skipif(
    not (FIXTURE_DIR / "PayaBean_441519152").exists(),
    reason="Real save fixture not present locally (gitignored)",
)


def _load_main() -> SaveFile:
    return SaveFile.load(FIXTURE_DIR / "PayaBean_441519152")


def _find_free_tile(main: SaveFile, location_type: str = "Farm") -> tuple[int, int]:
    occupied = list_occupied_tiles(main, location_type)
    for x in range(500, 600):
        if (x, 500) not in occupied:
            return (x, 500)
    raise RuntimeError("no free tile found in test range")


@_requires_fixture
def test_list_occupied_tiles_returns_real_farm_objects():
    main = _load_main()
    occupied = list_occupied_tiles(main, "Farm")
    assert len(occupied) > 0


@_requires_fixture
def test_place_chest_on_free_tile_succeeds_and_is_listed():
    main = _load_main()
    x, y = _find_free_tile(main)
    chest = build_chest_element(x, y)
    place_object(main, "Farm", x, y, chest)

    assert (x, y) in list_occupied_tiles(main, "Farm")


@_requires_fixture
def test_place_object_on_occupied_tile_raises_and_does_not_write():
    main = _load_main()
    occupied = list_occupied_tiles(main, "Farm")
    x, y = next(iter(occupied))
    before_count = len(list_occupied_tiles(main, "Farm"))

    chest = build_chest_element(x, y)
    with pytest.raises(TileOccupiedError):
        place_object(main, "Farm", x, y, chest)

    # must not have written anything on failure
    assert len(list_occupied_tiles(main, "Farm")) == before_count


@_requires_fixture
def test_placed_chest_survives_dump_and_reload():
    main = _load_main()
    x, y = _find_free_tile(main)
    chest = build_chest_element(x, y)
    place_object(main, "Farm", x, y, chest)

    reloaded = SaveFile.loads(main.dumps())
    assert (x, y) in list_occupied_tiles(reloaded, "Farm")
    chest_el = get_chest_element(reloaded, "Farm", x, y)
    assert chest_el is not None
    assert chest_el.get("{http://www.w3.org/2001/XMLSchema-instance}type") == "Chest"


@_requires_fixture
def test_add_items_to_chest_not_capped_at_36():
    main = _load_main()
    x, y = _find_free_tile(main)
    chest = build_chest_element(x, y)
    place_object(main, "Farm", x, y, chest)

    chest_el = get_chest_element(main, "Farm", x, y)
    for i in range(50):  # well beyond the 36-slot backpack cap
        add_item_to_chest(chest_el, item_id="390", name="Stone", stack=1)

    items = get_chest_items(chest_el)
    assert len(items) == 50


@_requires_fixture
def test_chest_items_survive_dump_and_reload():
    main = _load_main()
    x, y = _find_free_tile(main)
    chest = build_chest_element(x, y)
    place_object(main, "Farm", x, y, chest)
    chest_el = get_chest_element(main, "Farm", x, y)
    add_item_to_chest(chest_el, item_id="272", name="Eggplant", stack=3, quality=4)

    reloaded = SaveFile.loads(main.dumps())
    chest_el2 = get_chest_element(reloaded, "Farm", x, y)
    items = get_chest_items(chest_el2)
    assert len(items) == 1
    assert items[0].name == "Eggplant"
    assert items[0].stack == 3
    assert items[0].quality == 4


@_requires_fixture
def test_remove_object_clears_tile():
    main = _load_main()
    x, y = _find_free_tile(main)
    chest = build_chest_element(x, y)
    place_object(main, "Farm", x, y, chest)
    assert (x, y) in list_occupied_tiles(main, "Farm")

    removed = remove_object(main, "Farm", x, y)
    assert removed is True
    assert (x, y) not in list_occupied_tiles(main, "Farm")


@_requires_fixture
def test_remove_object_on_empty_tile_returns_false():
    main = _load_main()
    x, y = _find_free_tile(main)
    assert remove_object(main, "Farm", x, y) is False

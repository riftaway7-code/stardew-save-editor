from pathlib import Path

import pytest

from svse.itemdb import load_items, search

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "sample_save"


def test_loads_without_error_and_has_items():
    db = load_items()
    assert len(db) > 500


def test_no_duplicate_ids_in_source_json():
    import json

    with open(Path(__file__).parent.parent / "data" / "items.json", encoding="utf-8") as f:
        data = json.load(f)
    ids = list(data["items"].keys())
    assert len(ids) == len(set(ids))


def test_known_verified_ids_resolve_correctly():
    # Cross-checked manually against the wiki earlier - these must never
    # silently drift if the source data is rebuilt.
    db = load_items()
    expected = {
        "272": "Eggplant",
        "701": "Tilapia",
        "140": "Walleye",
        "24": "Parsnip",
        "394": "Rainbow Shell",
    }
    for item_id, name in expected.items():
        item = db.get(item_id)
        assert item is not None, f"item id {item_id} missing from db"
        assert item.name == name


def test_search_finds_exact_and_partial_matches():
    db = load_items()
    results = search(db, "parsnip")
    assert any(i.name == "Parsnip" for i in results)

    # partial/substring match
    results = search(db, "egg")
    assert any("egg" in i.name.lower() for i in results)


def test_empty_query_returns_items_without_crashing():
    db = load_items()
    results = search(db, "")
    assert len(results) > 0


def test_sprite_paths_exist_for_items_marked_has_sprite():
    db = load_items()
    checked = 0
    for item in db.all():
        if not item.has_sprite:
            continue
        checked += 1
        path = db.sprite_path(item)
        assert path is not None and path.exists(), f"missing sprite file for {item.id} ({item.name})"
    assert checked > 500  # most objects should have sprites


def test_known_bigcraftable_chest_resolves_with_sprite():
    db = load_items()
    chest = db.get_bigcraftable("130")
    assert chest is not None
    assert chest.name == "Chest"
    path = db.sprite_path(chest, bigcraftable=True)
    assert path is not None and path.exists()


@pytest.mark.skipif(
    not (FIXTURE_DIR / "PayaBean_441519152").exists(),
    reason="Real save fixture not present locally (gitignored)",
)
def test_item_ids_referenced_in_real_fixture_resolve_where_expected():
    """Every plain-Object item currently in the real fixture's backpack
    should resolve in the item db (tool/weapon slots are skipped - they're
    not Data/Objects entries and aren't something the GUI's item picker
    would ever create)."""
    from svse.savemodel import SaveFile, get_slots

    main = SaveFile.load(FIXTURE_DIR / "PayaBean_441519152")
    db = load_items()
    slots = get_slots(main)
    checked = 0
    for slot in slots:
        if slot is None or slot.xsi_type != "Object":
            # tools/weapons/rings (MeleeWeapon, Hoe, FishingRod, Ring, ...)
            # live in different id namespaces and can share numeric ids with
            # unrelated Data/Objects entries - only "Object" items belong in
            # this db.
            continue
        checked += 1
        assert db.get(slot.item_id) is not None, f"item id {slot.item_id} ({slot.name}) not in db"
    assert checked > 0, "expected at least one plain-Object item in the fixture backpack"

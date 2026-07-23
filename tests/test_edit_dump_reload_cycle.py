"""Integration test: the full load -> edit -> dump -> reload cycle the real
app will do on every "Push to Device" - proves edits actually survive a
write+re-parse, not just an in-memory read of the same object."""

from pathlib import Path

import pytest

from svse.savemodel import SaveFile, add_item, find_free_slots, get_money, get_slots, set_money

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "sample_save"

_requires_fixture = pytest.mark.skipif(
    not (FIXTURE_DIR / "PayaBean_441519152").exists(),
    reason="Real save fixture not present locally (gitignored)",
)


@_requires_fixture
def test_money_and_inventory_edits_survive_dump_and_reload():
    main = SaveFile.load(FIXTURE_DIR / "PayaBean_441519152")
    info = SaveFile.load(FIXTURE_DIR / "SaveGameInfo")

    set_money(main, info, 42_000_000)
    free_index = find_free_slots(main)[0]
    add_item(
        main,
        item_id="272",
        name="Eggplant",
        category=-75,
        price=20,
        edibility=50,
        stack=1,
        quality=0,
    )

    main_bytes = main.dumps()
    info_bytes = info.dumps()

    reloaded_main = SaveFile.loads(main_bytes)
    reloaded_info = SaveFile.loads(info_bytes)

    assert get_money(reloaded_main) == 42_000_000
    assert int(reloaded_info.find("./money").text) == 42_000_000

    slots = get_slots(reloaded_main)
    assert slots[free_index] is not None
    assert slots[free_index].name == "Eggplant"
    assert slots[free_index].item_id == "272"

"""GUI smoke tests using pytest-qt, which drives Qt's own event system
directly (mouseClick/keyClick go through the real Qt event queue) - more
reliable than OS-level GUI automation for a custom-painted widget like
QListWidget, and doesn't require a visible display."""

from pathlib import Path

import pytest
from PySide6.QtCore import Qt

from svse.gui.widgets.item_picker_dialog import ItemPickerDialog
from svse.gui.main_window import MainWindow
from svse.itemdb import load_items
from svse.savemodel import SaveFile

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "sample_save"

_requires_fixture = pytest.mark.skipif(
    not (FIXTURE_DIR / "PayaBean_441519152").exists(),
    reason="Real save fixture not present locally (gitignored)",
)


def test_item_picker_dialog_search_and_select(qtbot):
    db = load_items()
    dialog = ItemPickerDialog(db)
    qtbot.addWidget(dialog)

    qtbot.keyClicks(dialog.search_box, "parsnip")
    assert dialog.results_list.count() >= 1
    assert dialog.results_list.item(0).text().startswith("Parsnip")

    assert not dialog.ok_button.isEnabled()
    dialog.results_list.setCurrentRow(0)
    assert dialog.ok_button.isEnabled()

    item = dialog.selected_item()
    assert item is not None
    assert item.name == "Parsnip"
    assert item.id == "24"

    qtbot.mouseClick(dialog.ok_button, Qt.LeftButton)
    assert dialog.result() == ItemPickerDialog.Accepted


@_requires_fixture
def test_main_window_loads_fixture_and_shows_money_and_slots(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    # Bypass the device layer entirely - load the local fixture files
    # directly into the session, exactly like a real pull would populate it.
    window.session.udid = "test-udid"
    window.session.folder_name = "PayaBean_441519152"
    window.session.main = SaveFile.load(FIXTURE_DIR / "PayaBean_441519152")
    window.session.info = SaveFile.load(FIXTURE_DIR / "SaveGameInfo")
    window.session.dirty = False
    window._populate_tabs()

    assert window.money_tab.isEnabled()
    assert window.money_tab.money_spin.value() == window.session.get_money()
    assert window.inventory_tab.isEnabled()
    assert window.push_button.isEnabled()


@_requires_fixture
def test_main_window_money_edit_marks_dirty_and_updates_session(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.session.main = SaveFile.load(FIXTURE_DIR / "PayaBean_441519152")
    window.session.info = SaveFile.load(FIXTURE_DIR / "SaveGameInfo")
    window._populate_tabs()

    assert window.session.dirty is False
    window.money_tab.money_spin.setValue(12345)

    assert window.session.dirty is True
    assert window.session.get_money() == 12345
    assert "Unsaved changes" in window.dirty_label.text()


@_requires_fixture
def test_main_window_add_item_updates_grid_and_session(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.session.main = SaveFile.load(FIXTURE_DIR / "PayaBean_441519152")
    window.session.info = SaveFile.load(FIXTURE_DIR / "SaveGameInfo")
    window._populate_tabs()

    free_before = [i for i, s in enumerate(window.session.get_slots()) if s is None]
    assert free_before, "fixture save has no free slots to test with"

    window._on_item_add_requested("272", "Eggplant", 1, 0)

    slots = window.session.get_slots()
    added_index = free_before[0]
    assert slots[added_index] is not None
    assert slots[added_index].name == "Eggplant"
    assert window.session.dirty is True
    # grid widget should reflect it too - full name lives in the tooltip
    # (the button itself only shows an icon + short qty/quality caption,
    # see inventory_slot_widget.py)
    assert "Eggplant" in window.inventory_tab._slot_widgets[added_index].toolTip()


@_requires_fixture
def test_main_window_relationships_tab_loads_and_edits(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.session.main = SaveFile.load(FIXTURE_DIR / "PayaBean_441519152")
    window.session.info = SaveFile.load(FIXTURE_DIR / "SaveGameInfo")
    window._populate_tabs()

    assert window.relationships_tab.isEnabled()
    assert window.relationships_tab.table.rowCount() > 0
    assert "Lewis" in window.relationships_tab._npc_order

    row = window.relationships_tab._npc_order.index("Lewis")
    slider = window.relationships_tab.table.cellWidget(row, 2)
    slider.setValue(2000)

    assert window.session.get_friendships()["Lewis"].points == 2000
    assert window.session.dirty is True


@_requires_fixture
def test_main_window_map_tab_loads_placed_objects(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.session.main = SaveFile.load(FIXTURE_DIR / "PayaBean_441519152")
    window.session.info = SaveFile.load(FIXTURE_DIR / "SaveGameInfo")
    window._populate_tabs()

    assert window.map_tab.isEnabled()
    # real Farm has hundreds of placed objects in the fixture
    assert len(window.map_tab.canvas._occupied) > 100


@_requires_fixture
def test_main_window_place_chest_on_free_tile_via_session(qtbot):
    from svse.savemodel import list_occupied_tiles

    window = MainWindow()
    qtbot.addWidget(window)
    window.session.main = SaveFile.load(FIXTURE_DIR / "PayaBean_441519152")
    window.session.info = SaveFile.load(FIXTURE_DIR / "SaveGameInfo")
    window._populate_tabs()

    # must stay within TileCanvas's default rendered grid (120x100) -
    # unlike the savemodel-level test, which deliberately picks a
    # far-out-of-bounds tile since it doesn't render anything.
    occupied = list_occupied_tiles(window.session.main, "Farm")
    free_tile = next(
        (x, 90) for x in range(0, 120) if (x, 90) not in occupied
    )

    window._on_chest_place_requested(*free_tile)

    assert free_tile in window.map_tab.canvas._occupied
    assert window.session.dirty is True


@_requires_fixture
def test_main_window_place_chest_on_occupied_tile_shows_warning_not_crash(qtbot, monkeypatch):
    from svse.gui import main_window as main_window_module
    from svse.savemodel import list_occupied_tiles

    window = MainWindow()
    qtbot.addWidget(window)
    window.session.main = SaveFile.load(FIXTURE_DIR / "PayaBean_441519152")
    window.session.info = SaveFile.load(FIXTURE_DIR / "SaveGameInfo")
    window._populate_tabs()

    occupied_tile = next(iter(list_occupied_tiles(window.session.main, "Farm")))
    warned = {}
    monkeypatch.setattr(
        main_window_module.QMessageBox,
        "warning",
        lambda *a, **k: warned.setdefault("called", True),
    )

    window._on_chest_place_requested(*occupied_tile)

    assert warned.get("called") is True
    assert window.session.dirty is False  # nothing was actually written

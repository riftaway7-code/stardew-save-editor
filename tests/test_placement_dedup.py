"""Regression test for tonight's real incident: placing a second object at a
tile that already has one creates a duplicate <objects> dict key, which
corrupts the save (the game silently falls back to an older auto-backup on
load). validate_no_duplicate_tiles must catch this before any push."""

from copy import deepcopy
from pathlib import Path

import pytest
from lxml import etree

from svse.savemodel.save_file import SaveFile
from svse.savemodel.validation import ValidationError, validate_before_push, validate_no_duplicate_tiles

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "sample_save"

_requires_fixture = pytest.mark.skipif(
    not (FIXTURE_DIR / "PayaBean_441519152").exists(),
    reason="Real save fixture not present locally (gitignored)",
)


def _duplicate_first_farm_object(main: SaveFile) -> None:
    xsi_type = "{http://www.w3.org/2001/XMLSchema-instance}type"
    location = main.find(f"./locations/GameLocation[@{xsi_type}='Farm']")
    objects_el = location.find("./objects")
    first_item = objects_el.find("./item")
    # Clone the exact first entry (same tile key) and append it - this is
    # precisely the mistake made tonight (placing a new chest at a tile that
    # already had one).
    objects_el.append(deepcopy(first_item))


@_requires_fixture
def test_clean_real_save_has_no_duplicate_tiles():
    main = SaveFile.load(FIXTURE_DIR / "PayaBean_441519152")
    # must not raise
    validate_no_duplicate_tiles(main, "Farm")


@_requires_fixture
def test_duplicate_tile_is_detected():
    main = SaveFile.load(FIXTURE_DIR / "PayaBean_441519152")
    _duplicate_first_farm_object(main)

    with pytest.raises(ValidationError, match="Duplicate object"):
        validate_no_duplicate_tiles(main, "Farm")


@_requires_fixture
def test_validate_before_push_refuses_to_pass_a_corrupted_save():
    main = SaveFile.load(FIXTURE_DIR / "PayaBean_441519152")
    info = SaveFile.load(FIXTURE_DIR / "SaveGameInfo")
    _duplicate_first_farm_object(main)

    with pytest.raises(ValidationError):
        validate_before_push(main, info)

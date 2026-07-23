"""Byte-identical round-trip test: this must pass before any editing feature
in savemodel/ is trusted (see project plan, "Guiding Principles" #1)."""

from pathlib import Path

import pytest

from svse.savemodel.save_file import SaveFile

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "sample_save"

_requires_fixture = pytest.mark.skipif(
    not (FIXTURE_DIR / "PayaBean_441519152").exists(),
    reason=(
        "Real save fixture not present (gitignored, personal data - pull one "
        "with tools/smoke_test_device.py against a live device to populate "
        "tests/fixtures/sample_save/ locally before running this test)"
    ),
)


@_requires_fixture
def test_main_save_roundtrip_is_byte_identical():
    path = FIXTURE_DIR / "PayaBean_441519152"
    original = path.read_bytes()

    save = SaveFile.loads(original)
    reserialized = save.dumps()

    assert reserialized == original


@_requires_fixture
def test_save_game_info_roundtrip_is_byte_identical():
    path = FIXTURE_DIR / "SaveGameInfo"
    original = path.read_bytes()

    save = SaveFile.loads(original)
    reserialized = save.dumps()

    assert reserialized == original


def test_missing_bom_raises_malformed_error():
    from svse.savemodel.save_file import MalformedSaveError

    with pytest.raises(MalformedSaveError):
        SaveFile.loads(b'<?xml version="1.0"?><SaveGame></SaveGame>')

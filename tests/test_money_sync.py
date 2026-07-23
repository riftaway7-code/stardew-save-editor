from pathlib import Path

import pytest

from svse.savemodel import SaveFile, get_money, is_synced, set_money

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "sample_save"

_requires_fixture = pytest.mark.skipif(
    not (FIXTURE_DIR / "PayaBean_441519152").exists(),
    reason="Real save fixture not present locally (gitignored)",
)


@_requires_fixture
def test_money_starts_synced():
    main = SaveFile.load(FIXTURE_DIR / "PayaBean_441519152")
    info = SaveFile.load(FIXTURE_DIR / "SaveGameInfo")
    assert is_synced(main, info)


@_requires_fixture
def test_set_money_updates_both_files():
    main = SaveFile.load(FIXTURE_DIR / "PayaBean_441519152")
    info = SaveFile.load(FIXTURE_DIR / "SaveGameInfo")

    set_money(main, info, 99_999_999)

    assert get_money(main) == 99_999_999
    assert int(info.find("./money").text) == 99_999_999
    assert is_synced(main, info)


@_requires_fixture
def test_set_money_rejects_negative():
    main = SaveFile.load(FIXTURE_DIR / "PayaBean_441519152")
    info = SaveFile.load(FIXTURE_DIR / "SaveGameInfo")

    with pytest.raises(ValueError):
        set_money(main, info, -1)

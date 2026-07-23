from pathlib import Path

import pytest

from svse.savemodel import SaveFile, get_friendships, set_points
from svse.savemodel.relationships import MAX_POINTS_NORMAL, MAX_POINTS_SPOUSE

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "sample_save"

_requires_fixture = pytest.mark.skipif(
    not (FIXTURE_DIR / "PayaBean_441519152").exists(),
    reason="Real save fixture not present locally (gitignored)",
)


def _load_main() -> SaveFile:
    return SaveFile.load(FIXTURE_DIR / "PayaBean_441519152")


@_requires_fixture
def test_get_friendships_returns_all_npcs_with_hearts():
    main = _load_main()
    friendships = get_friendships(main)
    assert "Lewis" in friendships
    lewis = friendships["Lewis"]
    assert lewis.points == 1379
    assert lewis.status == "Friendly"
    assert lewis.hearts == 1379 // 250


@_requires_fixture
def test_married_npc_has_higher_cap_and_correct_hearts():
    main = _load_main()
    friendships = get_friendships(main)
    harvey = friendships["Harvey"]
    assert harvey.status == "Married"
    assert harvey.points == 3516
    assert harvey.max_points == MAX_POINTS_SPOUSE
    # hearts display should cap at 14 even if points exceed 3500 slightly
    assert harvey.hearts == 14


@_requires_fixture
def test_set_points_updates_and_is_readable_back():
    main = _load_main()
    set_points(main, "Lewis", 2000)
    friendships = get_friendships(main)
    assert friendships["Lewis"].points == 2000
    assert friendships["Lewis"].hearts == 8


@_requires_fixture
def test_set_points_clamps_to_normal_max_for_non_spouse():
    main = _load_main()
    set_points(main, "Lewis", 999999)
    friendships = get_friendships(main)
    assert friendships["Lewis"].points == MAX_POINTS_NORMAL


@_requires_fixture
def test_set_points_clamps_to_spouse_max_for_married_npc():
    main = _load_main()
    set_points(main, "Harvey", 999999)
    friendships = get_friendships(main)
    assert friendships["Harvey"].points == MAX_POINTS_SPOUSE


@_requires_fixture
def test_set_points_clamps_negative_to_zero():
    main = _load_main()
    set_points(main, "Lewis", -500)
    friendships = get_friendships(main)
    assert friendships["Lewis"].points == 0


@_requires_fixture
def test_set_points_unknown_npc_raises():
    main = _load_main()
    with pytest.raises(ValueError):
        set_points(main, "NotARealVillager", 100)


@_requires_fixture
def test_relationship_edit_survives_dump_and_reload():
    main = _load_main()
    set_points(main, "Abigail", 2500)
    reloaded = SaveFile.loads(main.dumps())
    friendships = get_friendships(reloaded)
    assert friendships["Abigail"].points == 2500

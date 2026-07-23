"""NPC friendship (hearts) read/write.

Schema captured from a real save's <player><friendshipData> dict:
    <item><key><string>Lewis</string></key>
    <value><Friendship><Points>1379</Points>...<Status>Friendly</Status>
    ...</Friendship></value></item>

250 friendship points = 1 heart. Regular villagers cap at 10 hearts (2500
points); a married/roommate spouse can go up to 14 hearts (3500 points) -
verified against a real save containing a Married NPC at 3516 points."""

from __future__ import annotations

from dataclasses import dataclass

from svse.savemodel.save_file import SaveFile

POINTS_PER_HEART = 250
MAX_POINTS_NORMAL = 2500  # 10 hearts
MAX_POINTS_SPOUSE = 3500  # 14 hearts
_SPOUSE_STATUSES = {"Married", "Roommate"}

_FRIENDSHIP_DATA_PATH = "./player/friendshipData"


@dataclass
class FriendshipInfo:
    npc_name: str
    points: int
    status: str

    @property
    def hearts(self) -> int:
        return min(self.points, self.max_points) // POINTS_PER_HEART

    @property
    def max_points(self) -> int:
        return MAX_POINTS_SPOUSE if self.status in _SPOUSE_STATUSES else MAX_POINTS_NORMAL


def get_friendships(main: SaveFile) -> dict[str, FriendshipInfo]:
    data_el = main.find(_FRIENDSHIP_DATA_PATH)
    if data_el is None:
        return {}
    result: dict[str, FriendshipInfo] = {}
    for item in data_el:
        name_el = item.find("./key/string")
        points_el = item.find("./value/Friendship/Points")
        status_el = item.find("./value/Friendship/Status")
        if name_el is None or points_el is None:
            continue
        name = name_el.text
        result[name] = FriendshipInfo(
            npc_name=name,
            points=int(points_el.text or "0"),
            status=status_el.text if status_el is not None else "Friendly",
        )
    return result


def set_points(main: SaveFile, npc_name: str, points: int) -> None:
    """Set an NPC's friendship points, clamped to [0, max_points] for their
    current relationship status (see FriendshipInfo.max_points)."""
    data_el = main.find(_FRIENDSHIP_DATA_PATH)
    if data_el is None:
        raise ValueError("Save file has no <player><friendshipData> element")

    for item in data_el:
        name_el = item.find("./key/string")
        if name_el is None or name_el.text != npc_name:
            continue
        points_el = item.find("./value/Friendship/Points")
        status_el = item.find("./value/Friendship/Status")
        if points_el is None:
            raise ValueError(f"No <Points> element for {npc_name}")
        status = status_el.text if status_el is not None else "Friendly"
        max_points = MAX_POINTS_SPOUSE if status in _SPOUSE_STATUSES else MAX_POINTS_NORMAL
        clamped = max(0, min(points, max_points))
        points_el.text = str(clamped)
        return

    raise ValueError(f"No friendship data found for NPC {npc_name!r}")

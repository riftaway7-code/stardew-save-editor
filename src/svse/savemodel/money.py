"""Money is stored in two places that must never drift apart: the main
save's <player><money> and the load-screen preview file's <money> (root
element of SaveGameInfo). Verified live tonight - editing only the main save
left the load screen showing stale money until the file was re-synced."""

from __future__ import annotations

from svse.savemodel.save_file import SaveFile


def get_money(main: SaveFile) -> int:
    el = main.find("./player/money")
    if el is None or el.text is None:
        raise ValueError("Save file has no <player><money> element")
    return int(el.text)


def set_money(main: SaveFile, info: SaveFile, value: int) -> None:
    if value < 0:
        raise ValueError("Money cannot be negative")
    main_el = main.find("./player/money")
    if main_el is None:
        raise ValueError("Save file has no <player><money> element")
    main_el.text = str(value)

    info_el = info.find("./money")
    if info_el is None:
        raise ValueError("SaveGameInfo has no <money> element")
    info_el.text = str(value)


def is_synced(main: SaveFile, info: SaveFile) -> bool:
    return get_money(main) == int(info.find("./money").text)

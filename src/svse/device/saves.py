from __future__ import annotations

import re
import tempfile
from pathlib import Path

from svse.device import _shell
from svse.device.errors import HouseArrestError, SaveNotFoundError
from svse.device.models import SaveFolderInfo

_SAVE_FOLDER_RE = re.compile(r"^(?P<farm_name>.+)_(?P<unique_id>\d+)$")
# Never touch these - they're the game's own auto-recovery backups.
_PROTECTED_SUFFIXES = ("_old", "_SVBAK", "_SVEMERG")


def _peek_int(xml_bytes: bytes, tag: str) -> int | None:
    match = re.search(rf"<{tag}>(\d+)</{tag}>".encode(), xml_bytes)
    return int(match.group(1)) if match else None


def list_save_folders(udid: str | None = None) -> list[SaveFolderInfo]:
    """List save folders on the device. `udid` is accepted for interface
    consistency with the rest of the device layer but unused here - the
    underlying CLI always targets the first attached device; multi-device
    disambiguation is a documented limitation until pymobiledevice3's shell
    quirks (see svse.device._shell) are worked around more precisely."""
    names = _shell.list_root_entries()
    folders: list[SaveFolderInfo] = []
    with tempfile.TemporaryDirectory(prefix="svse_peek_") as tmp:
        tmp_path = Path(tmp)
        for name in names:
            m = _SAVE_FOLDER_RE.match(name)
            if not m:
                continue
            info_dest = tmp_path / f"{name}_SaveGameInfo"
            try:
                _shell.pull_file(name, "SaveGameInfo", info_dest)
                data = info_dest.read_bytes()
                money = _peek_int(data, "money")
                days_played = _peek_int(data, "daysPlayed")
            except Exception:
                money = days_played = None
            folders.append(
                SaveFolderInfo(
                    folder_name=name,
                    farm_name=m.group("farm_name"),
                    unique_id=m.group("unique_id"),
                    money=money,
                    days_played=days_played,
                )
            )
    return folders


def pull_save(udid: str | None, folder_name: str) -> dict[str, bytes]:
    """Pull exactly the two live save files (main save + SaveGameInfo) as
    in-memory bytes, keyed by their filename. Deliberately never touches the
    game's own `_old`/`_SVBAK`/`_SVEMERG` backups."""
    with tempfile.TemporaryDirectory(prefix="svse_pull_") as tmp:
        tmp_path = Path(tmp)
        main_dest = tmp_path / folder_name
        info_dest = tmp_path / "SaveGameInfo"
        try:
            _shell.pull_file(folder_name, folder_name, main_dest)
            _shell.pull_file(folder_name, "SaveGameInfo", info_dest)
        except HouseArrestError as exc:
            raise SaveNotFoundError(f"Couldn't pull save {folder_name!r}: {exc}") from exc
        return {
            folder_name: main_dest.read_bytes(),
            "SaveGameInfo": info_dest.read_bytes(),
        }


def push_save(udid: str | None, folder_name: str, files: dict[str, bytes]) -> None:
    """Write files back to the device. Callers MUST have already snapshotted
    and validated `files` - see svse.safety.snapshots and
    svse.savemodel.validation. This function does not validate content."""
    for filename in files:
        if any(filename.endswith(suffix) for suffix in _PROTECTED_SUFFIXES):
            raise ValueError(f"Refusing to write to protected backup file: {filename}")
    with tempfile.TemporaryDirectory(prefix="svse_push_") as tmp:
        tmp_path = Path(tmp)
        for filename, data in files.items():
            local_src = tmp_path / filename
            local_src.write_bytes(data)
            _shell.push_file(folder_name, filename, local_src)


def local_pulled_paths(pulled: dict[str, bytes], dest_dir: Path, folder_name: str) -> dict[str, Path]:
    """Write a pulled save dict to local disk under dest_dir/folder_name/ and
    return the resulting paths, for callers that want files on disk rather
    than in memory (e.g. for ElementTree.parse)."""
    out_dir = dest_dir / folder_name
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {}
    for filename, data in pulled.items():
        path = out_dir / filename
        path.write_bytes(data)
        paths[filename] = path
    return paths

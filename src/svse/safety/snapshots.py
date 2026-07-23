"""Local backups taken before every device write - separate from, and in
addition to, the game's own `_old`/`_SVBAK`/`_SVEMERG` backups (which we
never touch). Lets a user recover from a bad push even if the game's own
recovery mechanism also gets confused (as happened tonight)."""

from __future__ import annotations

import time
from pathlib import Path

_BACKUP_ROOT = Path.home() / "Library" / "Application Support" / "StardewSaveEditor" / "backups"


def snapshot_dir_for(folder_name: str) -> Path:
    _BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
    return _BACKUP_ROOT


def take_snapshot(folder_name: str, files: dict[str, bytes]) -> Path:
    """Write `files` (as currently pulled from the device, BEFORE any local
    edits are applied to them) into a fresh timestamped backup directory.
    Returns the directory path."""
    _BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    out_dir = _BACKUP_ROOT / f"{folder_name}_{timestamp}"
    out_dir.mkdir(parents=True, exist_ok=False)
    for filename, data in files.items():
        (out_dir / filename).write_bytes(data)
    return out_dir


def list_snapshots(folder_name: str | None = None) -> list[Path]:
    if not _BACKUP_ROOT.exists():
        return []
    dirs = [d for d in _BACKUP_ROOT.iterdir() if d.is_dir()]
    if folder_name:
        dirs = [d for d in dirs if d.name.startswith(f"{folder_name}_")]
    return sorted(dirs, key=lambda d: d.name, reverse=True)


def load_snapshot(snapshot_dir: Path) -> dict[str, bytes]:
    return {p.name: p.read_bytes() for p in snapshot_dir.iterdir() if p.is_file()}

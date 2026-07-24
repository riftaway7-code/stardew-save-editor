#!/usr/bin/env python3
"""svse-helper — pull/push a Stardew Valley save between a connected
iPhone/iPad and the online save editor.

Self-contained: the ONLY thing you need to install is pymobiledevice3.

    python3 -m pip install pymobiledevice3

Then, with your device plugged in over USB (unlocked, "Trust This Computer"
accepted, and Developer Mode on):

    python3 svse-helper.py list           # show saves on the device
    python3 svse-helper.py pull           # copy the active save to ~/Downloads
    python3 svse-helper.py push --in ~/Downloads/<Farm>_<id>

Between pull and push: open the pulled file in the web editor, edit it, and
download the edited file back into that same folder (overwrite), then push.

This drives pymobiledevice3's proven `apps afc <bundle> --documents` shell,
the same mechanism the desktop app uses. It never touches the game's own
_old / _SVBAK / _SVEMERG backup files.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

BUNDLE_ID = "com.chucklefish.stardewvalley"
PROTECTED_SUFFIXES = ("_old", "_SVBAK", "_SVEMERG")
SAVE_FOLDER_RE = re.compile(r"^(?P<farm>.+)_(?P<id>\d+)$")
NOISE = ("Welcome to", "Use show-help", "These special commands", "xonsh")


def pmd3_argv() -> list[str]:
    """How to invoke the pymobiledevice3 CLI."""
    if shutil.which("pymobiledevice3"):
        return ["pymobiledevice3"]
    return [sys.executable, "-m", "pymobiledevice3"]


def check_pmd3() -> None:
    try:
        import pymobiledevice3  # noqa: F401
    except ImportError:
        sys.exit("pymobiledevice3 isn't installed.\n"
                 "Install it with:  python3 -m pip install pymobiledevice3")


def run_afc(commands: list[str], timeout: float = 60.0) -> str:
    """Run AFC shell commands in one session against the app's Documents."""
    script = "\n".join(commands) + "\nexit\n"
    proc = subprocess.run(
        [*pmd3_argv(), "apps", "afc", BUNDLE_ID, "--documents"],
        input=script, capture_output=True, text=True, timeout=timeout,
    )
    return proc.stdout + proc.stderr


def list_entries() -> list[str]:
    out = run_afc(["ls"])
    names = []
    for line in out.splitlines():
        s = line.strip()
        if not s or " " in s or any(n in s for n in NOISE):
            continue
        names.append(s)
    return names


def peek_money(save_folder: str) -> int | None:
    with tempfile.TemporaryDirectory() as tmp:
        dest = Path(tmp) / "SaveGameInfo"
        run_afc([f"cd {save_folder}", f"pull SaveGameInfo {dest}"])
        if dest.exists() and dest.stat().st_size:
            m = re.search(rb"<money>(\d+)</money>", dest.read_bytes())
            if m:
                return int(m.group(1))
    return None


def find_saves() -> list[tuple[str, str, int | None]]:
    saves = []
    for name in list_entries():
        m = SAVE_FOLDER_RE.match(name)
        if not m or any(name.endswith(s) for s in PROTECTED_SUFFIXES):
            continue
        saves.append((name, m.group("farm"), peek_money(name)))
    return saves


def cmd_list(_args) -> int:
    check_pmd3()
    saves = find_saves()
    if not saves:
        print("No Stardew saves found. Is Stardew installed, the device "
              "unlocked and trusted, and Developer Mode on?")
        return 1
    print(f"Found {len(saves)} save(s):")
    for folder, farm, money in saves:
        g = f"{money:,}g" if money is not None else "?g"
        print(f"  {folder}   ({farm} Farm, {g})")
    return 0


def pick(folder_arg: str | None) -> str:
    saves = find_saves()
    if not saves:
        sys.exit("No Stardew saves found on the device.")
    if folder_arg:
        for folder, _, _ in saves:
            if folder == folder_arg:
                return folder
        sys.exit(f"No save folder named {folder_arg!r} on the device.")
    if len(saves) == 1:
        return saves[0][0]
    print("Multiple saves found - choose one with --folder <name>:")
    for folder, farm, _ in saves:
        print(f"  {folder}   ({farm} Farm)")
    sys.exit(2)


def cmd_pull(args) -> int:
    check_pmd3()
    folder = pick(args.folder)
    out_dir = Path(args.out).expanduser() / folder
    out_dir.mkdir(parents=True, exist_ok=True)
    main_dest = out_dir / folder
    info_dest = out_dir / "SaveGameInfo"
    print(f"Pulling {folder} …")
    run_afc([f"cd {folder}", f"pull {folder} {main_dest}",
             f"pull SaveGameInfo {info_dest}"])
    if not main_dest.exists() or not main_dest.stat().st_size:
        sys.exit(f"Failed to pull the save. Shell output:\n{run_afc(['ls'])}")
    print("Done. Pulled to:")
    print(f"  {main_dest}  ({main_dest.stat().st_size:,} bytes)")
    print()
    print("Next: open this file in the web editor, edit, and download the")
    print("edited file back into this folder (overwrite). Then run:")
    print(f'  python3 svse-helper.py push --in "{out_dir}"')
    return 0


def cmd_push(args) -> int:
    check_pmd3()
    in_dir = Path(args.inpath).expanduser()
    if not in_dir.is_dir():
        sys.exit(f"{in_dir} is not a folder. Point --in at the pulled save folder.")
    folder = in_dir.name
    files = [p for p in sorted(in_dir.iterdir())
             if p.is_file() and not p.name.startswith(".")
             and not any(p.name.endswith(s) for s in PROTECTED_SUFFIXES)]
    if not files:
        sys.exit(f"No files to push in {in_dir}.")
    print(f"Pushing into {folder} on the device: " + ", ".join(p.name for p in files))
    if not args.yes:
        reply = input("This overwrites the save on your device. Continue? [y/N] ")
        if reply.strip().lower() not in ("y", "yes"):
            print("Cancelled.")
            return 1
    for p in files:
        run_afc([f"cd {folder}", f"push {p} {p.name}"])
    print("Done. Open Stardew on the device to load your edited save.")
    return 0


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(
        prog="svse-helper.py",
        description="Pull/push a Stardew save between a connected iPhone/iPad "
                    "and the online save editor.")
    sub = p.add_subparsers(dest="action", required=True)
    sub.add_parser("list", help="list saves on the connected device")
    sp = sub.add_parser("pull", help="copy the active save to a local folder")
    sp.add_argument("--out", default=str(Path.home() / "Downloads"))
    sp.add_argument("--folder", default=None)
    su = sub.add_parser("push", help="write an edited save back to the device")
    su.add_argument("--in", dest="inpath", required=True)
    su.add_argument("-y", "--yes", action="store_true")
    args = p.parse_args(argv)
    try:
        return {"list": cmd_list, "pull": cmd_pull, "push": cmd_push}[args.action](args)
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

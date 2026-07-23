#!/usr/bin/env python3
"""Helper scaffold: pull_push.py

Lightweight wrapper to PULL a Stardew save from a connected iOS device and PUSH an edited save back.
This is intentionally a scaffold: it prefers calling an existing pymobiledevice3-based CLI if installed,
otherwise it prints the developer commands the user should run.

DO NOT run this script without reviewing. It is a helper scaffold for devs.
"""

import sys
import shutil
import subprocess
from pathlib import Path

HELP = '''svse helper (scaffold)

Usage:
  python3 pull_push.py pull   --out ~/Downloads  # pull the active Stardew save from device to Downloads
  python3 pull_push.py push  --in  ~/Downloads/YourFarm  # push edited save back into device
  python3 pull_push.py --help

Notes:
- This script tries to call the system pymobiledevice3 CLI ("pymobiledevice3" / "pmd3").
- If pymobiledevice3 isn't installed, it prints the copy-paste commands to run manually.
- This scaffold intentionally does not auto-run destructive commands; it guides and shows commands.
'''


def run_cmd(cmd):
    print("=>", " ".join(cmd))
    try:
        r = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print(r.stdout)
        return 0
    except FileNotFoundError:
        return None
    except subprocess.CalledProcessError as e:
        print(e.stderr, file=sys.stderr)
        return e.returncode


def find_cli():
    # common names: pymobiledevice3 provides "pymobiledevice3" or "pmd3" depending on install
    for name in ("pymobiledevice3", "pmd3", "pmd3-cli"):
        if shutil.which(name):
            return name
    return None


def pull(out_dir: Path):
    cli = find_cli()
    if not cli:
        print("pymobiledevice3 CLI not found.")
        print("Dev instructions: install with: python3 -m pip install pymobiledevice3")
        print("Then run the device pull command. Example (may vary):")
        print("  pmd3 afc pull /path/to/Containers/Data/Application/<Stardew>/Documents/<save-file> " + str(out_dir))
        return 2
    # best-effort example using CLI; exact args depend on the CLI variant
    # This scaffold prints the command rather than guessing unpacking details.
    print(f"Found device CLI: {cli}. Please run the appropriate afc/house_arrest pull command for Stardew app.")
    print("Example (universal template):")
    print(f"  {cli} house_arrest pull com.chucklefish.stardewvalley.savedata /Documents/<farmname> {out_dir}")
    return 0


def push(in_path: Path):
    cli = find_cli()
    if not cli:
        print("pymobiledevice3 CLI not found.")
        print("Dev instructions: install with: python3 -m pip install pymobiledevice3")
        print("Then run the device push command. Example (may vary):")
        print("  pmd3 afc push ~/Downloads/<farmname> /path/to/Containers/Data/Application/<Stardew>/Documents/")
        return 2
    print(f"Found device CLI: {cli}. Please run the appropriate afc/house_arrest push command for Stardew app.")
    print("Example (universal template):")
    print(f"  {cli} house_arrest push {in_path} com.chucklefish.stardewvalley.savedata /Documents/")
    return 0


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(HELP)
        return 0
    cmd = argv[0]
    import argparse
    p = argparse.ArgumentParser(prog="pull_push.py")
    sub = p.add_subparsers(dest="action")
    spull = sub.add_parser("pull")
    spull.add_argument("--out", default=str(Path.home() / "Downloads"))
    spush = sub.add_parser("push")
    spush.add_argument("--in", dest="inpath", required=True)
    args = p.parse_args(argv)
    if args.action == "pull":
        return pull(Path(args.out))
    if args.action == "push":
        return push(Path(args.inpath))
    print(HELP)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

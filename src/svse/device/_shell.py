"""Drives pymobiledevice3's interactive `apps afc --documents` shell via a
subprocess, piping a small script to stdin.

Why not the raw async AfcService/HouseArrestService API directly: empirical
testing tonight showed the raw `listdir()`/`exists()`/`get_file_contents()`
calls return PERM_DENIED/OBJECT_NOT_FOUND for paths that the interactive CLI
shell (used manually, successfully, for hours) handles correctly - there's
some cwd/session initialization the shell's `AfcShell` class does that isn't
reproduced by calling the service methods directly, and it wasn't worth
reverse-engineering further under time pressure. Shelling out to the proven
CLI path trades a bit of elegance for reliability we've actually verified.
If a future pymobiledevice3 release exposes the working behavior via a clean
API, this module is the only place that needs to change.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

from svse.device.errors import HouseArrestError
from svse.device.models import STARDEW_BUNDLE_ID

_NOISE_SUBSTRINGS = (
    "Welcome to xonsh-afc shell",
    "Use show-help",
    "These special commands",
)


def _pymobiledevice3_argv() -> list[str]:
    """Locate a way to invoke pymobiledevice3's CLI.

    In a py2app-frozen build, `sys.executable` is the GUI app's own launcher
    binary, NOT a generic Python interpreter - passing it `-m pymobiledevice3`
    just re-launches the GUI with weird argv instead of running the CLI
    (confirmed by testing the packaged build: it silently produced empty
    output instead of erroring). The fix is a second bundled executable
    (packaging/pmd3_cli.py, added via py2app's `extra_scripts`) that sits
    next to the main binary in Contents/MacOS/ and shares the same bundled
    pymobiledevice3 - RESOURCEPATH (set by py2app, see svse.paths) tells us
    we're frozen and where Contents/ is, so we can find it.

    In dev (running from source, not frozen), `sys.executable` is a normal
    venv Python and `-m pymobiledevice3` works directly - no second script
    needed."""
    resource_path = os.environ.get("RESOURCEPATH")
    if resource_path:
        macos_dir = Path(resource_path).parent / "MacOS"
        return [str(macos_dir / "pmd3_cli")]
    return [sys.executable, "-m", "pymobiledevice3"]


def run_afc_script(commands: list[str], bundle_id: str = STARDEW_BUNDLE_ID, timeout: float = 30.0) -> str:
    """Run a sequence of AFC shell commands (e.g. ["cd Foo", "ls -la"]) in one
    session and return raw combined stdout+stderr text."""
    script = "\n".join(commands) + "\nexit\n"
    proc = subprocess.run(
        [*_pymobiledevice3_argv(), "apps", "afc", bundle_id, "--documents"],
        input=script,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return proc.stdout + proc.stderr


def list_root_entries(bundle_id: str = STARDEW_BUNDLE_ID) -> list[str]:
    """List the Documents root by filename pattern matching, since the
    shell's own `ls` output isn't structured - we rely on the fact that only
    real filenames match the FarmName_digits / plain-name shape and the
    shell's banner text doesn't."""
    output = run_afc_script(["ls"], bundle_id=bundle_id)
    names = []
    for line in output.splitlines():
        stripped = line.strip()
        if not stripped or any(noise in stripped for noise in _NOISE_SUBSTRINGS):
            continue
        # ls output is one bare name per line with no extra formatting for
        # this shell (verified manually) - skip anything with whitespace,
        # which would indicate we captured a prose/banner fragment instead.
        if " " in stripped:
            continue
        names.append(stripped)
    return names


def pull_file(folder_name: str, filename: str, local_dest: Path, bundle_id: str = STARDEW_BUNDLE_ID) -> None:
    local_dest.parent.mkdir(parents=True, exist_ok=True)
    output = run_afc_script(
        [f"cd {folder_name}", f"pull {filename} {local_dest}"],
        bundle_id=bundle_id,
    )
    if not local_dest.exists() or local_dest.stat().st_size == 0:
        raise HouseArrestError(
            f"Failed to pull {folder_name}/{filename} from device. Shell output:\n{output}"
        )


def push_file(folder_name: str, filename: str, local_src: Path, bundle_id: str = STARDEW_BUNDLE_ID) -> None:
    if not local_src.exists():
        raise FileNotFoundError(local_src)
    run_afc_script(
        [f"cd {folder_name}", f"push {local_src} {filename}"],
        bundle_id=bundle_id,
    )

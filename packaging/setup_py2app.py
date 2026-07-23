"""py2app build script.

Run from the project root (not from packaging/) with the project venv
active:
    python packaging/setup_py2app.py py2app

Bundles data/items.json, data/tilesheets/, and the theme's fonts/QSS -
py2app does not auto-include non-Python data files, so they're listed
explicitly below.

Also bundles pmd3_cli.py as a second executable (extra_scripts) - the
device layer shells out to a real `pymobiledevice3` CLI process (see
svse.device._shell), and py2app apps don't include a generic `python -m`
capable interpreter by default (sys.executable inside the frozen app is the
GUI's own launcher binary, not a plain interpreter - confirmed by testing).

KNOWN MANUAL STEP after building: py2app's dylib-copying step corrupts
libssl.3.dylib/libcrypto.3.dylib's code signature when rewriting install
names (a macholib bug with this particular Homebrew-built dylib), which
makes cryptography's Rust extension fail to dlopen. Re-copy the real
Homebrew OpenSSL libs and re-sign them after every build - see
packaging/fix_dylibs.sh, which does exactly this and should be run
immediately after `python packaging/setup_py2app.py py2app`.
"""

from __future__ import annotations

from pathlib import Path
from setuptools import setup

ROOT = Path(__file__).parent.parent

APP = [str(ROOT / "run.py")]

DATA_FILES = [
    ("data", [str(ROOT / "data" / "items.json")]),
]


def _tree_data_files(src_dir: Path, dest_prefix: str) -> list[tuple[str, list[str]]]:
    """py2app's DATA_FILES wants (dest_dir, [file, ...]) pairs, one per
    source directory - walk the tree and build that structure."""
    entries: list[tuple[str, list[str]]] = []
    for dirpath in sorted({p.parent for p in src_dir.rglob("*") if p.is_file()}):
        files = [str(p) for p in dirpath.iterdir() if p.is_file()]
        if not files:
            continue
        rel = dirpath.relative_to(src_dir)
        dest = f"{dest_prefix}/{rel}".rstrip("/.")
        entries.append((dest, files))
    return entries


DATA_FILES += _tree_data_files(ROOT / "data" / "tilesheets", "data/tilesheets")
DATA_FILES += _tree_data_files(ROOT / "src" / "svse" / "gui" / "theme" / "fonts", "svse/gui/theme/fonts")
DATA_FILES += [
    ("svse/gui/theme", [str(ROOT / "src" / "svse" / "gui" / "theme" / "stardew.qss")]),
]

OPTIONS = {
    "argv_emulation": False,
    # xmod does self-mutating import-time metaprogramming (replaces its own
    # module object with a callable class) that breaks under py2app's
    # default zipimport-based freezing - force it and its dependents to be
    # copied as loose files instead (confirmed fix by testing the packaged
    # build, which failed with "Class is immutable" from inside xmod
    # otherwise).
    "packages": ["svse", "pymobiledevice3", "xmod", "runs", "editor", "inquirer3"],
    "includes": ["PySide6.QtCore", "PySide6.QtGui", "PySide6.QtWidgets"],
    "extra_scripts": [str(ROOT / "packaging" / "pmd3_cli.py")],
    "iconfile": None,
    "plist": {
        "CFBundleName": "Stardew Valley Save Editor",
        "CFBundleDisplayName": "Stardew Valley Save Editor",
        "CFBundleIdentifier": "com.raahimsyed.stardew-save-editor",
        "CFBundleShortVersionString": "0.1.0",
        "NSHighResolutionCapable": True,
    },
}

setup(
    name="Stardew Valley Save Editor",
    app=APP,
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)

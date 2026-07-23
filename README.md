# Stardew Valley Save Editor

A macOS GUI app for editing Stardew Valley mobile saves over USB - money,
inventory, NPC relationships, and object placement with a visual map
preview - connecting directly to a paired iPhone/iPad.

## Running from source

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
python run.py
```

The first time you connect a device you'll need to accept the "Trust This
Computer?" prompt on the device, and enable Developer Mode (Settings ->
Privacy & Security -> Developer Mode) if it isn't already on - the app will
tell you if either is needed.

## Running tests

```
python -m pytest tests/
```

Most tests are gated on a real save fixture (`tests/fixtures/sample_save/`)
which is gitignored (never commit real player save data) - pull one with a
device connected:

```
python tools/smoke_test_device.py
```

which also doubles as a no-GUI smoke test of the whole device layer.

## Building the standalone .app

```
python packaging/setup_py2app.py py2app
./packaging/fix_dylibs.sh
```

The second step is **required, not optional** - see the comments at the
top of `packaging/setup_py2app.py` and inside `fix_dylibs.sh` for why
(py2app corrupts a codesigned OpenSSL dylib while rewriting install names,
and separately would otherwise bundle a symbol-incomplete build; the script
fixes both by re-copying the correct Homebrew OpenSSL libs and re-signing
them). Skipping it produces an app that crashes on launch.

The built app lives at `dist/Stardew Valley Save Editor.app` and is fully
standalone - it does not need the venv or Homebrew Python at runtime (it
does still need Homebrew's `openssl@3` present on the *build* machine, to
source correct libraries from).

## Project layout

- `src/svse/device/` - USB device I/O (pairing, dev mode, save pull/push),
  wraps `pymobiledevice3`.
- `src/svse/savemodel/` - save file XML parsing/editing (money, inventory,
  relationships, object placement), byte-identical round-trip safe.
- `src/svse/itemdb/` - compiled item database + sprite art (see
  `data/items_raw/SOURCES.md` for provenance).
- `src/svse/safety/` - local backups + validation gate before every device
  write.
- `src/svse/gui/` - the PySide6 application.
- `tools/build_item_db.py` - one-time offline build of `data/items.json`
  and `data/tilesheets/` from `data/items_raw/`.
- `packaging/` - py2app build script and the post-build dylib fix.

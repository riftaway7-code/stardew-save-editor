"""Tiny wrapper bundled as a second executable (py2app's extra_scripts) so
the packaged .app has a genuine `pymobiledevice3` CLI binary to shell out
to - see svse.device._shell for why the device layer needs the real CLI
(not the raw async API) and svse.paths/this file's use in _shell.py for why
`sys.executable -m pymobiledevice3` doesn't work inside a frozen py2app
app (sys.executable there is the app's own GUI launcher binary, not a
generic Python interpreter - discovered by testing the packaged build).

Top-level try/except is deliberate and load-bearing, not defensive
boilerplate: pymobiledevice3's own AFC-shell cleanup path has a
"RuntimeError: event loop is already running" bug that only surfaces
inside a frozen py2app bundle (not in the dev venv - never root-caused why,
possibly a tty/rich-console detection difference). The real work (e.g. a
`pull`) has already completed successfully by the time this fires - it's
purely a cleanup-path crash. Left uncaught, a bundled .app's helper
executable crashing triggers macOS's own crash-reporter dialog, which
BLOCKS waiting for a human to click it - fatal for a binary that's only
ever invoked headlessly via subprocess, since the parent's subprocess.run()
call then hangs until its timeout. Catching everything here converts that
into a prompt, silent, correct-exit-code process exit instead."""

import sys

from pymobiledevice3.__main__ import main

if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except BaseException as exc:  # noqa: BLE001 - see module docstring
        print(f"pmd3_cli: suppressing post-completion cleanup error: {exc!r}", file=sys.stderr)
        sys.exit(0)

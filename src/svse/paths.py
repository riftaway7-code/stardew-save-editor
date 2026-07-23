"""Resolves the project's data/ directory in both dev (running from source)
and frozen (packaged .app via py2app) contexts.

py2app sets the RESOURCEPATH env var to Contents/Resources and lays
data_files out directly under it (see packaging/setup_py2app.py) - in dev,
data/ sits at the project root, four levels above this file
(src/svse/paths.py -> src/svse -> src -> <project root>/data)."""

from __future__ import annotations

import os
from pathlib import Path


def data_dir() -> Path:
    resource_path = os.environ.get("RESOURCEPATH")
    if resource_path:
        return Path(resource_path) / "data"
    return Path(__file__).parent.parent.parent / "data"
